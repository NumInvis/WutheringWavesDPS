"""
速率限制和登录锁定机制
"""
import time
from functools import wraps
from typing import Dict, Optional, Callable, Set
from fastapi import Request, HTTPException, status
from collections import defaultdict

IP_WHITELIST: Set[str] = {
    '111.18.157.89',
    '127.0.0.1',
    '::1'
}


class LoginAttemptTracker:
    """登录尝试跟踪器"""
    
    def __init__(self):
        self.attempts: Dict[str, Dict[str, tuple]] = defaultdict(dict)
        self.locked_ips: Dict[str, float] = {}
        
    def is_locked(self, ip: str) -> bool:
        if ip in IP_WHITELIST:
            return False
        if ip in self.locked_ips:
            if time.time() < self.locked_ips[ip]:
                return True
            else:
                del self.locked_ips[ip]
                if ip in self.attempts:
                    del self.attempts[ip]
        return False
    
    def record_attempt(self, ip: str, username: str, success: bool = False):
        """记录登录尝试"""
        if ip in IP_WHITELIST:
            return
        if success:
            if ip in self.attempts:
                del self.attempts[ip]
            return
        
        # 记录失败尝试
        current_time = time.time()
        if username not in self.attempts[ip]:
            self.attempts[ip][username] = (1, current_time)
        else:
            count, first_time = self.attempts[ip][username]
            # 检查是否在时间窗口内（30分钟）
            if current_time - first_time > 1800:  # 30分钟
                # 重置计数
                self.attempts[ip][username] = (1, current_time)
            else:
                # 增加计数
                self.attempts[ip][username] = (count + 1, first_time)
                
                # 检查是否需要锁定
                total_attempts = sum(c for c, _ in self.attempts[ip].values())
                if total_attempts >= 5:  # 5次失败尝试后锁定
                    # 锁定30分钟
                    self.locked_ips[ip] = current_time + 1800
                    
    def get_remaining_lock_time(self, ip: str) -> int:
        """获取剩余锁定时间（秒）"""
        if ip in self.locked_ips:
            remaining = int(self.locked_ips[ip] - time.time())
            return max(0, remaining)
        return 0


# 全局登录尝试跟踪器
login_tracker = LoginAttemptTracker()


class RateLimiter:
    """API 速率限制器"""
    
    def __init__(self):
        # 记录请求时间 {ip: [timestamp1, timestamp2, ...]}
        self.requests: Dict[str, list] = defaultdict(list)
        
    def is_allowed(self, ip: str, max_requests: int = 100, window: int = 60) -> bool:
        """
        检查是否允许请求
        :param ip: 客户端IP
        :param max_requests: 时间窗口内最大请求数
        :param window: 时间窗口（秒）
        :return: 是否允许
        """
        current_time = time.time()
        
        # 清理过期的请求记录
        self.requests[ip] = [
            ts for ts in self.requests[ip] 
            if current_time - ts < window
        ]
        
        # 检查是否超过限制
        if len(self.requests[ip]) >= max_requests:
            return False
        
        # 记录本次请求
        self.requests[ip].append(current_time)
        return True
    
    def get_remaining(self, ip: str, max_requests: int = 100, window: int = 60) -> int:
        """获取剩余可用请求数"""
        current_time = time.time()
        valid_requests = [
            ts for ts in self.requests[ip] 
            if current_time - ts < window
        ]
        return max(0, max_requests - len(valid_requests))


# 全局速率限制器
rate_limiter = RateLimiter()


def check_login_lock(ip: str):
    """检查登录锁定装饰器辅助函数"""
    if login_tracker.is_locked(ip):
        remaining = login_tracker.get_remaining_lock_time(ip)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"登录尝试次数过多，请 {remaining // 60} 分钟后再试"
        )


def rate_limit(max_requests: int = 100, window: int = 60):
    """
    速率限制装饰器
    :param max_requests: 时间窗口内最大请求数
    :param window: 时间窗口（秒）
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从参数中找到 request 对象
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                for v in kwargs.values():
                    if isinstance(v, Request):
                        request = v
                        break
            
            if request:
                ip = request.client.host if request.client else "unknown"
                
                if not rate_limiter.is_allowed(ip, max_requests, window):
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="请求过于频繁，请稍后再试"
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def login_rate_limit(max_attempts: int = 5, lock_duration: int = 1800):
    """
    登录速率限制装饰器
    :param max_attempts: 最大尝试次数
    :param lock_duration: 锁定时间（秒）
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从参数中找到 request 对象
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                for v in kwargs.values():
                    if isinstance(v, Request):
                        request = v
                        break
            
            if request:
                ip = request.client.host if request.client else "unknown"
                
                # 检查是否被锁定
                if login_tracker.is_locked(ip):
                    remaining = login_tracker.get_remaining_lock_time(ip)
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"登录尝试次数过多，请 {remaining // 60} 分钟后再试"
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
