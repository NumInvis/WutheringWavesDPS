"""
管理员相关API
"""
import time
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.api.auth import get_current_admin_user

router = APIRouter(prefix="/api/admin", tags=["管理员"])

# 内存中存储日志（生产环境应该使用文件或数据库）
_logs: List[Dict[str, Any]] = []
_max_logs = 1000


def add_log(level: str, message: str, details: Any = None):
    """添加日志"""
    global _logs
    log_entry = {
        "timestamp": int(time.time() * 1000),
        "level": level,
        "message": message,
        "details": details
    }
    _logs.append(log_entry)
    # 限制日志数量
    if len(_logs) > _max_logs:
        _logs = _logs[-_max_logs:]


@router.get("/logs")
def get_logs(
    current_user: User = Depends(get_current_admin_user)
):
    """获取系统日志（管理员 only）"""
    return {
        "logs": _logs[-100:]  # 返回最近100条
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
