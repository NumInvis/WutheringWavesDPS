"""
贴吧数据爬取服务
使用aiotieba库实现真实的贴吧数据获取
借鉴AstrBot插件的Set去重和内存缓存统计
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
import aiotieba as tb
HAS_AIOTIEBA = True


from app.models.tieba import TiebaDailyStats, TiebaHotPost
from app.core.logger import add_log
from app.core.database import SessionLocal

MONITORED_TIEBAS = [
    "鸣潮爆料", "鸣潮内鬼", "新鸣潮内鬼", "北落野", "鸣潮",
    "三度笑话", "原神内鬼", "mihoyo", "asoul",
    "崩坏星穹铁道内鬼", "星穹铁道内鬼", "原神内鬼爆料", "绝区零内鬼", "快乐雪花"
]

TIEBA_COLORS = {
    "鸣潮爆料": "#667eea", "鸣潮内鬼": "#764ba2", "新鸣潮内鬼": "#f093fb",
    "北落野": "#22c55e", "鸣潮": "#10b981", "三度笑话": "#f59e0b",
    "原神内鬼": "#ef4444", "mihoyo": "#dc2626", "asoul": "#3b82f6",
    "崩坏星穹铁道内鬼": "#8b5cf6", "星穹铁道内鬼": "#a855f7",
    "原神内鬼爆料": "#ec4899", "绝区零内鬼": "#06b6d4", "快乐雪花": "#14b8a6"
}

CRAWL_INTERVAL = 900

FILTER_KEYWORDS = ["水楼", "集中", "汇总", "专用", "本吧"]

_crawl_task: Optional[asyncio.Task] = None
_running = False

# ========== 内存缓存统计（借鉴AstrBot插件）==========
class TiebaStatsCache:
    """贴吧统计内存缓存 - 减少数据库查询次数"""
    
    def __init__(self):
        # 每日发帖统计: {date: {tieba_name: count}}
        self.daily_posts: Dict[str, Dict[str, int]] = {}
        # 贴吧活跃度: {tieba_name: {"total_posts": int, "first_seen": str, "last_post": str}}
        self.forum_activity: Dict[str, Dict] = {}
        # 已缓存的帖子ID: {tieba_name: Set[post_id]}
        self.cached_post_ids: Dict[str, Set[str]] = {}
        # 最后更新时间
        self.last_update: Dict[str, datetime] = {}
        # 异步锁，保护并发写入
        self._lock = asyncio.Lock()
    
    async def load_from_db(self, db: Session):
        """从数据库加载统计数据到内存"""
        async with self._lock:
            # 加载最近7天的统计数据
            today = get_beijing_date()
            for i in range(7):
                date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                stats = db.query(TiebaDailyStats).filter(TiebaDailyStats.date == date).all()
                self.daily_posts[date] = {}
                for stat in stats:
                    self.daily_posts[date][stat.tieba_name] = stat.post_count
                    # 更新活跃度
                    if stat.tieba_name not in self.forum_activity:
                        self.forum_activity[stat.tieba_name] = {
                            "total_posts": 0,
                            "first_seen": date,
                            "last_post": date
                        }
                    self.forum_activity[stat.tieba_name]["total_posts"] += stat.post_count
                    self.forum_activity[stat.tieba_name]["last_post"] = date
            
            # 加载已存在的帖子ID（最近3天）
            three_days_ago = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
            for tieba in MONITORED_TIEBAS:
                posts = db.query(TiebaHotPost).filter(
                    and_(
                        TiebaHotPost.tieba_name == tieba,
                        TiebaHotPost.hot_date >= three_days_ago
                    )
                ).all()
                self.cached_post_ids[tieba] = {p.post_id for p in posts}
            
            add_log("info", "内存缓存统计加载完成")
    
    async def update_daily_stats(self, tieba_name: str, new_posts_count: int, date: str):
        """更新每日发帖统计"""
        async with self._lock:
            if date not in self.daily_posts:
                self.daily_posts[date] = {}
            if tieba_name not in self.daily_posts[date]:
                self.daily_posts[date][tieba_name] = 0
            self.daily_posts[date][tieba_name] += new_posts_count
            
            # 更新活跃度
            if tieba_name not in self.forum_activity:
                self.forum_activity[tieba_name] = {
                    "total_posts": 0,
                    "first_seen": date,
                    "last_post": date
                }
            self.forum_activity[tieba_name]["total_posts"] += new_posts_count
            self.forum_activity[tieba_name]["last_post"] = date
            self.last_update[tieba_name] = datetime.now()
    
    async def add_post_id(self, tieba_name: str, post_id: str):
        """添加已缓存的帖子ID"""
        async with self._lock:
            if tieba_name not in self.cached_post_ids:
                self.cached_post_ids[tieba_name] = set()
            self.cached_post_ids[tieba_name].add(post_id)
    
    def is_post_exists(self, tieba_name: str, post_id: str) -> bool:
        """检查帖子是否已存在（使用Set，O(1)查询）"""
        return post_id in self.cached_post_ids.get(tieba_name, set())
    
    def get_daily_count(self, tieba_name: str, date: str) -> int:
        """获取某日发帖数"""
        return self.daily_posts.get(date, {}).get(tieba_name, 0)
    
    def get_forum_ranking(self) -> List[Dict]:
        """获取贴吧活跃度排行"""
        forums = []
        for name, data in self.forum_activity.items():
            forums.append({
                "name": name,
                "total_posts": data.get("total_posts", 0),
                "last_post": data.get("last_post", "")
            })
        return sorted(forums, key=lambda x: x["total_posts"], reverse=True)

# 全局统计缓存实例
_stats_cache = TiebaStatsCache()


def get_beijing_time() -> datetime:
    return datetime.utcnow() + timedelta(hours=8)


def get_beijing_date() -> str:
    return get_beijing_time().strftime("%Y-%m-%d")


def is_today_beijing(timestamp: int) -> bool:
    if not timestamp:
        return False
    try:
        post_time = datetime.fromtimestamp(timestamp)
        beijing_post_time = post_time + timedelta(hours=8)
        today_beijing = get_beijing_date()
        result = beijing_post_time.strftime("%Y-%m-%d") == today_beijing
        return result
    except Exception as e:
        add_log("error", f"时间过滤失败: {e}")
        return False


def calc_hot_index(reply_count: int, like_count: int) -> int:
    return 3 * reply_count + like_count


async def crawl_tieba(tieba_name: str, client, db: Session) -> Dict:
    """
    爬取贴吧数据
    使用内存缓存的Set去重（O(1)查询效率），同时更新已存在帖子的回复数和点赞数
    """
    result = {
        "tieba_name": tieba_name,
        "post_count": 0,
        "posts": [],
        "new_post_ids": set(),
        "today_post_ids": set(),
        "updated_posts": [],  # 记录需要更新的帖子
        "error": None
    }
    
    try:
        threads_resp = await client.get_threads(tieba_name, pn=1, rn=200, sort=tb.ThreadSortType.CREATE)
        
        threads = []
        if threads_resp:
            if hasattr(threads_resp, 'objs'):
                threads = threads_resp.objs
            elif isinstance(threads_resp, list):
                threads = threads_resp
            elif hasattr(threads_resp, '__iter__'):
                threads = list(threads_resp)
        
        today = get_beijing_date()
        
        if threads:
            for thread in threads:
                reply_count = getattr(thread, 'reply_num', 0) or 0
                like_count = getattr(thread, 'agree_num', 0) or 0
                title = getattr(thread, 'title', '')[:500] if getattr(thread, 'title', '') else ''
                tid = getattr(thread, 'tid', 0)
                create_time = getattr(thread, 'create_time', 0)
                
                if not is_today_beijing(create_time):
                    continue
                
                if any(kw in title for kw in FILTER_KEYWORDS):
                    continue
                
                post_id_str = str(tid)
                result["today_post_ids"].add(post_id_str)
                
                # 使用内存缓存的Set检查帖子是否已存在（O(1)效率）
                if _stats_cache.is_post_exists(tieba_name, post_id_str):
                    # 已存在的帖子，记录更新信息
                    result["updated_posts"].append({
                        "post_id": post_id_str,
                        "reply_count": reply_count,
                        "like_count": like_count
                    })
                else:
                    # 新帖子
                    result["new_post_ids"].add(post_id_str)
                    result["post_count"] += 1
                    
                    post_time = datetime.fromtimestamp(create_time) if create_time else get_beijing_time()
                    
                    post_data = {
                        "tieba_name": tieba_name,
                        "post_id": post_id_str,
                        "title": title,
                        "reply_count": reply_count,
                        "like_count": like_count,
                        "hot_index": calc_hot_index(reply_count, like_count),
                        "post_url": f"https://tieba.baidu.com/p/{tid}",
                        "post_time": post_time
                    }
                    result["posts"].append(post_data)
        
        add_log("info", f"爬取贴吧 {tieba_name}: 新帖 {result['post_count']} 帖，更新 {len(result['updated_posts'])} 帖，今日共 {len(result['today_post_ids'])} 帖")
        
    except Exception as e:
        result["error"] = str(e)
        add_log("error", f"爬取贴吧 {tieba_name} 失败: {e}")
    
    return result


async def save_crawl_results(results: List[Dict], db: Session):
    """
    保存爬取结果
    使用内存缓存统计，批量更新已存在的帖子
    """
    today = get_beijing_date()
    
    for result in results:
        if result.get("error"):
            continue
            
        tieba_name = result["tieba_name"]
        new_post_count = result["post_count"]
        today_post_count = len(result.get("today_post_ids", set()))
        posts = result["posts"]
        updated_posts = result.get("updated_posts", [])
        
        # 使用内存缓存更新统计（减少数据库查询）
        await _stats_cache.update_daily_stats(tieba_name, new_post_count, today)
        
        # 更新或创建每日统计记录
        existing = db.query(TiebaDailyStats).filter(
            and_(TiebaDailyStats.tieba_name == tieba_name, TiebaDailyStats.date == today)
        ).first()
        
        if existing:
            existing.post_count = today_post_count
        else:
            stat = TiebaDailyStats(tieba_name=tieba_name, date=today, post_count=today_post_count)
            db.add(stat)
        
        # 批量更新已存在的帖子（回复数和点赞数）
        if updated_posts:
            # 使用批量查询提高效率
            post_ids = [p["post_id"] for p in updated_posts]
            existing_posts = db.query(TiebaHotPost).filter(
                and_(
                    TiebaHotPost.tieba_name == tieba_name,
                    TiebaHotPost.post_id.in_(post_ids),
                    TiebaHotPost.hot_date == today
                )
            ).all()
            
            # 创建映射以便快速查找
            post_map = {p.post_id: p for p in existing_posts}
            
            for update_info in updated_posts:
                post_id = update_info["post_id"]
                if post_id in post_map:
                    post_map[post_id].reply_count = update_info["reply_count"]
                    post_map[post_id].like_count = update_info["like_count"]
        
        # 插入新帖子
        for post in posts:
            hot_post = TiebaHotPost(
                tieba_name=post["tieba_name"],
                post_id=post["post_id"],
                title=post["title"],
                reply_count=post["reply_count"],
                like_count=post["like_count"],
                post_url=post["post_url"],
                post_time=post["post_time"],
                hot_date=today,
                hot_type='daily'
            )
            db.add(hot_post)
            
            # 添加到内存缓存
            await _stats_cache.add_post_id(tieba_name, post["post_id"])
    
    db.commit()
    add_log("info", f"保存爬取结果完成，共处理 {len(results)} 个贴吧")


async def init_stats_cache():
    """初始化统计缓存 - 在应用启动时调用"""
    db = SessionLocal()
    try:
        await _stats_cache.load_from_db(db)
        add_log("info", "统计缓存初始化完成")
    except Exception as e:
        add_log("error", f"统计缓存初始化失败: {e}")
    finally:
        db.close()


async def crawl_all_tiebas():
    if not HAS_AIOTIEBA:
        add_log("error", "aiotieba未安装，无法爬取数据")
        return []
    
    add_log("info", "开始爬取所有贴吧数据...")
    
    db = SessionLocal()
    results = []
    
    try:
        # 确保缓存已加载
        if not _stats_cache.cached_post_ids:
            await _stats_cache.load_from_db(db)
        
        async with tb.Client() as client:
            for tieba_name in MONITORED_TIEBAS:
                result = await crawl_tieba(tieba_name, client, db)
                results.append(result)
                await asyncio.sleep(0.3)
        
        await save_crawl_results(results, db)
        
        total_posts = sum(r["post_count"] for r in results)
        total_updated = sum(len(r.get("updated_posts", [])) for r in results)
        add_log("info", f"爬取完成: 新帖{total_posts}帖，更新{total_updated}帖")
        
    except Exception as e:
        add_log("error", f"爬取任务失败: {e}")
    finally:
        db.close()
    
    return results


async def crawl_scheduler():
    global _running
    _running = True
    
    add_log("info", "贴吧爬取调度器已启动，开始初始化爬取最近一周数据...")
    
    db = SessionLocal()
    try:
        beijing_now = get_beijing_time()
        dates_needed = [(beijing_now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
        
        existing_dates = set()
        for date in dates_needed:
            count = db.query(TiebaDailyStats).filter(TiebaDailyStats.date == date).count()
            if count > 0:
                existing_dates.add(date)
        
        missing_dates = [d for d in dates_needed if d not in existing_dates]
        
        if missing_dates:
            add_log("info", f"需要补充爬取 {len(missing_dates)} 天的数据: {missing_dates}")
            await crawl_all_tiebas()
        else:
            add_log("info", "数据库已有最近一周数据，跳过初始化爬取")
    except Exception as e:
        add_log("error", f"检查历史数据失败: {e}")
    finally:
        db.close()
    
    add_log("info", f"开始每{CRAWL_INTERVAL // 60}分钟定时爬取")
    
    while _running:
        try:
            await asyncio.sleep(CRAWL_INTERVAL)
            if _running:
                await crawl_all_tiebas()
        except asyncio.CancelledError:
            break
        except Exception as e:
            add_log("error", f"爬取调度器错误: {e}")
            await asyncio.sleep(60)


def start_crawl_scheduler():
    global _crawl_task, _running
    
    if _crawl_task is not None and not _crawl_task.done():
        return
    
    _running = True
    _crawl_task = asyncio.create_task(crawl_scheduler())
    add_log("info", "贴吧爬取后台任务已创建")


def stop_crawl_scheduler():
    global _crawl_task, _running
    
    _running = False
    
    if _crawl_task is not None and not _crawl_task.done():
        _crawl_task.cancel()
        _crawl_task = None
        add_log("info", "贴吧爬取后台任务已停止")


async def manual_crawl():
    return await crawl_all_tiebas()


def get_scheduler_status() -> Dict:
    return {
        "running": _running,
        "has_aiotieba": HAS_AIOTIEBA,
        "monitored_count": len(MONITORED_TIEBAS),
        "interval_seconds": CRAWL_INTERVAL,
        "next_crawl": "运行中" if _running else "已停止"
    }
