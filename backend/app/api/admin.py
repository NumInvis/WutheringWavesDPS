"""
管理员相关 API
"""
import time
import traceback
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.models.user import User
from app.api.auth import get_current_admin_user

router = APIRouter(prefix="/api/admin", tags=["管理员"])

# 内存中存储日志（生产环境应该使用文件或数据库）
_logs: List[Dict[str, Any]] = []
_max_logs = 5000


def _cleanup_old_logs():
    """清理超过 7 天的日志"""
    global _logs
    seven_days_ago = int((time.time() - 7 * 24 * 60 * 60) * 1000)
    _logs = [log for log in _logs if log.get("timestamp", 0) > seven_days_ago]


def add_log(level: str, message: str, details: Any = None, user: Optional[str] = None, ip: Optional[str] = None):
    """添加日志"""
    global _logs
    log_entry = {
        "timestamp": int(time.time() * 1000),
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "level": level.lower(),
        "message": message,
        "details": details,
        "user": user,
        "ip": ip
    }
    _logs.insert(0, log_entry)
    # 限制日志数量和保存时间（7 天）
    _cleanup_old_logs()
    if len(_logs) > _max_logs:
        _logs = _logs[:_max_logs]


def log_error(error: Exception, context: str = "", user: Optional[str] = None, ip: Optional[str] = None):
    """记录错误日志（生产环境不记录完整堆栈）"""
    from app.core.config import get_settings
    settings = get_settings()
    
    details = {"error_type": type(error).__name__}
    # 仅在调试模式下记录完整堆栈
    if settings.app_debug:
        details["traceback"] = traceback.format_exc()
    
    add_log(
        level="ERROR",
        message=f"{context}: {str(error)}",
        details=details,
        user=user,
        ip=ip
    )


@router.get("/logs")
def get_logs(
    level: Optional[str] = None,
    user: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user)
):
    """获取系统日志（管理员 only）"""
    filtered_logs = _logs
    
    if level:
        filtered_logs = [log for log in filtered_logs if log['level'] == level]
    
    if user:
        filtered_logs = [log for log in filtered_logs if log.get('user') == user]
    
    return {
        "logs": filtered_logs[:limit],  # 返回最近的日志
        "total": len(filtered_logs)
    }


@router.delete("/logs", status_code=status.HTTP_204_NO_CONTENT)
def clear_logs(
    current_user: User = Depends(get_current_admin_user)
):
    """清空系统日志（管理员 only）"""
    global _logs
    _logs = []


# 导出日志工具函数
__all__ = ['add_log', 'router']
