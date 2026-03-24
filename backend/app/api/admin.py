"""
管理员相关 API
"""
import traceback
import importlib
import sys
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from app.core.database import get_db
from app.core.logger import add_log, get_logs, clear_logs
from app.models.user import User
from app.api.auth import get_current_admin_user

router = APIRouter(prefix="/api/admin", tags=["管理员"])

BACKUP_DIR = Path("/root/ai/WutheringWavesDPS/backups")
BACKUP_DIR.mkdir(exist_ok=True)

# 备份设置存储
backup_settings = {
    "max_size": 50,  # MB
    "backup_interval": 60  # 分钟
}

# 定时备份任务
_backup_task = None
_backup_running = False


def get_backup_size():
    """获取当前备份目录大小（MB）"""
    total_size = 0
    for f in BACKUP_DIR.rglob("*"):
        if f.is_file():
            total_size += f.stat().st_size
    return round(total_size / (1024 * 1024), 2)


def cleanup_old_backups(max_size_mb):
    """清理旧备份直到总大小在限制内"""
    files = sorted(BACKUP_DIR.glob("*"), key=lambda x: x.stat().st_mtime)
    files = [f for f in files if f.is_file()]
    
    while get_backup_size() > max_size_mb and files:
        oldest_file = files.pop(0)
        try:
            oldest_file.unlink()
            add_log("info", f"清理旧备份: {oldest_file.name}")
        except Exception as e:
            add_log("error", f"清理备份失败: {e}")


async def auto_backup():
    """自动执行备份"""
    global _backup_running
    if _backup_running:
        return
    
    _backup_running = True
    try:
        from app.models.spreadsheet import Spreadsheet
        from app.models.app_ranking import AppInfo, RankingRecord
        
        db = next(get_db())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 备份表格
        spreadsheets = db.query(Spreadsheet).all()
        spreadsheet_backup = BACKUP_DIR / f"spreadsheet_auto_backup_{timestamp}.json"
        spreadsheet_data = []
        for sheet in spreadsheets:
            spreadsheet_data.append({
                "id": sheet.id,
                "sheet_number": sheet.sheet_number,
                "user_id": sheet.user_id,
                "title": sheet.title,
                "description": sheet.description,
                "category": sheet.category,
                "area": sheet.area,
                "is_draft": sheet.is_draft,
                "is_banned": sheet.is_banned,
                "is_featured": sheet.is_featured,
                "is_public": sheet.is_public,
                "star_count": sheet.star_count,
                "view_count": sheet.view_count,
                "download_count": sheet.download_count,
                "file_url": sheet.file_url,
                "file_size": sheet.file_size,
                "thumbnail_url": sheet.thumbnail_url,
                "extra_metadata": sheet.extra_metadata,
                "is_deleted": sheet.is_deleted,
                "deleted_at": sheet.deleted_at.isoformat() if sheet.deleted_at else None,
                "created_at": sheet.created_at.isoformat() if sheet.created_at else None,
                "updated_at": sheet.updated_at.isoformat() if sheet.updated_at else None
            })
        with open(spreadsheet_backup, "w", encoding="utf-8") as f:
            json.dump(spreadsheet_data, f, ensure_ascii=False, indent=2)
        
        # 备份排行榜
        apps = db.query(AppInfo).all()
        records = db.query(RankingRecord).all()
        ranking_backup = BACKUP_DIR / f"ranking_auto_backup_{timestamp}.json"
        ranking_data = {"apps": [], "records": []}
        for app in apps:
            ranking_data["apps"].append({
                "id": app.id,
                "itunes_id": app.itunes_id,
                "name_cn": app.name_cn,
                "name_en": app.name_en,
                "icon_url": app.icon_url,
                "developer": app.developer,
                "is_active": app.is_active
            })
        for record in records:
            ranking_data["records"].append({
                "id": record.id,
                "app_id": record.app_id,
                "country": record.country,
                "rank": record.rank,
                "recorded_at": record.recorded_at.isoformat() if record.recorded_at else None,
                "date": record.date
            })
        with open(ranking_backup, "w", encoding="utf-8") as f:
            json.dump(ranking_data, f, ensure_ascii=False, indent=2)
        
        cleanup_old_backups(backup_settings["max_size"])
        add_log("info", f"自动备份完成: spreadsheet_auto_backup_{timestamp}.json, ranking_auto_backup_{timestamp}.json")
    except Exception as e:
        add_log("error", f"自动备份失败: {e}")
    finally:
        _backup_running = False


