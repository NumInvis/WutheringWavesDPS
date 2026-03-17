"""
iOS应用排名 API
提供各地区iOS畅销榜排名数据
"""
import json
import aiohttp
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.core.database import get_db
from app.models.app_ranking import AppInfo, RankingRecord, TopAppsCache
from app.models.user import User
from app.api.auth import get_current_active_user
from app.core.logger import add_log

router = APIRouter(prefix="/api/ranking", tags=["iOS畅销榜"])

COUNTRIES = {
    "cn": "中国",
    "jp": "日本",
    "us": "美国",
    "kr": "韩国"
}

COUNTRY_FLAGS = {
    "cn": "🇨🇳",
    "jp": "🇯🇵",
    "us": "🇺🇸",
    "kr": "🇰🇷"
}


def get_beijing_time():
    return datetime.utcnow() + timedelta(hours=8)


def get_beijing_date():
    return get_beijing_time().strftime("%Y-%m-%d")


@router.get("/apps")
def get_monitored_apps(db: Session = Depends(get_db)):
    """获取监控的游戏列表"""
    apps = db.query(AppInfo).filter(AppInfo.is_active.is_(True)).all()
    
    result = []
    for app in apps:
        result.append({
            "id": app.id,
            "name_cn": app.name_cn,
            "name_en": app.name_en,
            "app_id_cn": app.app_id_cn,
            "app_id_jp": app.app_id_jp,
            "app_id_us": app.app_id_us,
            "app_id_kr": app.app_id_kr,
            "icon_url": app.icon_url,
            "developer": app.developer
        })
    
    return {"apps": result, "total": len(result)}


@router.get("/current")
def get_current_ranking(db: Session = Depends(get_db)):
    apps = db.query(AppInfo).filter(AppInfo.is_active.is_(True)).all()
    
    result = []
    for app in apps:
        app_data = {
            "id": app.id,
            "name_cn": app.name_cn,
            "name_en": app.name_en,
            "icon_url": app.icon_url,
            "developer": app.developer,
            "rankings": {}
        }
        
        for country in COUNTRIES.keys():
            latest_record = db.query(RankingRecord).filter(
                RankingRecord.app_id == app.id,
                RankingRecord.country == country
            ).order_by(desc(RankingRecord.recorded_at)).first()
            
            if latest_record:
                app_data["rankings"][country] = {
                    "rank": latest_record.rank,
                    "recorded_at": latest_record.recorded_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "flag": COUNTRY_FLAGS.get(country, ""),
                    "country_name": COUNTRIES.get(country, country)
                }
            else:
                app_data["rankings"][country] = {
                    "rank": 101,
                    "recorded_at": None,
                    "flag": COUNTRY_FLAGS.get(country, ""),
                    "country_name": COUNTRIES.get(country, country)
                }
        
        result.append(app_data)
    
    # 按中国排名排序（排名越小越靠前）
    result.sort(key=lambda x: x["rankings"]["cn"]["rank"])
    
    latest_time = db.query(func.max(RankingRecord.recorded_at)).scalar()
    
    return {
        "apps": result,
        "total": len(result),
        "countries": COUNTRIES,
        "flags": COUNTRY_FLAGS,
        "last_updated": latest_time.strftime("%Y-%m-%d %H:%M:%S") if latest_time else None
    }


