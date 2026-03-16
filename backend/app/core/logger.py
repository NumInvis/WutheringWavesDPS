"""
日志工具模块
"""
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

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
    _cleanup_old_logs()
    if len(_logs) > _max_logs:
        _logs = _logs[:_max_logs]


def get_logs(limit: int = 100, level: Optional[str] = None) -> List[Dict[str, Any]]:
    """获取日志"""
    global _logs
    logs = _logs[:limit]
    if level:
        logs = [log for log in logs if log.get("level") == level.lower()]
    return logs


def clear_logs():
    """清空日志"""
    global _logs
    _logs = []