async def backup_scheduler():
    """备份调度器"""
    import asyncio
    global _backup_running
    
    add_log("info", "自动备份调度器已启动")
    
    while _backup_task and not _backup_task.done():
        try:
            interval = backup_settings["backup_interval"] * 60  # 转换为秒
            await asyncio.sleep(interval)
            await auto_backup()
        except asyncio.CancelledError:
            break
        except Exception as e:
            add_log("error", f"备份调度器错误: {e}")
            await asyncio.sleep(60)


def start_backup_scheduler():
    """启动备份调度器"""
    import asyncio
    global _backup_task
    
    if _backup_task and not _backup_task.done():
        return
    
    loop = asyncio.get_event_loop()
    _backup_task = loop.create_task(backup_scheduler())


def stop_backup_scheduler():
    """停止备份调度器"""
    global _backup_task
    if _backup_task and not _backup_task.done():
        _backup_task.cancel()
        _backup_task = None


@router.get("/backup/settings")
def get_backup_settings_api(current_user: User = Depends(get_current_admin_user)):
    """获取备份设置"""
    return {
        "max_size": backup_settings["max_size"],
        "backup_interval": backup_settings["backup_interval"],
        "current_size": get_backup_size()
    }


@router.post("/backup/settings")
def save_backup_settings_api(
    data: dict,
    current_user: User = Depends(get_current_admin_user)
):
    """保存备份设置"""
    max_size = data.get("max_size", 50)
    backup_interval = data.get("backup_interval", 60)
    
    backup_settings["max_size"] = max_size
    backup_settings["backup_interval"] = backup_interval
    
    cleanup_old_backups(max_size)
    add_log("info", f"管理员 {current_user.username} 更新备份设置: 最大{max_size}MB, 间隔{backup_interval}分钟")
    return {
        "message": "设置已保存", 
        "max_size": max_size,
        "backup_interval": backup_interval
    }


@router.get("/backup/spreadsheet")
def export_spreadsheet_backup(current_user: User = Depends(get_current_admin_user)):
    """导出表格备份"""
    try:
        from app.models.spreadsheet import Spreadsheet
        
        db = next(get_db())
        spreadsheets = db.query(Spreadsheet).all()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = BACKUP_DIR / f"spreadsheet_backup_{timestamp}.json"
        
        data = []
        for sheet in spreadsheets:
            data.append({
                "id": sheet.id,
                "sheet_number": sheet.sheet_number,
                "user_id": sheet.user_id,
                "title": sheet.title,
                "description": sheet.description,
                "category": sheet.category,
                "area": sheet.area,
                "is_draft": sheet.is_draft,
                "is_banned": sheet.is_banned,
                "is_featured": sheet.is_featured,
                "is_public": sheet.is_public,
                "star_count": sheet.star_count,
                "view_count": sheet.view_count,
                "download_count": sheet.download_count,
                "file_url": sheet.file_url,
                "file_size": sheet.file_size,
                "thumbnail_url": sheet.thumbnail_url,
                "extra_metadata": sheet.extra_metadata,
                "is_deleted": sheet.is_deleted,
                "deleted_at": sheet.deleted_at.isoformat() if sheet.deleted_at else None,
                "created_at": sheet.created_at.isoformat() if sheet.created_at else None,
                "updated_at": sheet.updated_at.isoformat() if sheet.updated_at else None
            })
        
        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        cleanup_old_backups(backup_settings["max_size"])
        add_log("info", f"管理员 {current_user.username} 导出表格备份")
        
        return FileResponse(
            path=backup_file,
            filename=backup_file.name,
            media_type="application/json"
        )
    except Exception as e:
        log_error(e, "导出表格备份", user=current_user.username)
        raise HTTPException(status_code=500, detail="导出失败")


