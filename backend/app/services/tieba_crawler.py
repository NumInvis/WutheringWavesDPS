"""
贴吧数据爬取服务
使用aiotieba库实现真实的贴吧数据获取
借鉴AstrBot插件的Set去重和内存缓存统计
数据存储改为JSON文件（模仿AstrBot）
"""

import asyncio
import json
import os
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set

import aiotieba as tb


# 配置常量
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

# 爬取间隔1分钟，每次获取30条
CRAWL_INTERVAL = 60
THREADS_PER_CRAWL = 30

FILTER_KEYWORDS = ["水楼", "集中", "汇总", "专用", "本吧"]

# 数据目录
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "tieba")
os.makedirs(DATA_DIR, exist_ok=True)

# 全局状态
_crawl_task: Optional[asyncio.Task] = None
_running = False


# 简单的日志函数
def add_log(level: str, message: str):
    """添加日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level.upper()}] {message}")


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


# ========== JSON 文件操作工具 ==========
def load_json_file(filename: str) -> Dict:
    """加载JSON文件"""
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError, OSError) as e:
            add_log("error", f"加载文件 {filename} 失败: {e}")
    return {}


def save_json_file(filename: str, data: Dict):
    """保存JSON文件"""
    filepath = os.path.join(DATA_DIR, filename)
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except (IOError, OSError, TypeError) as e:
        add_log("error", f"保存文件 {filename} 失败: {e}")


# ========== 内存缓存统计（借鉴AstrBot插件）==========
class TiebaStatsCache:
    """贴吧统计内存缓存 - 模仿AstrBot实现"""
    
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
        # 文件写入锁
        self._file_lock = asyncio.Lock()
    
    def load_from_files(self):
        """从JSON文件加载统计数据到内存 - 模仿AstrBot"""
        # 加载统计数据
        stats = load_json_file("stats.json")
        self.daily_posts = stats.get("daily_posts", {})
        self.forum_activity = stats.get("forum_activity", {})
        
        # 加载所有已存在的帖子ID（每个贴吧一个文件）
        total_posts = 0
        for tieba in MONITORED_TIEBAS:
            posts_data = load_json_file(f"{tieba}.json")
            if isinstance(posts_data, list):
                self.cached_post_ids[tieba] = {str(p.get("tid", p.get("post_id", ""))) for p in posts_data}
                total_posts += len(self.cached_post_ids[tieba])
            else:
                self.cached_post_ids[tieba] = set()
        
        add_log("info", f"内存缓存统计加载完成，已加载 {total_posts} 条帖子记录")
    
    async def force_reload(self):
        """强制重新加载缓存 - 每次爬取前调用"""
        async with self._lock:
            self.cached_post_ids.clear()
            
            for tieba in MONITORED_TIEBAS:
                posts_data = load_json_file(f"{tieba}.json")
                if isinstance(posts_data, list):
                    self.cached_post_ids[tieba] = {str(p.get("tid", p.get("post_id", ""))) for p in posts_data}
                else:
                    self.cached_post_ids[tieba] = set()
            
            # 重新加载统计
            stats = load_json_file("stats.json")
            self.daily_posts = stats.get("daily_posts", {})
            self.forum_activity = stats.get("forum_activity", {})
            
            add_log("info", "缓存已强制重新加载")
    
    async def update_daily_stats(self, tieba_name: str, new_posts_count: int, date: str):
        """更新每日发帖统计 - 累加新帖子数（参考AstrBot逻辑）"""
        async with self._lock:
            if date not in self.daily_posts:
                self.daily_posts[date] = {}
            if tieba_name not in self.daily_posts[date]:
                self.daily_posts[date][tieba_name] = 0
            # 累加新帖子数，而不是覆盖
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
            
            # 异步保存到文件
            await self._save_stats_async()
    
    async def _save_stats_async(self):
        """异步保存统计数据到JSON文件（带锁）- 模仿AstrBot"""
        async with self._file_lock:
            stats_data = {
                "daily_posts": self.daily_posts,
                "forum_activity": self.forum_activity
            }
            save_json_file("stats.json", stats_data)
    
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
    
    def get_daily_stats(self, days: int = 7) -> Dict[str, Dict]:
        """获取最近N天的统计 - 模仿AstrBot"""
        result = {}
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            result[date] = self.daily_posts.get(date, {})
        return result


# 全局统计缓存实例
_stats_cache = TiebaStatsCache()


# ========== 帖子数据文件操作 ==========
async def load_posts_from_file(tieba_name: str) -> List[Dict]:
    """从JSON文件加载帖子数据 - 模仿AstrBot"""
    posts_data = load_json_file(f"{tieba_name}.json")
    if isinstance(posts_data, list):
        return posts_data
    return []


async def save_posts_to_file(tieba_name: str, posts: List[Dict]):
    """保存帖子数据到JSON文件（带锁）- 模仿AstrBot"""
    async with _stats_cache._file_lock:
        # 加载现有数据
        existing_posts = load_json_file(f"{tieba_name}.json")
        if not isinstance(existing_posts, list):
            existing_posts = []
        
        # 合并新数据
        existing_tids = {str(p.get("tid", p.get("post_id", ""))) for p in existing_posts}
        for post in posts:
            tid = str(post.get("tid", post.get("post_id", "")))
            if tid not in existing_tids:
                existing_posts.append(post)
        
        # 保存
        save_json_file(f"{tieba_name}.json", existing_posts)


# ========== 爬取逻辑 ==========
async def crawl_tieba_with_retry(tieba_name: str, client, retry: int = 3, timeout: int = 30) -> Dict:
    """
    爬取贴吧数据 - 带重试机制（参考AstrBot实现）
    使用内存缓存的Set去重（O(1)查询效率）
    """
    result = {
        "tieba_name": tieba_name,
        "post_count": 0,
        "posts": [],
        "new_post_ids": set(),
        "today_post_ids": set(),
        "updated_posts": [],
        "error": None
    }
    
    attempt = 0
    threads = []
    
    while attempt < retry:
        try:
            # 每次只获取30条
            threads_resp = await asyncio.wait_for(
                client.get_threads(tieba_name, pn=1, rn=THREADS_PER_CRAWL, sort=tb.ThreadSortType.CREATE),
                timeout=timeout
            )
            
            if threads_resp:
                if hasattr(threads_resp, 'objs'):
                    threads = threads_resp.objs
                elif isinstance(threads_resp, list):
                    threads = threads_resp
                elif hasattr(threads_resp, '__iter__'):
                    threads = list(threads_resp)
            
            # 如果获取到0条且不是最后一次尝试，则重试
            if len(threads) == 0 and attempt < retry - 1:
                attempt += 1
                delay = random.uniform(1, 5)
                add_log("warning", f"获取贴吧[{tieba_name}]帖子为0条，{delay:.2f}秒后进行第{attempt}次重试...")
                await asyncio.sleep(delay)
                continue
            
            # 成功获取数据，跳出重试循环
            break
            
        except asyncio.TimeoutError:
            attempt += 1
            add_log("error", f"获取贴吧[{tieba_name}]帖子超时(尝试{attempt}/{retry})")
            if attempt < retry:
                await asyncio.sleep(random.uniform(2, 5))
        except Exception as e:
            attempt += 1
            add_log("error", f"获取贴吧[{tieba_name}]帖子失败(尝试{attempt}/{retry}): {e}")
            if attempt < retry:
                await asyncio.sleep(random.uniform(1, 3))
    
    # 处理获取到的帖子
    if threads:
        for thread in threads:
            try:
                reply_count = getattr(thread, 'reply_num', 0) or 0
                like_count = getattr(thread, 'agree_num', 0) or 0
                title = getattr(thread, 'title', '')[:500] if getattr(thread, 'title', '') else ''
                tid = getattr(thread, 'tid', 0)
                create_time = getattr(thread, 'create_time', 0)
                
                post_id_str = str(tid)
                is_today = is_today_beijing(create_time)
                
                # 检查帖子是否已存在（用于更新热度数据）
                is_existing = _stats_cache.is_post_exists(tieba_name, post_id_str)
                
                # 如果是已存在的帖子，更新热度数据（评论数、点赞数）
                if is_existing:
                    result["updated_posts"].append({
                        "post_id": post_id_str,
                        "reply_count": reply_count,
                        "like_count": like_count
                    })
                
                # 只处理今天的帖子用于发帖量统计
                if not is_today:
                    continue
                
                if any(kw in title for kw in FILTER_KEYWORDS):
                    continue
                
                result["today_post_ids"].add(post_id_str)
                
                # 如果帖子已存在，不需要再添加到新帖子列表
                if is_existing:
                    continue
                
                # 新帖子
                result["new_post_ids"].add(post_id_str)
                result["post_count"] += 1
                
                post_time = datetime.fromtimestamp(create_time) if create_time else get_beijing_time()
                
                post_data = {
                    "tid": tid,
                    "post_id": post_id_str,
                    "title": title,
                    "text": getattr(thread, 'text', '')[:500],
                    "reply_num": reply_count,
                    "agree": like_count,
                    "like_count": like_count,
                    "hot_index": calc_hot_index(reply_count, like_count),
                    "url": f"https://tieba.baidu.com/p/{tid}",
                    "post_url": f"https://tieba.baidu.com/p/{tid}",
                    "post_time": post_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "create_time": post_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "tieba_name": tieba_name,
                    "author_id": getattr(thread, 'user', None) and getattr(thread.user, 'user_name', '未知') or '未知'
                }
                result["posts"].append(post_data)
            except (AttributeError, TypeError) as conv_e:
                add_log("warning", f"转换帖子数据失败: {conv_e}")
                continue
    
    add_log("info", f"爬取贴吧 {tieba_name}: 新帖 {result['post_count']} 帖，更新 {len(result['updated_posts'])} 帖，今日共 {len(result['today_post_ids'])} 帖")
    
    return result


# 保持向后兼容
async def crawl_tieba(tieba_name: str, client) -> Dict:
    """兼容旧接口，调用带重试的版本"""
    return await crawl_tieba_with_retry(tieba_name, client)


async def save_crawl_results(results: List[Dict]):
    """
    保存爬取结果到JSON文件和数据库
    模仿AstrBot的文件存储方式 + 数据库同步
    """
    today = get_beijing_date()
    
    # 同步到数据库
    try:
        from app.core.database import get_db
        from app.models.tieba import TiebaDailyStats, TiebaHotPost
        from sqlalchemy.orm import Session
        import uuid
        
        db = next(get_db())
        
        for result in results:
            if result.get("error"):
                continue
                
            tieba_name = result["tieba_name"]
            new_post_count = result["post_count"]
            posts = result["posts"]
            updated_posts = result.get("updated_posts", [])
            today_post_ids = result.get("today_post_ids", set())
            
            # 更新内存统计（累加新帖子数）
            await _stats_cache.update_daily_stats(tieba_name, new_post_count, today)
            
            # ===== 同步到数据库：每日统计 =====
            try:
                existing_stat = db.query(TiebaDailyStats).filter(
                    TiebaDailyStats.tieba_name == tieba_name,
                    TiebaDailyStats.date == today
                ).first()
                
                if existing_stat:
                    # 累加新帖子数（而不是覆盖）
                    existing_stat.post_count += new_post_count
                else:
                    # 创建新记录
                    new_stat = TiebaDailyStats(
                        id=str(uuid.uuid4()),
                        tieba_name=tieba_name,
                        date=today,
                        post_count=new_post_count
                    )
                    db.add(new_stat)
                
                db.commit()
            except Exception as e:
                db.rollback()
                add_log("error", f"同步每日统计到数据库失败 [{tieba_name}]: {e}")
            
            # ===== 同步到数据库：热帖记录 =====
            try:
                for post in posts:
                    # 检查是否已存在
                    existing_hot = db.query(TiebaHotPost).filter(
                        TiebaHotPost.post_id == str(post["post_id"]),
                        TiebaHotPost.hot_date == today
                    ).first()
                    
                    if not existing_hot:
                        hot_post = TiebaHotPost(
                            id=str(uuid.uuid4()),
                            tieba_name=tieba_name,
                            post_id=str(post["post_id"]),
                            title=post["title"][:500],
                            reply_count=post.get("reply_num", 0),
                            like_count=post.get("like_count", 0),
                            post_url=post.get("post_url", ""),
                            post_time=datetime.strptime(post["post_time"], "%Y-%m-%d %H:%M:%S") if post.get("post_time") else get_beijing_time(),
                            hot_date=today,
                            hot_type='daily'
                        )
                        db.add(hot_post)
                
                db.commit()
            except Exception as e:
                db.rollback()
                add_log("error", f"同步热帖到数据库失败 [{tieba_name}]: {e}")
            
            # 更新已存在帖子的回复数和点赞数
            if updated_posts:
                existing_posts = await load_posts_from_file(tieba_name)
                post_map = {str(p.get("post_id", p.get("tid", ""))): p for p in existing_posts}
                
                for update_info in updated_posts:
                    post_id = update_info["post_id"]
                    if post_id in post_map:
                        post_map[post_id]["reply_num"] = update_info["reply_count"]
                        post_map[post_id]["reply_count"] = update_info["reply_count"]
                        post_map[post_id]["agree"] = update_info["like_count"]
                        post_map[post_id]["like_count"] = update_info["like_count"]
                
                # 保存更新后的数据
                async with _stats_cache._file_lock:
                    save_json_file(f"{tieba_name}.json", existing_posts)
            
            # 保存新帖子
            if posts:
                await save_posts_to_file(tieba_name, posts)
                
                # 添加到内存缓存
                for post in posts:
                    await _stats_cache.add_post_id(tieba_name, post["post_id"])
        
        add_log("info", f"保存爬取结果完成，共处理 {len(results)} 个贴吧")
        
    except Exception as e:
        add_log("error", f"数据库同步失败: {e}")


async def init_stats_cache():
    """初始化统计缓存 - 在应用启动时调用"""
    _stats_cache.load_from_files()
    
    # 同步JSON历史数据到数据库（用于前端API读取）
    await sync_json_to_database()
    
    add_log("info", "统计缓存初始化完成")


async def sync_json_to_database():
    """将JSON文件中的历史统计数据同步到数据库"""
    try:
        from app.core.database import get_db
        from app.models.tieba import TiebaDailyStats
        import uuid
        
        db = next(get_db())
        stats = load_json_file("stats.json")
        daily_posts = stats.get("daily_posts", {})
        
        sync_count = 0
        for date, tieba_data in daily_posts.items():
            for tieba_name, post_count in tieba_data.items():
                # 检查数据库是否已存在
                existing = db.query(TiebaDailyStats).filter(
                    TiebaDailyStats.tieba_name == tieba_name,
                    TiebaDailyStats.date == date
                ).first()
                
                if not existing:
                    # 创建新记录
                    new_stat = TiebaDailyStats(
                        id=str(uuid.uuid4()),
                        tieba_name=tieba_name,
                        date=date,
                        post_count=post_count
                    )
                    db.add(new_stat)
                    sync_count += 1
                else:
                    # 更新现有记录（以JSON为准，因为可能修复过数据）
                    existing.post_count = post_count
        
        db.commit()
        if sync_count > 0:
            add_log("info", f"历史数据同步完成：新增 {sync_count} 条记录到数据库")
        
    except Exception as e:
        add_log("error", f"同步历史数据到数据库失败: {e}")


async def crawl_all_tiebas():
    """爬取所有贴吧 - 强制缓存加载"""
    add_log("info", "开始爬取所有贴吧数据...")
    
    results = []
    
    try:
        # 每次爬取前强制重新加载缓存
        await _stats_cache.force_reload()
        
        async with tb.Client() as client:
            for tieba_name in MONITORED_TIEBAS:
                result = await crawl_tieba_with_retry(tieba_name, client)
                results.append(result)
                await asyncio.sleep(0.3)
        
        await save_crawl_results(results)
        
        total_posts = sum(r["post_count"] for r in results)
        total_updated = sum(len(r.get("updated_posts", [])) for r in results)
        add_log("info", f"爬取完成: 新帖{total_posts}帖，更新{total_updated}帖")
        
    except Exception as e:
        add_log("error", f"爬取任务失败: {e}")
    
    return results


async def crawl_scheduler():
    global _running
    _running = True
    
    add_log("info", "贴吧爬取调度器已启动，开始初始化...")
    
    # 初始化缓存
    await init_stats_cache()
    
    # 检查是否需要补充历史数据
    stats = load_json_file("stats.json")
    daily_posts = stats.get("daily_posts", {})
    
    beijing_now = get_beijing_time()
    dates_needed = [(beijing_now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    
    missing_dates = [d for d in dates_needed if d not in daily_posts or not daily_posts[d]]
    
    if missing_dates:
        add_log("info", f"需要补充爬取 {len(missing_dates)} 天的数据: {missing_dates}")
        await crawl_all_tiebas()
    else:
        add_log("info", "已有最近一周数据，跳过初始化爬取")
    
    # 启动时执行一次归档
    try:
        from app.services.tieba_archiver import run_archive_task
        await run_archive_task()
    except Exception as e:
        add_log("error", f"初始归档失败: {e}")
    
    add_log("info", f"开始每{CRAWL_INTERVAL // 60}分钟定时爬取")
    
    # 归档计数器（每24次爬取执行一次归档，约每天一次）
    archive_counter = 0
    
    while _running:
        try:
            await asyncio.sleep(CRAWL_INTERVAL)
            if _running:
                await crawl_all_tiebas()
                
                # 定期归档（每24次爬取 ≈ 每天）
                archive_counter += 1
                if archive_counter >= 24:
                    archive_counter = 0
                    try:
                        from app.services.tieba_archiver import run_archive_task
                        await run_archive_task()
                    except Exception as e:
                        add_log("error", f"定期归档失败: {e}")
                        
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
        "monitored_count": len(MONITORED_TIEBAS),
        "interval_seconds": CRAWL_INTERVAL,
        "data_dir": DATA_DIR,
        "next_crawl": "运行中" if _running else "已停止"
    }


# ========== 数据查询接口（供API使用）==========
def get_daily_stats(days: int = 7) -> Dict[str, Dict]:
    """获取最近N天的统计"""
    return _stats_cache.get_daily_stats(days)


def get_forum_ranking() -> List[Dict]:
    """获取贴吧活跃度排行"""
    return _stats_cache.get_forum_ranking()


def get_hot_threads_list(limit: int = 10) -> List[Dict]:
    """获取热门帖子列表"""
    hot_threads = []
    
    for tieba in MONITORED_TIEBAS:
        posts = load_json_file(f"{tieba}.json")
        if isinstance(posts, list):
            for post in posts:
                reply_num = post.get("reply_num", 0)
                agree_num = post.get("agree", 0)
                # 热度阈值：回复>100 或 点赞>1000
                if reply_num >= 100 or agree_num >= 1000:
                    hot_threads.append({
                        "tid": post.get("tid", post.get("post_id", "")),
                        "post_id": post.get("post_id", post.get("tid", "")),
                        "title": post.get("title", ""),
                        "tieba_name": tieba,
                        "reply_num": reply_num,
                        "agree": agree_num,
                        "like_count": agree_num,
                        "url": post.get("url", ""),
                        "post_url": post.get("post_url", ""),
                        "author_id": post.get("author_id", "未知")
                    })
    
    # 按热度排序
    hot_threads.sort(key=lambda x: x["reply_num"] + x["agree"], reverse=True)
    return hot_threads[:limit]


def get_recent_posts(tieba_name: str, limit: int = 5) -> List[Dict]:
    """获取指定贴吧的最近帖子"""
    posts = load_json_file(f"{tieba_name}.json")
    if isinstance(posts, list):
        return posts[-limit:][::-1]  # 最近的在前面
    return []


def search_posts(keyword: str, limit: int = 10) -> List[Dict]:
    """搜索帖子"""
    results = []
    
    for tieba in MONITORED_TIEBAS:
        posts = load_json_file(f"{tieba}.json")
        if isinstance(posts, list):
            for post in posts:
                title = post.get("title", "")
                text = post.get("text", "")
                if keyword.lower() in title.lower() or keyword.lower() in text.lower():
                    results.append({
                        **post,
                        "tieba_name": tieba
                    })
                    if len(results) >= limit:
                        return results
    
    return results
