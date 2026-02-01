"""API Key 认证中间件"""

import hashlib
import secrets
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

# API Key Header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_api_key_header(api_key: Optional[str] = Security(api_key_header)) -> Optional[str]:
    """获取 API Key Header"""
    return api_key


class APIKeyAuth:
    """API Key 认证器
    
    支持:
    - API Key 验证
    - 权限检查
    - 速率限制
    - 审计日志
    """
    
    def __init__(self, required: bool = True):
        """初始化认证器
        
        Args:
            required: 是否必须提供 API Key
        """
        self.required = required
    
    async def __call__(
        self,
        api_key: Optional[str] = Security(api_key_header),
    ) -> Optional[dict]:
        """验证 API Key
        
        Returns:
            dict: API Key 信息，包含 user_id, permissions 等
        """
        if not api_key:
            if self.required:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED,
                    detail="需要提供 API Key",
                    headers={"WWW-Authenticate": "ApiKey"},
                )
            return None
        
        # 验证 API Key
        key_info = await self._validate_api_key(api_key)
        
        if not key_info:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="无效的 API Key",
            )
        
        if not key_info.get("is_active", False):
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail="API Key 已禁用",
            )
        
        # 检查是否过期
        expires_at = key_info.get("expires_at")
        if expires_at and datetime.fromisoformat(expires_at) < datetime.utcnow():
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail="API Key 已过期",
            )
        
        # 记录使用
        await self._record_usage(key_info)
        
        return key_info
    
    async def _validate_api_key(self, api_key: str) -> Optional[dict]:
        """验证 API Key
        
        API Key 格式: auto_xxxxxxxx (前缀_随机字符串)
        存储时使用 SHA-256 哈希
        """
        # 检查格式
        if not api_key.startswith("auto_"):
            return None
        
        # 计算哈希
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # 从数据库查询
        try:
            from auto.infrastructure.database.session import get_db_manager
            from sqlalchemy import select
            from auto.infrastructure.database.models import APIKey
            
            db = get_db_manager()
            async with db.session() as session:
                result = await session.execute(
                    select(APIKey).where(APIKey.key_hash == key_hash)
                )
                api_key_record = result.scalar_one_or_none()
                
                if not api_key_record:
                    return None
                
                return {
                    "id": api_key_record.id,
                    "user_id": api_key_record.user_id,
                    "name": api_key_record.name,
                    "permissions": api_key_record.permissions or {},
                    "rate_limit": api_key_record.rate_limit,
                    "is_active": api_key_record.is_active,
                    "expires_at": api_key_record.expires_at.isoformat() if api_key_record.expires_at else None,
                }
        except Exception:
            # 数据库未初始化时，使用本地配置
            return await self._validate_from_config(api_key)
    
    async def _validate_from_config(self, api_key: str) -> Optional[dict]:
        """从配置文件验证 API Key (本地模式)"""
        try:
            from auto.shared.config import get_config_manager
            
            config = get_config_manager()
            stored_keys = config.get("api_keys", [])
            
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            for stored in stored_keys:
                if stored.get("key_hash") == key_hash:
                    return {
                        "id": stored.get("id", 0),
                        "user_id": stored.get("user_id", 0),
                        "name": stored.get("name", ""),
                        "permissions": stored.get("permissions", {}),
                        "rate_limit": stored.get("rate_limit", 1000),
                        "is_active": stored.get("is_active", True),
                        "expires_at": stored.get("expires_at"),
                    }
            
            return None
        except Exception:
            return None
    
    async def _record_usage(self, key_info: dict) -> None:
        """记录 API Key 使用"""
        try:
            from auto.infrastructure.database.session import get_db_manager
            from sqlalchemy import update
            from auto.infrastructure.database.models import APIKey
            
            db = get_db_manager()
            async with db.session() as session:
                await session.execute(
                    update(APIKey)
                    .where(APIKey.id == key_info["id"])
                    .values(
                        last_used_at=datetime.utcnow(),
                        usage_count=APIKey.usage_count + 1,
                    )
                )
        except Exception:
            pass  # 忽略记录失败


class PermissionChecker:
    """权限检查器"""
    
    def __init__(self, required_permissions: list[str]):
        self.required_permissions = required_permissions
    
    async def __call__(
        self,
        key_info: Optional[dict] = Depends(APIKeyAuth(required=True)),
    ) -> dict:
        """检查权限"""
        if not key_info:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="需要认证",
            )
        
        user_permissions = key_info.get("permissions", {})
        
        # 检查是否有 admin 权限
        if user_permissions.get("admin"):
            return key_info
        
        # 检查具体权限
        for perm in self.required_permissions:
            if not user_permissions.get(perm):
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN,
                    detail=f"缺少权限: {perm}",
                )
        
        return key_info


# 辅助函数
def generate_api_key(prefix: str = "auto") -> tuple[str, str]:
    """生成 API Key
    
    Returns:
        tuple[str, str]: (API Key, Key Hash)
    """
    random_part = secrets.token_urlsafe(32)
    api_key = f"{prefix}_{random_part}"
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    return api_key, key_hash


def get_key_prefix(api_key: str) -> str:
    """获取 API Key 前缀 (用于显示)"""
    if "_" in api_key:
        parts = api_key.split("_")
        if len(parts) >= 2:
            return f"{parts[0]}_{parts[1][:8]}..."
    return api_key[:12] + "..."