@router.get("/backup/tieba")
def export_tieba_backup(current_user: User = Depends(get_current_admin_user)):
    """导出贴吧备份"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = BACKUP_DIR / f"tieba_backup_{timestamp}.csv"
        
        # 简单示例，实际应从数据库获取贴吧数据
        headers = ["tieba_name", "post_count", "last_updated"]
        sample_data = [
            ["贴吧1", 100, datetime.now().isoformat()],
            ["贴吧2", 200, datetime.now().isoformat()]
        ]
        
        with open(backup_file, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(sample_data)
        
        cleanup_old_backups(backup_settings["max_size"])
        add_log("info", f"管理员 {current_user.username} 导出贴吧备份")
        
        return FileResponse(
            path=backup_file,
            filename=backup_file.name,
            media_type="text/csv"
        )
    except Exception as e:
        log_error(e, "导出贴吧备份", user=current_user.username)
        raise HTTPException(status_code=500, detail="导出失败")


@router.get("/backup/ranking")
def export_ranking_backup(current_user: User = Depends(get_current_admin_user)):
    """导出iOS排行榜备份"""
    try:
        from app.models.app_ranking import AppInfo, RankingRecord
        
        db = next(get_db())
        apps = db.query(AppInfo).all()
        records = db.query(RankingRecord).all()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = BACKUP_DIR / f"ranking_backup_{timestamp}.json"
        
        data = {
            "apps": [],
            "records": []
        }
        
        for app in apps:
            data["apps"].append({
                "id": app.id,
                "itunes_id": app.itunes_id,
                "name_cn": app.name_cn,
                "name_en": app.name_en,
                "icon_url": app.icon_url,
                "developer": app.developer,
                "is_active": app.is_active
            })
        
        for record in records:
            data["records"].append({
                "id": record.id,
                "app_id": record.app_id,
                "country": record.country,
                "rank": record.rank,
                "recorded_at": record.recorded_at.isoformat() if record.recorded_at else None,
                "date": record.date
            })
        
        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        cleanup_old_backups(backup_settings["max_size"])
        add_log("info", f"管理员 {current_user.username} 导出排行榜备份")
        
        return FileResponse(
            path=backup_file,
            filename=backup_file.name,
            media_type="application/json"
        )
    except Exception as e:
        log_error(e, "导出排行榜备份", user=current_user.username)
        raise HTTPException(status_code=500, detail="导出失败")


def log_error(error: Exception, context: str = "", user: Optional[str] = None, ip: Optional[str] = None):
    """记录错误日志（生产环境不记录完整堆栈）"""
    from app.core.config import get_settings
    settings = get_settings()
    
    details = {"error_type": type(error).__name__}
    if settings.app_debug:
        details["traceback"] = traceback.format_exc()
    
    add_log(
        level="error",
        message=f"{context}: {str(error)}",
        details=details,
        user=user,
        ip=ip
    )


@router.get("/logs")
def get_logs_api(
    level: Optional[str] = None,
    user: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user)
):
    """获取系统日志（管理员 only）"""
    logs = get_logs(limit=limit, level=level)
    
    if user:
        logs = [log for log in logs if log.get('user') == user]
    
    return {
        "logs": logs,
        "total": len(logs)
    }


@router.delete("/logs", status_code=status.HTTP_204_NO_CONTENT)
def clear_logs_api(
    current_user: User = Depends(get_current_admin_user)
):
    """清空系统日志（管理员 only）"""
    clear_logs()


@router.post("/hot-reload")
def hot_reload_modules(
    modules: Optional[List[str]] = None,
    current_user: User = Depends(get_current_admin_user)
):
    """热更新指定模块（管理员 only）"""
    reloaded = []
    errors = []
    
    default_modules = [
        "app.api.tieba",
        "app.services.tieba_crawler",
        "app.models.tieba",
    ]
    
    target_modules = modules if modules else default_modules
    
    for module_name in target_modules:
        try:
            if module_name in sys.modules:
                module = sys.modules[module_name]
                importlib.reload(module)
                reloaded.append(module_name)
                add_log("info", f"热更新模块成功: {module_name}")
            else:
                __import__(module_name)
                reloaded.append(f"{module_name} (新加载)")
                add_log("info", f"新加载模块: {module_name}")
        except Exception as e:
            errors.append({"module": module_name, "error": str(e)})
            add_log("error", f"热更新模块失败: {module_name} - {e}")
    
    return {
        "reloaded": reloaded,
        "errors": errors,
        "message": f"成功更新 {len(reloaded)} 个模块" + (f"，{len(errors)} 个失败" if errors else "")
    }


@router.get("/settings/data-observer")
def get_data_observer_settings(current_user: User = Depends(get_current_admin_user)):
    """获取数据观察页面设置"""
    try:
        import json
        import os
        from pathlib import Path
        
        settings_file = Path(__file__).parent / "../data" / "data_observer_settings.json"
        
        if settings_file.exists():
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        else:
            settings = {
                "leftColumnWidth": 1,
                "rightColumnWidth": 1.5,
                "barChartHeight": 280,
                "hotListHeight": 400,
                "statsDays": 3,
                "hotPostsLimit": 10,
                "fontSizeScale": 1,
                "chartHeightScale": 1,
                "panelOpacity": 0.92,
                "borderRadius": 8
            }
            
            # 确保目录存在
            settings_file.parent.mkdir(exist_ok=True)
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        
        return {"settings": settings}
    except Exception as e:
        log_error(e, "获取数据观察页面设置")
        raise HTTPException(status_code=500, detail="获取设置失败")


from pydantic import BaseModel

class DataObserverSettings(BaseModel):
    leftColumnWidth: float = 1
    rightColumnWidth: float = 1.5
    barChartHeight: int = 280
    hotListHeight: int = 400
    statsDays: int = 3
    hotPostsLimit: int = 10
    fontSizeScale: float = 1
    chartHeightScale: float = 1
    panelOpacity: float = 0.92
    borderRadius: int = 8

@router.post("/settings/data-observer")
def save_data_observer_settings(
    settings: DataObserverSettings,
    current_user: User = Depends(get_current_admin_user)
):
    """保存数据观察页面设置"""
    try:
        import json
        from pathlib import Path
        
        settings_file = Path(__file__).parent / "../data" / "data_observer_settings.json"
        
        # 确保目录存在
        settings_file.parent.mkdir(exist_ok=True)
        
        # 转换为字典
        settings_dict = settings.model_dump()
        
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings_dict, f, ensure_ascii=False, indent=2)
        
        add_log("info", f"数据观察页面设置已更新 by {current_user.username}")
        return {"message": "设置已保存"}
    except Exception as e:
        log_error(e, "保存数据观察页面设置")
        raise HTTPException(status_code=500, detail="保存设置失败")


@router.get("/stats/users")
def get_user_stats(current_user: User = Depends(get_current_admin_user)):
    """获取用户统计数据（管理员 only）"""
    try:
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        db = next(get_db())
        
        # 总注册用户数
        total_users = db.query(func.count(User.id)).scalar()
        
        # 今日注册用户数
        today = datetime.now().strftime("%Y-%m-%d")
        today_start = datetime.strptime(today, "%Y-%m-%d")
        today_end = today_start + timedelta(days=1)
        today_users = db.query(func.count(User.id)).filter(
            User.created_at >= today_start,
            User.created_at < today_end
        ).scalar()
        
        # 本周注册用户数
        week_start = datetime.now() - timedelta(days=7)
        week_users = db.query(func.count(User.id)).filter(
            User.created_at >= week_start
        ).scalar()
        
        # 本月注册用户数
        month_start = datetime.now().replace(day=1)
        month_users = db.query(func.count(User.id)).filter(
            User.created_at >= month_start
        ).scalar()
        
        # 管理员数量
        admin_count = db.query(func.count(User.id)).filter(
            User.is_admin == True
        ).scalar()
        
        # 活跃用户（最近7天登录）
        active_threshold = datetime.now() - timedelta(days=7)
        active_users = db.query(func.count(User.id)).filter(
            User.last_login_at >= active_threshold
        ).scalar()
        
        add_log("info", f"管理员 {current_user.username} 查询用户统计")
        
        return {
            "total_users": total_users,
            "today_users": today_users,
            "week_users": week_users,
            "month_users": month_users,
            "admin_count": admin_count,
            "active_users": active_users
        }
    except Exception as e:
        log_error(e, "获取用户统计")
        raise HTTPException(status_code=500, detail="获取用户统计失败")


@router.get("/users")
def get_all_users(
    page: int = 1,
    page_size: int = 50,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_admin_user)
):
    """获取所有注册用户列表（管理员 only）"""
    try:
        from sqlalchemy import or_
        
        db = next(get_db())
        
        # 构建查询
        query = db.query(User)
        
        # 搜索过滤
        if search:
            search_filter = or_(
                User.username.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.display_name.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        # 统计总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        users = query.order_by(User.created_at.desc()).offset(offset).limit(page_size).all()
        
        # 格式化用户数据
        user_list = []
        for user in users:
            user_list.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "display_name": user.display_name,
                "avatar_url": user.avatar_url,
                "bio": user.bio,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "is_admin": user.is_admin,
                "role": user.role,
                "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None
            })
        
        add_log("info", f"管理员 {current_user.username} 查询用户列表，第{page}页")
        
        return {
            "users": user_list,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    except Exception as e:
        log_error(e, "获取用户列表")
        raise HTTPException(status_code=500, detail="获取用户列表失败")
