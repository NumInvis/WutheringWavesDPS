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


def add_log(level: str, message: str, details: Any = None, user: Optional[str] = None, ip: Optional[str] = None):
    """添加日志"""
    global _logs
    log_entry = {
        "timestamp": int(time.time() * 1000),
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "level": level,
        "message": message,
        "details": details,
        "user": user,
        "ip": ip
    }
    _logs.insert(0, log_entry)  # 新日志插入到开头
    # 限制日志数量和保存时间（7 天）
    _cleanup_old_logs()
    if len(_logs) > _max_logs:
        _logs = _logs[:_max_logs]


def _cleanup_old_logs():
    """清理超过 7 天的日志"""
    global _logs
    seven_days_ago = int((time.time() - 7 * 24 * 60 * 60) * 1000)
    _logs = [log for log in _logs if log.get("timestamp", 0) > seven_days_ago]


# 初始化一些示例日志
def _init_sample_logs():
    """初始化示例日志"""
    if len(_logs) == 0:
        add_log("INFO", "系统启动", {"version": "Beta1.0"})
        add_log("INFO", "日志系统初始化完成")
        add_log("WARN", "检测到网络波动", {"retry_count": 3})
        add_log("ERROR", "测试错误日志", {"test": True})
        add_log("INFO", "用户登录成功", {"user": "admin"})
        add_log("INFO", "表格上传", {"user": "admin", "title": "测试表格"})
        add_log("WARN", "API 请求超时", {"endpoint": "/api/spreadsheets", "duration": "5s"})
        add_log("INFO", "密码修改", {"user": "admin"})
        add_log("ERROR", "数据库连接失败", {"retry": True, "error": "timeout"})
        add_log("INFO", "系统运行正常")


_init_sample_logs()


def add_log(level: str, message: str, details: Any = None, user: Optional[str] = None, ip: Optional[str] = None):
    """添加日志"""
    global _logs
    log_entry = {
        "timestamp": int(time.time() * 1000),
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "level": level,
        "message": message,
        "details": details,
        "user": user,
        "ip": ip
    }
    _logs.insert(0, log_entry)  # 新日志插入到开头
    # 限制日志数量和保存时间（7 天）
    _cleanup_old_logs()
    if len(_logs) > _max_logs:
        _logs = _logs[:_max_logs]


def _cleanup_old_logs():
    """清理超过 7 天的日志"""
    global _logs
    seven_days_ago = int((time.time() - 7 * 24 * 60 * 60) * 1000)
    _logs = [log for log in _logs if log.get("timestamp", 0) > seven_days_ago]


def log_error(error: Exception, context: str = "", user: Optional[str] = None, ip: Optional[str] = None):
    """记录错误日志"""
    add_log(
        level="ERROR",
        message=f"{context}: {str(error)}",
        details={
            "error_type": type(error).__name__,
            "traceback": traceback.format_exc()
        },
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
