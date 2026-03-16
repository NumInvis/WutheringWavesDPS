"""
贴吧数据爬取服务
使用aiotieba库实现真实的贴吧数据获取

运行逻辑：
1. 启动时创建后台定时任务，每15分钟执行一次爬取
2. 爬取流程：遍历所有监控的贴吧 -> 获取帖子列表 -> 统计发帖量 -> 存储到数据库
3. 热帖指数 = 3*回复量 + 点赞量
4. 使用aiotieba库的异步接口，高效并发获取数据
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
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


def get_beijing_time() -> datetime:
    return datetime.utcnow() + timedelta(hours=8)


def get_beijing_date() -> str:
    return get_beijing_time().strftime("%Y-%m-%d")


def calc_hot_index(reply_count: int, like_count: int) -> int:
    return 3 * reply_count + like_count


async def crawl_tieba(tieba_name: str, client, db: Session) -> Dict:
    result = {
        "tieba_name": tieba_name,
        "post_count": 0,
        "posts": [],
        "error": None
    }
    
    try:
        threads_resp = await client.get_threads(tieba_name, pn=1, rn=50, sort=tb.ThreadSortType.CREATE)
        
        threads = []
        if threads_resp:
            if hasattr(threads_resp, 'objs'):
                threads = threads_resp.objs
            elif isinstance(threads_resp, list):
                threads = threads_resp
            elif hasattr(threads_resp, '__iter__'):
                threads = list(threads_resp)
        
        if threads:
            for thread in threads:
                reply_count = getattr(thread, 'reply_num', 0) or 0
                like_count = getattr(thread, 'agree_num', 0) or 0
                title = getattr(thread, 'title', '')[:500] if getattr(thread, 'title', '') else ''
                tid = getattr(thread, 'tid', 0)
                create_time = getattr(thread, 'create_time', 0)
                
                if any(kw in title for kw in FILTER_KEYWORDS):
                    continue
                
                result["post_count"] += 1
                
                post_data = {
                    "tieba_name": tieba_name,
                    "post_id": str(tid),
                    "title": title,
                    "reply_count": reply_count,
                    "like_count": like_count,
                    "hot_index": calc_hot_index(reply_count, like_count),
                    "post_url": f"https://tieba.baidu.com/p/{tid}",
                    "post_time": datetime.fromtimestamp(create_time) if create_time else get_beijing_time()
                }
                result["posts"].append(post_data)
        
        add_log("info", f"爬取贴吧 {tieba_name}: {result['post_count']}帖")
        
    except Exception as e:
        result["error"] = str(e)
        add_log("error", f"爬取贴吧 {tieba_name} 失败: {e}")
    
    return result


async def save_crawl_results(results: List[Dict], db: Session):
    today = get_beijing_date()
    
    for result in results:
        if result.get("error"):
            continue
            
        tieba_name = result["tieba_name"]
        post_count = result["post_count"]
        posts = result["posts"]
        
        existing = db.query(TiebaDailyStats).filter(
            and_(TiebaDailyStats.tieba_name == tieba_name, TiebaDailyStats.date == today)
        ).first()
        
        if existing:
            existing.post_count = post_count
        else:
            stat = TiebaDailyStats(tieba_name=tieba_name, date=today, post_count=post_count)
            db.add(stat)
        
        for post in posts:
            existing_post = db.query(TiebaHotPost).filter(
                TiebaHotPost.post_id == post["post_id"]
            ).first()
            
            if existing_post:
                existing_post.reply_count = post["reply_count"]
                existing_post.like_count = post["like_count"]
            else:
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
    
    db.commit()


async def crawl_all_tiebas():
    if not HAS_AIOTIEBA:
        add_log("error", "aiotieba未安装，无法爬取数据")
        return []
    
    add_log("info", "开始爬取所有贴吧数据...")
    
    db = SessionLocal()
    results = []
    
    try:
        async with tb.Client() as client:
            for tieba_name in MONITORED_TIEBAS:
                result = await crawl_tieba(tieba_name, client, db)
                results.append(result)
                await asyncio.sleep(0.3)
        
        await save_crawl_results(results, db)
        
        total_posts = sum(r["post_count"] for r in results)
        add_log("info", f"爬取完成: {total_posts}帖")
        
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
