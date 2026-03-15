"""
访问统计相关API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Dict
from datetime import datetime, timedelta

from app.core.database import get_db, SessionLocal
from app.models.visit_stat import VisitStat
from app.schemas.visit_stat import VisitStatResponse
from app.api.auth import get_current_active_user

router = APIRouter(prefix="/api/visit-stats", tags=["访问统计"])


def record_visit(path: str):
    """记录访问统计（内部函数）"""
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        date_str = now.strftime("%Y-%m-%d")
        hour = now.hour
        
        # 查找是否已有同日期、同小时、同路径的记录
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
        
        db.commit()
    except Exception:
        db.rollback()
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
    
    # 计算起始日期
    now = datetime.utcnow()
    start_date = (now - timedelta(days=days)).strftime("%Y-%m-%d")
    
    # 查询统计数据
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
    
    # 格式化结果
    result = []
    for stat in stats:
        result.append({
            'date': stat.date,
            'hour': stat.hour,
            'time': f"{stat.date} {stat.hour:02d}:00",
            'count': stat.total
        })
    
    return result


@router.get("/summary", response_model=Dict)
def get_stats_summary(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """获取统计摘要（管理员功能）"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看统计"
        )
    
    # 总访问数
    total_visits = db.query(func.sum(VisitStat.visit_count)).scalar() or 0
    
    # 今天的访问数
    today = datetime.utcnow().strftime("%Y-%m-%d")
    today_visits = db.query(func.sum(VisitStat.visit_count)).filter(
        VisitStat.date == today
    ).scalar() or 0
    
    # 过去7天的访问数
    seven_days_ago = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
    seven_days_visits = db.query(func.sum(VisitStat.visit_count)).filter(
        VisitStat.date >= seven_days_ago
    ).scalar() or 0
    
    return {
        'total_visits': total_visits,
        'today_visits': today_visits,
        'seven_days_visits': seven_days_visits
    }
