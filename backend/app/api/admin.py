"""
管理员相关 API
"""
import traceback
import importlib
import sys
import os
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logger import add_log, get_logs, clear_logs
from app.models.user import User
from app.api.auth import get_current_admin_user

router = APIRouter(prefix="/api/admin", tags=["管理员"])

BACKUP_DIR = Path("/root/ai/WutheringWavesDPS/backups")
BACKUP_DIR.mkdir(exist_ok=True)

# 备份设置存储
backup_settings = {"max_size": 50}


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


@router.get("/backup/settings")
def get_backup_settings_api(current_user: User = Depends(get_current_admin_user)):
    """获取备份设置"""
    return {
        "max_size": backup_settings["max_size"],
        "current_size": get_backup_size()
    }


@router.post("/backup/settings")
def save_backup_settings_api(
    data: dict,
    current_user: User = Depends(get_current_admin_user)
):
    """保存备份设置"""
    max_size = data.get("max_size", 50)
    backup_settings["max_size"] = max_size
    cleanup_old_backups(max_size)
    add_log("info", f"管理员 {current_user.username} 更新备份设置: 最大{max_size}MB")
    return {"message": "设置已保存", "max_size": max_size}


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
                "name": sheet.name,
                "filename": sheet.filename,
                "sheet_number": sheet.sheet_number,
                "uploaded_by": sheet.uploaded_by,
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
