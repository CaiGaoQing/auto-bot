"""速率限制中间件"""

import asyncio
import time
from collections import defaultdict
from typing import Optional

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS


class RateLimiter:
    """速率限制器
    
    使用令牌桶算法实现。
    """
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
    ):
        self.rpm_limit = requests_per_minute
        self.rph_limit = requests_per_hour
        
        # 存储每个 key 的请求时间戳
        self._minute_requests: dict[str, list[float]] = defaultdict(list)
        self._hour_requests: dict[str, list[float]] = defaultdict(list)
        
        # 清理锁
        self._lock = asyncio.Lock()
    
    async def check(self, key: str, limit_override: Optional[int] = None) -> bool:
        """检查是否允许请求
        
        Args:
            key: 限制键 (通常是 API Key 或 IP)
            limit_override: 覆盖默认限制
        
        Returns:
            bool: 是否允许
        
        Raises:
            HTTPException: 超过限制时抛出
        """
        now = time.time()
        rpm_limit = limit_override or self.rpm_limit
        
        async with self._lock:
            # 清理过期记录
            self._cleanup(key, now)
            
            # 检查每分钟限制
            minute_count = len(self._minute_requests[key])
            if minute_count >= rpm_limit:
                raise HTTPException(
                    status_code=HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"请求过于频繁，每分钟最多 {rpm_limit} 次",
                    headers={"Retry-After": "60"},
                )
            
            # 检查每小时限制
            hour_count = len(self._hour_requests[key])
            if hour_count >= self.rph_limit:
                raise HTTPException(
                    status_code=HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"请求过于频繁，每小时最多 {self.rph_limit} 次",
                    headers={"Retry-After": "3600"},
                )
            
            # 记录请求
            self._minute_requests[key].append(now)
            self._hour_requests[key].append(now)
        
        return True
    
    def _cleanup(self, key: str, now: float) -> None:
        """清理过期记录"""
        # 清理分钟记录 (保留最近60秒)
        minute_cutoff = now - 60
        self._minute_requests[key] = [
            t for t in self._minute_requests[key]
            if t > minute_cutoff
        ]
        
        # 清理小时记录 (保留最近3600秒)
        hour_cutoff = now - 3600
        self._hour_requests[key] = [
            t for t in self._hour_requests[key]
            if t > hour_cutoff
        ]
    
    def get_remaining(self, key: str) -> dict:
        """获取剩余请求次数"""
        now = time.time()
        
        # 清理过期记录
        self._cleanup(key, now)
        
        return {
            "minute_remaining": max(0, self.rpm_limit - len(self._minute_requests[key])),
            "hour_remaining": max(0, self.rph_limit - len(self._hour_requests[key])),
            "reset_minute": 60,
            "reset_hour": 3600,
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """速率限制中间件"""
    
    def __init__(
        self,
        app,
        limiter: Optional[RateLimiter] = None,
        exclude_paths: Optional[list[str]] = None,
    ):
        super().__init__(app)
        self.limiter = limiter or RateLimiter()
        self.exclude_paths = exclude_paths or ["/health", "/ready", "/live"]
    
    async def dispatch(self, request: Request, call_next):
        # 排除路径
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # 获取限制键
        key = self._get_key(request)
        
        # 获取自定义限制
        limit_override = None
        if hasattr(request.state, "api_key_info"):
            key_info = request.state.api_key_info
            limit_override = key_info.get("rate_limit")
        
        # 检查限制
        await self.limiter.check(key, limit_override)
        
        # 添加响应头
        response = await call_next(request)
        
        remaining = self.limiter.get_remaining(key)
        response.headers["X-RateLimit-Limit"] = str(self.limiter.rpm_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining["minute_remaining"])
        response.headers["X-RateLimit-Reset"] = str(remaining["reset_minute"])
        
        return response
    
    def _get_key(self, request: Request) -> str:
        """获取限制键"""
        # 优先使用 API Key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"apikey:{api_key[:20]}"
        
        # 使用 IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        
        return f"ip:{ip}"


# 全局限制器实例
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """获取全局速率限制器"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
