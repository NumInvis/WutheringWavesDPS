"""
贴吧观察者 API - 使用aiotieba库实现真实数据爬取
热帖指数 = 3*回复量 + 点赞量
"""
import json
import io
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc

from app.core.database import get_db
from app.models.tieba import TiebaDailyStats, TiebaHotPost, DownloadRecord
from app.models.user import User
from app.api.auth import get_current_active_user, get_current_user_optional
from app.core.logger import add_log

router = APIRouter(prefix="/api/tieba", tags=["贴吧观察者"])

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


def get_beijing_time():
    return datetime.utcnow() + timedelta(hours=8)


def get_beijing_date():
    return get_beijing_time().strftime("%Y-%m-%d")


def calc_hot_index(reply_count: int, like_count: int) -> int:
    return 3 * reply_count + like_count


@router.get("/forums")
def get_monitored_forums():
    return {"forums": MONITORED_TIEBAS, "colors": TIEBA_COLORS}


@router.get("/stats/weekly")
def get_weekly_stats(db: Session = Depends(get_db)):
    beijing_now = get_beijing_time()
    dates = [(beijing_now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    
    stats = db.query(TiebaDailyStats).filter(
        TiebaDailyStats.date.in_(dates)
    ).all()
    
    result = {}
    for tieba in MONITORED_TIEBAS:
        tieba_stats = [s for s in stats if s.tieba_name == tieba]
        result[tieba] = {
            "daily": {s.date: s.post_count for s in tieba_stats},
            "total_posts": sum(s.post_count for s in tieba_stats)
        }
    
    return {"dates": dates, "stats": result}


@router.get("/stats/stacked")
def get_stacked_stats(days: int = Query(7, ge=1, le=30), db: Session = Depends(get_db)):
    beijing_now = get_beijing_time()
    dates = [(beijing_now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
    dates.reverse()
    
    stats = db.query(TiebaDailyStats).filter(
        TiebaDailyStats.date.in_(dates)
    ).all()
    
    result = []
    for date in dates:
        day_data = {"date": date, "label": date[5:]}
        for tieba in MONITORED_TIEBAS:
            stat = next((s for s in stats if s.date == date and s.tieba_name == tieba), None)
            day_data[tieba] = stat.post_count if stat else 0
        result.append(day_data)
    
    return {"data": result, "dates": dates, "forums": MONITORED_TIEBAS, "colors": TIEBA_COLORS}


@router.get("/leaderboard")
def get_leaderboard(days: int = Query(7, ge=1, le=30), db: Session = Depends(get_db)):
    beijing_now = get_beijing_time()
    start_date = (beijing_now - timedelta(days=days)).strftime("%Y-%m-%d")
    
    stats = db.query(
        TiebaDailyStats.tieba_name,
        func.sum(TiebaDailyStats.post_count).label('total_posts')
    ).filter(
        TiebaDailyStats.date >= start_date
    ).group_by(
        TiebaDailyStats.tieba_name
    ).order_by(desc('total_posts')).all()
    
    result = []
    for i, stat in enumerate(stats, 1):
        result.append({
            "rank": i,
            "tieba_name": stat.tieba_name,
            "total_posts": stat.total_posts,
            "color": TIEBA_COLORS.get(stat.tieba_name, "#667eea")
        })
    
    return {"leaderboard": result, "days": days}


@router.get("/hot/weekly")
def get_weekly_hot_posts(limit: int = Query(10, ge=1, le=20), db: Session = Depends(get_db)):
    beijing_now = get_beijing_time()
    week_start = beijing_now - timedelta(days=7)
    
    hot_posts = db.query(TiebaHotPost).filter(
        TiebaHotPost.post_time >= week_start
    ).order_by(
        desc(3 * TiebaHotPost.reply_count + TiebaHotPost.like_count)
    ).limit(limit).all()
    
    result = []
    for post in hot_posts:
        result.append({
            "tieba_name": post.tieba_name,
            "post_id": post.post_id,
            "title": post.title,
            "reply_count": post.reply_count,
            "like_count": post.like_count,
            "hot_index": calc_hot_index(post.reply_count, post.like_count),
            "post_url": post.post_url,
            "post_time": post.post_time.strftime("%Y-%m-%d %H:%M:%S") if post.post_time else None,
            "color": TIEBA_COLORS.get(post.tieba_name, "#667eea")
        })
    
    return {"posts": result, "total": len(result)}


@router.get("/hot/daily")
def get_daily_hot_posts(date: Optional[str] = None, limit: int = Query(3, ge=1, le=10), db: Session = Depends(get_db)):
    if not date:
        date = get_beijing_date()
    
    day_start = datetime.strptime(date, "%Y-%m-%d")
    day_end = day_start + timedelta(days=1)
    
    hot_posts = db.query(TiebaHotPost).filter(
        TiebaHotPost.post_time >= day_start,
        TiebaHotPost.post_time < day_end
    ).order_by(
        desc(3 * TiebaHotPost.reply_count + TiebaHotPost.like_count)
    ).limit(limit).all()
    
    result = []
    for post in hot_posts:
        result.append({
            "tieba_name": post.tieba_name,
            "post_id": post.post_id,
            "title": post.title,
            "reply_count": post.reply_count,
            "like_count": post.like_count,
            "hot_index": calc_hot_index(post.reply_count, post.like_count),
            "post_url": post.post_url,
            "post_time": post.post_time.strftime("%Y-%m-%d %H:%M:%S") if post.post_time else None,
            "color": TIEBA_COLORS.get(post.tieba_name, "#667eea")
        })
    
    return {"date": date, "posts": result, "total": len(result)}


@router.get("/download")
def download_data(request: Request, date: Optional[str] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if not date:
        date = get_beijing_date()
    
    client_ip = request.client.host if request.client else "unknown"
    hour_start = get_beijing_time().replace(minute=0, second=0, microsecond=0)
    hour_str = hour_start.strftime("%Y-%m-%d-%H")
    
    existing_record = db.query(DownloadRecord).filter(
        and_(
            DownloadRecord.user_id == client_ip,
            DownloadRecord.download_type == 'tieba_data_ip',
            DownloadRecord.download_date == hour_str
        )
    ).count()
    
    if existing_record >= 2:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="每小时最多下载两次，请稍后再试"
        )
    
    beijing_now = get_beijing_time()
    start_date = (beijing_now - timedelta(days=7)).strftime("%Y-%m-%d")
    today = get_beijing_date()
    
    daily_stats = db.query(TiebaDailyStats).filter(
        TiebaDailyStats.date >= start_date
    ).all()
    
    hot_posts = db.query(TiebaHotPost).filter(
        TiebaHotPost.hot_date >= start_date
    ).all()
    
    export_data = {
        "export_time": get_beijing_time().strftime("%Y-%m-%d %H:%M:%S"),
        "export_timezone": "UTC+8 (北京时间)",
        "date_range": {"start": start_date, "end": today},
        "monitored_forums": MONITORED_TIEBAS,
        "daily_stats": [
            {"tieba_name": s.tieba_name, "date": s.date, "post_count": s.post_count}
            for s in daily_stats
        ],
        "hot_posts": [
            {
                "tieba_name": p.tieba_name, "title": p.title, 
                "reply_count": p.reply_count, "like_count": p.like_count,
                "hot_index": calc_hot_index(p.reply_count, p.like_count),
                "post_url": p.post_url, "hot_date": p.hot_date
            }
            for p in hot_posts
        ]
    }
    
    json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
    
    if len(json_str.encode('utf-8')) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="数据文件超过10MB限制"
        )
    
    download_record = DownloadRecord(
        user_id=client_ip,
        download_type='tieba_data_ip',
        download_date=hour_str
    )
    db.add(download_record)
    db.commit()
    
    add_log("info", f"用户下载贴吧数据: {current_user.username} (IP: {client_ip})", user=current_user.username)
    
    buffer = io.BytesIO(json_str.encode('utf-8'))
    
    return StreamingResponse(
        buffer,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=tieba_data_{date}.json"}
    )


@router.post("/crawl")
async def trigger_crawl(current_user: User = Depends(get_current_active_user)):
    """手动触发爬取所有贴吧数据 - 立即执行"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以执行此操作"
        )
    
    try:
        from app.services.tieba_crawler import crawl_all_tiebas
        results = await crawl_all_tiebas()
        total_posts = sum(r.get("post_count", 0) for r in results)
        return {
            "message": "爬取完成",
            "total_posts": total_posts,
            "results_count": len(results)
        }
    except Exception as e:
        add_log("error", f"爬取任务执行失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"爬取任务执行失败: {e}")


@router.get("/crawl-status")
def get_crawl_status_api():
    """获取爬取任务状态"""
    try:
        from app.services.tieba_crawler import get_scheduler_status
        return get_scheduler_status()
    except Exception as e:
        return {"error": str(e), "running": False}


@router.get("/scheduler/start")
def start_scheduler():
    """启动定时爬取调度器"""
    try:
        from app.services.tieba_crawler import start_crawl_scheduler
        start_crawl_scheduler()
        return {"message": "爬取调度器已启动"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"启动失败: {e}")


@router.get("/scheduler/stop")
def stop_scheduler():
    """停止定时爬取调度器"""
    try:
        from app.services.tieba_crawler import stop_crawl_scheduler
        stop_crawl_scheduler()
        return {"message": "爬取调度器已停止"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"停止失败: {e}")