@router.get("/history/{app_id}")
def get_ranking_history(
    app_id: str,
    days: int = Query(7, ge=1, le=180),
    country: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """获取指定游戏的历史排名趋势"""
    app = db.query(AppInfo).filter(AppInfo.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="游戏不存在")
    
    beijing_now = get_beijing_time()
    start_time = beijing_now - timedelta(days=days)
    
    query = db.query(RankingRecord).filter(
        RankingRecord.app_id == app_id,
        RankingRecord.recorded_at >= start_time
    )
    
    if country:
        query = query.filter(RankingRecord.country == country)
    
    records = query.order_by(RankingRecord.recorded_at).all()
    
    history_by_country = {}
    for record in records:
        if record.country not in history_by_country:
            history_by_country[record.country] = []
        history_by_country[record.country].append({
            "rank": record.rank,
            "recorded_at": record.recorded_at.strftime("%Y-%m-%d %H:%M:%S"),
            "date": record.date
        })
    
    return {
        "app": {
            "id": app.id,
            "name_cn": app.name_cn,
            "name_en": app.name_en
        },
        "history": history_by_country,
        "days": days,
        "countries": COUNTRIES,
        "flags": COUNTRY_FLAGS
    }


@router.get("/compare")
def get_ranking_compare(
    app_ids: str = Query(..., description="逗号分隔的游戏ID"),
    country: str = Query("cn"),
    days: int = Query(7, ge=1, le=180),
    db: Session = Depends(get_db)
):
    """获取多游戏对比数据"""
    app_id_list = [id.strip() for id in app_ids.split(",")]
    
    apps = db.query(AppInfo).filter(AppInfo.id.in_(app_id_list)).all()
    if not apps:
        raise HTTPException(status_code=404, detail="未找到任何游戏")
    
    beijing_now = get_beijing_time()
    start_time = beijing_now - timedelta(days=days)
    
    result = []
    for app in apps:
        records = db.query(RankingRecord).filter(
            RankingRecord.app_id == app.id,
            RankingRecord.country == country,
            RankingRecord.recorded_at >= start_time
        ).order_by(RankingRecord.recorded_at).all()
        
        result.append({
            "app": {
                "id": app.id,
                "name_cn": app.name_cn,
                "name_en": app.name_en
            },
            "data": [
                {
                    "rank": r.rank,
                    "recorded_at": r.recorded_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "date": r.date
                }
                for r in records
            ]
        })
    
    return {
        "apps": result,
        "country": country,
        "country_name": COUNTRIES.get(country, country),
        "flag": COUNTRY_FLAGS.get(country, ""),
        "days": days
    }


@router.get("/top/{country}")
def get_top_apps(country: str, limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    """获取指定地区的TOP应用"""
    if country not in COUNTRIES:
        raise HTTPException(status_code=400, detail="不支持的地区")
    
    cache = db.query(TopAppsCache).filter(
        TopAppsCache.country == country
    ).order_by(desc(TopAppsCache.recorded_at)).first()
    
    if not cache:
        return {
            "country": country,
            "country_name": COUNTRIES.get(country, country),
            "flag": COUNTRY_FLAGS.get(country, ""),
            "apps": [],
            "recorded_at": None
        }
    
    apps = json.loads(cache.rank_data)
    
    return {
        "country": country,
        "country_name": COUNTRIES.get(country, country),
        "flag": COUNTRY_FLAGS.get(country, ""),
        "apps": apps[:limit],
        "recorded_at": cache.recorded_at.strftime("%Y-%m-%d %H:%M:%S")
    }


@router.get("/top-all")
def get_all_top_apps(db: Session = Depends(get_db)):
    """获取所有地区的TOP应用"""
    result = {}
    
    for country in COUNTRIES.keys():
        cache = db.query(TopAppsCache).filter(
            TopAppsCache.country == country
        ).order_by(desc(TopAppsCache.recorded_at)).first()
        
        if cache:
            result[country] = {
                "country": country,
                "country_name": COUNTRIES.get(country, country),
                "flag": COUNTRY_FLAGS.get(country, ""),
                "apps": json.loads(cache.rank_data),
                "recorded_at": cache.recorded_at.strftime("%Y-%m-%d %H:%M:%S")
            }
        else:
            result[country] = {
                "country": country,
                "country_name": COUNTRIES.get(country, country),
                "flag": COUNTRY_FLAGS.get(country, ""),
                "apps": [],
                "recorded_at": None
            }
    
    return result


@router.post("/crawl")
async def trigger_crawl(current_user: User = Depends(get_current_active_user)):
    """手动触发爬取 - 仅管理员"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以执行此操作"
        )
    
    try:
        from app.services.app_ranking_crawler import crawl_all_countries
        await crawl_all_countries()
        return {"message": "爬取完成"}
    except Exception as e:
        add_log("error", f"爬取任务执行失败: {e}")
        raise HTTPException(status_code=500, detail=f"爬取任务执行失败: {e}")


@router.get("/crawl-status")
def get_crawl_status():
    """获取爬取任务状态"""
    try:
        from app.services.app_ranking_crawler import get_scheduler_status
        return get_scheduler_status()
    except Exception as e:
        return {"error": str(e), "running": False}


@router.get("/scheduler/start")
def start_scheduler():
    """启动定时爬取调度器"""
    try:
        from app.services.app_ranking_crawler import start_crawl_scheduler
        start_crawl_scheduler()
        return {"message": "爬取调度器已启动"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动失败: {e}")


@router.get("/scheduler/stop")
def stop_scheduler():
    """停止定时爬取调度器"""
    try:
        from app.services.app_ranking_crawler import stop_crawl_scheduler
        stop_crawl_scheduler()
        return {"message": "爬取调度器已停止"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止失败: {e}")


@router.get("/history")
def get_all_ranking_history(
    range: str = Query("30d", description="时间范围: 24h, 30d, 180d"),
    db: Session = Depends(get_db)
):
    """获取所有游戏的历史排名数据"""
    beijing_now = get_beijing_time()
    
    if range == "24h":
        start_time = beijing_now - timedelta(hours=24)
    elif range == "30d":
        start_time = beijing_now - timedelta(days=30)
    elif range == "180d":
        start_time = beijing_now - timedelta(days=180)
    else:
        start_time = beijing_now - timedelta(days=30)
    
    records = db.query(RankingRecord).filter(
        RankingRecord.recorded_at >= start_time
    ).order_by(RankingRecord.recorded_at).all()
    
    result = []
    for record in records:
        result.append({
            "id": record.id,
            "app_id": record.app_id,
            "country": record.country,
            "rank": record.rank,
            "recorded_at": record.recorded_at.strftime("%Y-%m-%d %H:%M:%S")
        })
    
    return {"records": result, "range": range}


@router.get("/search")
async def search_itunes_apps(query: str = Query(..., description="搜索关键词或iTunes ID")):
    """搜索iTunes应用"""
    try:
        url = "https://itunes.apple.com/search"
        params = {
            "term": query,
            "country": "cn",
            "media": "software",
            "limit": 10
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, timeout=10) as response:
                text = await response.text()
                data = json.loads(text)
                return {"results": data.get("results", [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


from pydantic import BaseModel

class AddAppRequest(BaseModel):
    itunes_id: str
    name_cn: str
    name_en: str = ""
    icon_url: str = ""
    developer: str = ""

@router.post("/apps")
def add_app(
    request: AddAppRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """添加新游戏到监控列表 - 仅管理员"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以执行此操作"
        )
    
    existing = db.query(AppInfo).filter(AppInfo.itunes_id == request.itunes_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="该游戏已存在")
    
    new_app = AppInfo(
        itunes_id=request.itunes_id,
        name_cn=request.name_cn,
        name_en=request.name_en or request.name_cn,
        app_id_cn=request.itunes_id,
        app_id_jp=request.itunes_id,
        app_id_us=request.itunes_id,
        app_id_kr=request.itunes_id,
        icon_url=request.icon_url,
        developer=request.developer,
        is_active=True
    )
    
    db.add(new_app)
    db.commit()
    db.refresh(new_app)
    
    add_log("info", f"管理员 {current_user.username} 添加了新游戏: {request.name_cn} (ID: {request.itunes_id})")
    
    return {"message": "添加成功", "app": {
        "id": new_app.id,
        "name_cn": new_app.name_cn,
        "itunes_id": new_app.itunes_id
    }}


@router.delete("/apps/{app_id}")
def delete_app(
    app_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除游戏 - 仅管理员"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以执行此操作"
        )
    
    app = db.query(AppInfo).filter(AppInfo.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="游戏不存在")
    
    app_name = app.name_cn
    db.delete(app)
    db.commit()
    
    add_log("info", f"管理员 {current_user.username} 删除了游戏: {app_name} (ID: {app_id})")
    
    return {"message": "删除成功"}
