"""
安全配置 API
管理IP白名单、黑名单、速率限制等安全配置
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.models.user import User
from app.api.auth import get_current_active_user

router = APIRouter(prefix="/api/admin", tags=["安全配置"])

class RateLimitConfig(BaseModel):
    apiLimit: int = 60
    pageLimit: int = 200

class CrawlerDetectionConfig(BaseModel):
    enabled: bool = True
    blockedAgents: List[str] = []

class SecurityConfig(BaseModel):
    whitelist: List[str] = []
    blacklist: List[str] = []
    rateLimit: Optional[RateLimitConfig] = None
    crawlerDetection: Optional[CrawlerDetectionConfig] = None

_security_config = SecurityConfig(
    whitelist=['111.18.157.89', '127.0.0.1', '::1'],
    blacklist=[],
    rateLimit=RateLimitConfig(),
    crawlerDetection=CrawlerDetectionConfig(
        enabled=True,
        blockedAgents=['bot', 'crawler', 'spider', 'scraper', 'python-requests', 'selenium', 'phantomjs']
    )
)

_stats = {
    "totalRequests": 0,
    "blockedRequests": 0,
    "activeIps": 0
}

@router.get("/security-config")
def get_security_config(current_user: User = Depends(get_current_active_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return {
        "whitelist": _security_config.whitelist,
        "blacklist": _security_config.blacklist,
        "rateLimit": _security_config.rateLimit.model_dump() if _security_config.rateLimit else None,
        "crawlerDetection": _security_config.crawlerDetection.model_dump() if _security_config.crawlerDetection else None,
        "stats": _stats
    }

@router.post("/security-config")
def update_security_config(config: SecurityConfig, current_user: User = Depends(get_current_active_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    global _security_config
    _security_config = config
    return {"message": "配置已更新"}

def get_whitelist() -> List[str]:
    return _security_config.whitelist

def get_blacklist() -> List[str]:
    return _security_config.blacklist

def is_ip_whitelisted(ip: str) -> bool:
    return ip in _security_config.whitelist

def is_ip_blacklisted(ip: str) -> bool:
    return ip in _security_config.blacklist

def get_rate_limits() -> tuple:
    if _security_config.rateLimit:
        return _security_config.rateLimit.apiLimit, _security_config.rateLimit.pageLimit
    return 60, 200

def increment_request_count(blocked: bool = False):
    global _stats
    _stats["totalRequests"] += 1
    if blocked:
        _stats["blockedRequests"] += 1
