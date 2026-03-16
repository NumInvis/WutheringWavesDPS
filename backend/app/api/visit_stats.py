"""
访问统计相关API路由
"""
import hashlib
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, distinct
from typing import List, Dict, Literal
from datetime import datetime, timedelta

from app.core.database import get_db, SessionLocal
from app.models.visit_stat import VisitStat, DailyVisitStat, VisitorRecord
from app.schemas.visit_stat import VisitStatResponse
from app.api.auth import get_current_active_user

router = APIRouter(prefix="/api/visit-stats", tags=["访问统计"])


def record_visit(request: Request):
    """记录访问统计（内部函数）- PV和UV统计"""
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        date_str = now.strftime("%Y-%m-%d")
        hour = now.hour
        path = str(request.url.path)[:500]
        
        visitor_id = request.headers.get("X-Visitor-Id", "")
        if not visitor_id:
            user_agent = request.headers.get("user-agent", "")
            ip = request.client.host if request.client else "unknown"
            visitor_id = f"{ip}:{user_agent}"
        
        visitor_hash = hashlib.sha256(visitor_id.encode()).hexdigest()
        
        existing_stat = db.query(VisitStat).filter(
            and_(
                VisitStat.date == date_str,
                VisitStat.hour == hour,
                VisitStat.path == path
            )
        ).first()
        
        if existing_stat:
            existing_stat.visit_count += 1
        else:
            new_stat = VisitStat(
                date=date_str,
                hour=hour,
                path=path,
                visit_count=1
            )
            db.add(new_stat)
        
        existing_visitor = db.query(VisitorRecord).filter(
            and_(
                VisitorRecord.date == date_str,
                VisitorRecord.visitor_hash == visitor_hash
            )
        ).first()
        
        is_new_visitor = existing_visitor is None
        
        if not existing_visitor:
            new_visitor = VisitorRecord(
                date=date_str,
                visitor_hash=visitor_hash
            )
            db.add(new_visitor)
        
        daily_stat = db.query(DailyVisitStat).filter(
            DailyVisitStat.date == date_str
        ).first()
        
        if daily_stat:
            daily_stat.pv += 1
            if is_new_visitor:
                daily_stat.uv += 1
        else:
            new_daily = DailyVisitStat(
                date=date_str,
                pv=1,
                uv=1
            )
            db.add(new_daily)
        
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"记录访问统计失败: {e}")
    finally:
        db.close()


@router.get("/hourly", response_model=List[Dict])
def get_hourly_stats(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """获取每小时的访问统计（管理员功能）"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看统计"
        )
    
    now = datetime.utcnow()
    start_date = (now - timedelta(days=days)).strftime("%Y-%m-%d")
    
    stats = db.query(
        VisitStat.date,
        VisitStat.hour,
        func.sum(VisitStat.visit_count).label('total')
    ).filter(
        VisitStat.date >= start_date
    ).group_by(
        VisitStat.date,
        VisitStat.hour
    ).order_by(
        VisitStat.date,
        VisitStat.hour
    ).all()
    
    result = []
    for stat in stats:
        result.append({
            'date': stat.date,
            'hour': stat.hour,
            'time': f"{stat.date} {stat.hour:02d}:00",
            'count': stat.total
        })
    
    return result


@router.get("/trend", response_model=List[Dict])
def get_trend_stats(
    range_type: Literal["24h", "7d", "30d"] = Query("7d", description="时间范围: 24h, 7d, 30d"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    获取访问趋势统计（管理员功能）
    
    - 24h: 按小时统计，返回24条记录
    - 7d: 按6小时聚合，返回28条记录
    - 30d: 按天聚合，返回30条记录
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看统计"
        )
    
    now = datetime.utcnow()
    result = []
    
    if range_type == "24h":
        start_time = now - timedelta(hours=24)
        start_date = start_time.strftime("%Y-%m-%d")
        start_hour = start_time.hour
        
        stats = db.query(
            VisitStat.date,
            VisitStat.hour,
            func.sum(VisitStat.visit_count).label('total')
        ).filter(
            VisitStat.date >= start_date
        ).group_by(
            VisitStat.date,
            VisitStat.hour
        ).order_by(
            VisitStat.date,
            VisitStat.hour
        ).all()
        
        stats_dict = {(s.date, s.hour): s.total for s in stats}
        
        for i in range(24):
            t = now - timedelta(hours=23 - i)
            date_str = t.strftime("%Y-%m-%d")
            hour = t.hour
            count = stats_dict.get((date_str, hour), 0)
            result.append({
                'time': f"{date_str} {hour:02d}:00",
                'label': f"{hour:02d}:00",
                'count': count
            })
    
    elif range_type == "7d":
        start_date = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        
        stats = db.query(
            VisitStat.date,
            VisitStat.hour,
            func.sum(VisitStat.visit_count).label('total')
        ).filter(
            VisitStat.date >= start_date
        ).group_by(
            VisitStat.date,
            VisitStat.hour
        ).order_by(
            VisitStat.date,
            VisitStat.hour
        ).all()
        
        stats_dict = {(s.date, s.hour): s.total for s in stats}
        
        for i in range(28):
            t = now - timedelta(hours=6 * (27 - i))
            date_str = t.strftime("%Y-%m-%d")
            hour_group = t.hour // 6
            hour_start = hour_group * 6
            hour_end = hour_start + 5
            
            count = 0
            for h in range(hour_start, hour_end + 1):
                count += stats_dict.get((date_str, h), 0)
            
            result.append({
                'time': f"{date_str} {hour_start:02d}:00",
                'label': f"{date_str[5:]} {hour_start:02d}-{hour_end:02d}h",
                'count': count
            })
    
    elif range_type == "30d":
        start_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")
        
        daily_stats = db.query(DailyVisitStat).filter(
            DailyVisitStat.date >= start_date
        ).order_by(DailyVisitStat.date).all()
        
        stats_dict = {s.date: s.pv for s in daily_stats}
        
        for i in range(30):
            t = now - timedelta(days=29 - i)
            date_str = t.strftime("%Y-%m-%d")
            count = stats_dict.get(date_str, 0)
            result.append({
                'time': date_str,
                'label': date_str[5:],
                'count': count
            })
    
    return result


@router.get("/summary", response_model=Dict)
def get_stats_summary(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """获取统计摘要（管理员功能）- PV和UV"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看统计"
        )
    
    today = datetime.utcnow().strftime("%Y-%m-%d")
    seven_days_ago = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    total_pv = db.query(func.sum(DailyVisitStat.pv)).scalar() or 0
    total_uv = db.query(func.sum(DailyVisitStat.uv)).scalar() or 0
    
    today_stat = db.query(DailyVisitStat).filter(DailyVisitStat.date == today).first()
    today_pv = today_stat.pv if today_stat else 0
    today_uv = today_stat.uv if today_stat else 0
    
    seven_day_stats = db.query(DailyVisitStat).filter(
        DailyVisitStat.date >= seven_days_ago
    ).all()
    seven_days_pv = sum(s.pv for s in seven_day_stats)
    seven_days_uv = sum(s.uv for s in seven_day_stats)
    
    return {
        'total_visits': total_pv,
        'total_visitors': total_uv,
        'today_visits': today_pv,
        'today_visitors': today_uv,
        'seven_days_visits': seven_days_pv,
        'seven_days_visitors': seven_days_uv
    }
