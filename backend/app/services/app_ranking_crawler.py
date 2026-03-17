"""
iOS应用畅销榜爬取服务
使用iTunes RSS API获取各地区畅销榜数据
爬取间隔：随机5-10分钟
"""
import asyncio
import aiohttp
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from app.models.app_ranking import AppInfo, RankingRecord, TopAppsCache
from app.core.logger import add_log
from app.core.database import SessionLocal

CRAWL_INTERVAL_MIN = 300
CRAWL_INTERVAL_MAX = 600

COUNTRIES = {
    "cn": "中国",
    "jp": "日本",
    "us": "美国",
    "kr": "韩国"
}

MONITORED_APPS = [
    {"name_cn": "鸣潮", "name_en": "Wuthering Waves", "app_ids": {"cn": "6475033368", "jp": "6475033368", "us": "6475033368", "kr": "6475033368"}, "developer": "Kuro Games"},
    {"name_cn": "原神", "name_en": "Genshin Impact", "app_ids": {"cn": "1467190251", "jp": "1517783697", "us": "1517783697", "kr": "1517783697"}, "developer": "miHoYo"},
    {"name_cn": "绝区零", "name_en": "Zenless Zone Zero", "app_ids": {"cn": "6508280117", "jp": "6508280117", "us": "6508280117", "kr": "6508280117"}, "developer": "miHoYo"},
    {"name_cn": "崩坏：星穹铁道", "name_en": "Honkai: Star Rail", "app_ids": {"cn": "1523037824", "jp": "1599719154", "us": "1599719154", "kr": "1599719154"}, "developer": "miHoYo"},
    {"name_cn": "明日方舟", "name_en": "Arknights", "app_ids": {"cn": "1454497357", "jp": "1454497357", "us": "1454497357", "kr": "1454497357"}, "developer": "Hypergryph"},
    {"name_cn": "明日方舟：终末地", "name_en": "Arknights: Endfield", "app_ids": {"cn": "6753859465", "jp": "6752642477", "us": "6752642477", "kr": "6752642477"}, "developer": "Hypergryph"}
]


def get_monitored_apps_from_db(db: Session) -> List[Dict]:
    apps = db.query(AppInfo).filter(AppInfo.is_active.is_(True)).all()
    result = []
    for app in apps:
        result.append({
            "name_cn": app.name_cn,
            "name_en": app.name_en,
            "app_ids": {
                "cn": app.app_id_cn,
                "jp": app.app_id_jp,
                "us": app.app_id_us,
                "kr": app.app_id_kr
            },
            "developer": app.developer or "",
            "db_id": app.id
        })
    return result


def ensure_default_apps(db: Session):
    """确保默认应用存在于数据库中"""
    for app_data in MONITORED_APPS:
        existing = db.query(AppInfo).filter(
            (AppInfo.app_id_cn == app_data["app_ids"]["cn"]) |
            (AppInfo.itunes_id == app_data["app_ids"]["cn"])
        ).first()
        if not existing:
            new_app = AppInfo(
                itunes_id=app_data["app_ids"]["cn"],
                name_cn=app_data["name_cn"],
                name_en=app_data["name_en"],
                app_id_cn=app_data["app_ids"]["cn"],
                app_id_jp=app_data["app_ids"]["jp"],
                app_id_us=app_data["app_ids"]["us"],
                app_id_kr=app_data["app_ids"]["kr"],
                developer=app_data["developer"],
                is_active=True
            )
            db.add(new_app)
    db.commit()

_crawl_task: Optional[asyncio.Task] = None
_running = False
_last_crawl_time: Optional[datetime] = None


def get_beijing_time() -> datetime:
    return datetime.utcnow() + timedelta(hours=8)


def get_beijing_date() -> str:
    return get_beijing_time().strftime("%Y-%m-%d")


def get_random_interval() -> int:
    return random.randint(CRAWL_INTERVAL_MIN, CRAWL_INTERVAL_MAX)


async def fetch_ranking(country: str, session: aiohttp.ClientSession) -> Optional[Dict]:
    url = f"https://itunes.apple.com/{country}/rss/topgrossingapplications/limit=100/json"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*'
        }
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30), headers=headers) as response:
            if response.status == 200:
                text = await response.text()
                try:
                    data = json.loads(text.strip())
                    return data
                except json.JSONDecodeError as e:
                    add_log("error", f"获取{COUNTRIES.get(country, country)}榜单异常: JSON解析失败 - {str(e)}")
                    add_log("error", f"响应内容前200字符: {text[:200] if len(text) > 200 else text}")
                    return None
            else:
                add_log("error", f"获取{COUNTRIES.get(country, country)}榜单失败: HTTP {response.status}")
                return None
    except asyncio.TimeoutError:
        add_log("error", f"获取{COUNTRIES.get(country, country)}榜单超时")
        return None
    except Exception as e:
        add_log("error", f"获取{COUNTRIES.get(country, country)}榜单异常: {type(e).__name__} - {e}")
        return None


