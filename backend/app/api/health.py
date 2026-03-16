"""
健康检查 API
用于监控系统状态和自动恢复
"""
import os
import time
import sqlite3
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db, engine
from app.core.config import get_settings

router = APIRouter(prefix="/api/health", tags=["健康检查"])
settings = get_settings()

# 启动时间
START_TIME = time.time()


@router.get("/")
async def basic_health():
    """基础健康检查"""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/detailed")
async def detailed_health(db: Session = Depends(get_db)):
    """详细健康检查"""
    checks = {
        "database": await _check_database(db),
        "disk": await _check_disk_space(),
        "memory": await _check_memory(),
        "uptime": await _check_uptime(),
        "uploads": await _check_uploads_dir()
    }
    
    # 检查所有组件状态
    all_healthy = all(check["status"] == "healthy" for check in checks.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "version": settings.app_version,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }


@router.get("/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """就绪检查 - 用于 Kubernetes 等"""
    try:
        # 测试数据库连接
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"服务未就绪: {str(e)}"
        )


@router.get("/live")
async def liveness_check():
    """存活检查 - 用于 Kubernetes 等"""
    return {"status": "alive"}


async def _check_database(db: Session) -> Dict[str, Any]:
    """检查数据库状态"""
    try:
        start = time.time()
        db.execute(text("SELECT 1"))
        latency = (time.time() - start) * 1000
        
        db_size = 0
        db_path = None
        
        if settings.database_url.startswith("sqlite"):
            if settings.database_url.startswith("sqlite:///"):
                db_path = settings.database_url.replace("sqlite:///", "", 1)
            elif settings.database_url.startswith("sqlite://"):
                db_path = settings.database_url.replace("sqlite://", "", 1)
            
            if db_path and os.path.exists(db_path):
                db_size = os.path.getsize(db_path)
        
        return {
            "status": "healthy",
            "latency_ms": round(latency, 2),
            "size_bytes": db_size,
            "type": "sqlite" if settings.database_url.startswith("sqlite") else "other"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def _check_disk_space() -> Dict[str, Any]:
    """检查磁盘空间"""
    try:
        stat = os.statvfs(settings.upload_dir)
        
        total = stat.f_blocks * stat.f_frsize
        free = stat.f_bavail * stat.f_frsize
        used = total - free
        usage_percent = (used / total) * 100
        
        status = "healthy"
        if usage_percent > 90:
            status = "critical"
        elif usage_percent > 80:
            status = "warning"
        
        return {
            "status": status,
            "total_bytes": total,
            "free_bytes": free,
            "used_bytes": used,
            "usage_percent": round(usage_percent, 2)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def _check_memory() -> Dict[str, Any]:
    """检查内存使用"""
    try:
        # 读取 /proc/meminfo（Linux）
        with open('/proc/meminfo', 'r') as f:
            meminfo = f.read()
        
        # 解析内存信息
        mem_total = 0
        mem_available = 0
        
        for line in meminfo.split('\n'):
            if line.startswith('MemTotal:'):
                mem_total = int(line.split()[1]) * 1024
            elif line.startswith('MemAvailable:'):
                mem_available = int(line.split()[1]) * 1024
        
        if mem_total > 0:
            usage_percent = ((mem_total - mem_available) / mem_total) * 100
        else:
            usage_percent = 0
        
        status = "healthy"
        if usage_percent > 90:
            status = "critical"
        elif usage_percent > 80:
            status = "warning"
        
        return {
            "status": status,
            "total_bytes": mem_total,
            "available_bytes": mem_available,
            "usage_percent": round(usage_percent, 2)
        }
    except Exception as e:
        return {
            "status": "unknown",
            "error": str(e)
        }


async def _check_uptime() -> Dict[str, Any]:
    """检查服务运行时间"""
    uptime_seconds = time.time() - START_TIME
    
    return {
        "status": "healthy",
        "uptime_seconds": int(uptime_seconds),
        "uptime_human": _format_duration(uptime_seconds)
    }


async def _check_uploads_dir() -> Dict[str, Any]:
    """检查上传目录"""
    try:
        if not os.path.exists(settings.upload_dir):
            return {
                "status": "unhealthy",
                "error": "上传目录不存在"
            }
        
        # 检查是否可写
        test_file = os.path.join(settings.upload_dir, ".health_check")
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": f"目录不可写: {str(e)}"
            }
        
        # 统计文件数量和大小
        total_size = 0
        file_count = 0
        
        for root, dirs, files in os.walk(settings.upload_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    total_size += os.path.getsize(file_path)
                    file_count += 1
                except:
                    pass
        
        return {
            "status": "healthy",
            "file_count": file_count,
            "total_size_bytes": total_size
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


def _format_duration(seconds: float) -> str:
    """格式化持续时间"""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}天")
    if hours > 0:
        parts.append(f"{hours}小时")
    if minutes > 0:
        parts.append(f"{minutes}分钟")
    if secs > 0 or not parts:
        parts.append(f"{secs}秒")
    
    return "".join(parts)