def parse_ranking(data: Dict, country: str, monitored_apps: List[Dict]) -> Dict[str, int]:
    result = {}
    
    if not data or "feed" not in data or "entry" not in data["feed"]:
        return result
    
    entries = data["feed"]["entry"]
    target_app_ids = set()
    
    for app in monitored_apps:
        app_id = app["app_ids"].get(country)
        if app_id:
            target_app_ids.add(app_id)
    
    for rank, entry in enumerate(entries, 1):
        app_id = entry.get("id", {}).get("attributes", {}).get("im:id")
        if app_id and app_id in target_app_ids:
            result[app_id] = rank
    
    return result


def parse_top_apps(data: Dict, limit: int = 10) -> List[Dict]:
    result = []
    
    if not data or "feed" not in data or "entry" not in data["feed"]:
        return result
    
    entries = data["feed"]["entry"]
    
    for rank, entry in enumerate(entries[:limit], 1):
        app_info = {
            "rank": rank,
            "name": entry.get("im:name", {}).get("label", ""),
            "app_id": entry.get("id", {}).get("attributes", {}).get("im:id", ""),
            "icon": entry.get("im:image", [{}])[-1].get("label", "") if entry.get("im:image") else "",
            "developer": entry.get("im:artist", {}).get("label", "")
        }
        result.append(app_info)
    
    return result


async def save_ranking_records(country: str, rankings: Dict[str, int], monitored_apps: List[Dict], db: Session):
    global _last_crawl_time
    now = get_beijing_time()
    date_str = get_beijing_date()
    _last_crawl_time = now
    
    for app in monitored_apps:
        app_id = app["app_ids"].get(country)
        if not app_id:
            continue
        
        rank = rankings.get(app_id, 101)
        
        app_info = db.query(AppInfo).filter(AppInfo.id == app["db_id"]).first()
        if not app_info:
            continue
        
        record = RankingRecord(
            app_id=app_info.id,
            country=country,
            rank=rank,
            recorded_at=now,
            date=date_str
        )
        db.add(record)
    
    db.commit()


async def save_top_apps_cache(country: str, top_apps: List[Dict], db: Session):
    now = get_beijing_time()
    
    cache = TopAppsCache(
        country=country,
        rank_data=json.dumps(top_apps, ensure_ascii=False),
        recorded_at=now
    )
    db.add(cache)
    db.commit()


async def crawl_country(country: str, session: aiohttp.ClientSession, monitored_apps: List[Dict], db: Session):
    data = await fetch_ranking(country, session)
    
    if data:
        rankings = parse_ranking(data, country, monitored_apps)
        await save_ranking_records(country, rankings, monitored_apps, db)
        
        top_apps = parse_top_apps(data, 10)
        await save_top_apps_cache(country, top_apps, db)
        
        add_log("info", f"爬取{COUNTRIES.get(country, country)}榜单完成: {len(rankings)}个目标游戏")
    else:
        add_log("warning", f"爬取{COUNTRIES.get(country, country)}榜单失败")


async def crawl_all_countries():
    add_log("info", "开始爬取iOS畅销榜数据...")
    
    db = SessionLocal()
    
    try:
        ensure_default_apps(db)
        monitored_apps = get_monitored_apps_from_db(db)
        add_log("info", f"监控应用数量: {len(monitored_apps)}")
        
        async with aiohttp.ClientSession() as session:
            tasks = [crawl_country(country, session, monitored_apps, db) for country in COUNTRIES.keys()]
            await asyncio.gather(*tasks)
        
        add_log("info", "iOS畅销榜爬取完成")
    except Exception as e:
        add_log("error", f"iOS畅销榜爬取失败: {e}")
    finally:
        db.close()


async def crawl_scheduler():
    global _running
    _running = True
    
    add_log("info", "iOS畅销榜爬取调度器已启动，开始初始化爬取...")
    
    await crawl_all_countries()
    
    while _running:
        try:
            interval = get_random_interval()
            add_log("info", f"下次爬取将在 {interval // 60} 分 {interval % 60} 秒后执行")
            await asyncio.sleep(interval)
            if _running:
                await crawl_all_countries()
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
    add_log("info", "iOS畅销榜爬取后台任务已创建")


def stop_crawl_scheduler():
    global _crawl_task, _running
    
    _running = False
    
    if _crawl_task is not None and not _crawl_task.done():
        _crawl_task.cancel()
        _crawl_task = None
        add_log("info", "iOS畅销榜爬取后台任务已停止")


async def manual_crawl():
    await crawl_all_countries()


def get_scheduler_status() -> Dict:
    return {
        "running": _running,
        "interval_min": CRAWL_INTERVAL_MIN,
        "interval_max": CRAWL_INTERVAL_MAX,
        "monitored_apps": len(MONITORED_APPS),
        "countries": list(COUNTRIES.keys()),
        "last_crawl_time": _last_crawl_time.strftime("%Y-%m-%d %H:%M:%S") if _last_crawl_time else None,
        "next_crawl": "运行中" if _running else "已停止"
    }


def get_monitored_apps() -> List[Dict]:
    return MONITORED_APPS.copy()
