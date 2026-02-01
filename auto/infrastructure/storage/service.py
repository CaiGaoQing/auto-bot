"""存储服务

提供统一的数据存储接口，支持文件存储和数据库存储。
"""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, TypeVar, Generic

logger = logging.getLogger(__name__)

T = TypeVar("T")


class StorageService(ABC, Generic[T]):
    """存储服务基类"""
    
    @abstractmethod
    async def create(self, data: T) -> T:
        """创建记录"""
        pass
    
    @abstractmethod
    async def get(self, id: str) -> Optional[T]:
        """获取记录"""
        pass
    
    @abstractmethod
    async def update(self, id: str, data: dict) -> Optional[T]:
        """更新记录"""
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """删除记录"""
        pass
    
    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters,
    ) -> list[T]:
        """列出记录"""
        pass
    
    @abstractmethod
    async def count(self, **filters) -> int:
        """统计记录数"""
        pass


class FileStorageService(StorageService[dict]):
    """文件存储服务
    
    使用 JSON 文件存储数据，适用于本地/离线模式。
    """
    
    def __init__(self, file_path: Path, id_field: str = "id"):
        self.file_path = file_path
        self.id_field = id_field
        self._data: list[dict] = []
        self._loaded = False
    
    def _ensure_loaded(self) -> None:
        """确保数据已加载"""
        if not self._loaded:
            self._load()
    
    def _load(self) -> None:
        """从文件加载数据"""
        if self.file_path.exists():
            try:
                self._data = json.loads(self.file_path.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning(f"加载数据失败: {e}")
                self._data = []
        else:
            self._data = []
        self._loaded = True
    
    def _save(self) -> None:
        """保存数据到文件"""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_path.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
    
    async def create(self, data: dict) -> dict:
        """创建记录"""
        self._ensure_loaded()
        
        # 设置时间戳
        now = datetime.now().isoformat()
        if "created_at" not in data:
            data["created_at"] = now
        if "updated_at" not in data:
            data["updated_at"] = now
        
        self._data.append(data)
        self._save()
        return data
    
    async def get(self, id: str) -> Optional[dict]:
        """获取记录"""
        self._ensure_loaded()
        
        for item in self._data:
            if item.get(self.id_field) == id:
                return item
        return None
    
    async def get_by(self, **filters) -> Optional[dict]:
        """根据条件获取记录"""
        self._ensure_loaded()
        
        for item in self._data:
            match = True
            for key, value in filters.items():
                if item.get(key) != value:
                    match = False
                    break
            if match:
                return item
        return None
    
    async def update(self, id: str, data: dict) -> Optional[dict]:
        """更新记录"""
        self._ensure_loaded()
        
        for i, item in enumerate(self._data):
            if item.get(self.id_field) == id:
                # 更新字段
                item.update(data)
                item["updated_at"] = datetime.now().isoformat()
                self._data[i] = item
                self._save()
                return item
        return None
    
    async def delete(self, id: str) -> bool:
        """删除记录"""
        self._ensure_loaded()
        
        for i, item in enumerate(self._data):
            if item.get(self.id_field) == id:
                del self._data[i]
                self._save()
                return True
        return False
    
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters,
    ) -> list[dict]:
        """列出记录"""
        self._ensure_loaded()
        
        result = []
        for item in self._data:
            match = True
            for key, value in filters.items():
                if item.get(key) != value:
                    match = False
                    break
            if match:
                result.append(item)
        
        return result[skip:skip + limit]
    
    async def count(self, **filters) -> int:
        """统计记录数"""
        self._ensure_loaded()
        
        if not filters:
            return len(self._data)
        
        count = 0
        for item in self._data:
            match = True
            for key, value in filters.items():
                if item.get(key) != value:
                    match = False
                    break
            if match:
                count += 1
        
        return count
    
    async def find_one(self, **filters) -> Optional[dict]:
        """查找单条记录"""
        return await self.get_by(**filters)
    
    async def find_many(self, **filters) -> list[dict]:
        """查找多条记录"""
        return await self.list(**filters)


class DatabaseStorageService(StorageService[dict]):
    """数据库存储服务
    
    使用 SQLAlchemy 数据库存储，适用于生产环境。
    """
    
    def __init__(self, model_class, session_factory):
        self.model_class = model_class
        self.session_factory = session_factory
    
    async def create(self, data: dict) -> dict:
        """创建记录"""
        async with self.session_factory() as session:
            instance = self.model_class(**data)
            session.add(instance)
            await session.commit()
            await session.refresh(instance)
            return self._to_dict(instance)
    
    async def get(self, id: str) -> Optional[dict]:
        """获取记录"""
        from sqlalchemy import select
        
        async with self.session_factory() as session:
            result = await session.execute(
                select(self.model_class).where(self.model_class.id == id)
            )
            instance = result.scalar_one_or_none()
            if instance:
                return self._to_dict(instance)
        return None
    
    async def update(self, id: str, data: dict) -> Optional[dict]:
        """更新记录"""
        from sqlalchemy import select
        
        async with self.session_factory() as session:
            result = await session.execute(
                select(self.model_class).where(self.model_class.id == id)
            )
            instance = result.scalar_one_or_none()
            if instance:
                for key, value in data.items():
                    if hasattr(instance, key):
                        setattr(instance, key, value)
                instance.updated_at = datetime.now()
                await session.commit()
                await session.refresh(instance)
                return self._to_dict(instance)
        return None
    
    async def delete(self, id: str) -> bool:
        """删除记录"""
        from sqlalchemy import select, delete
        
        async with self.session_factory() as session:
            result = await session.execute(
                delete(self.model_class).where(self.model_class.id == id)
            )
            await session.commit()
            return result.rowcount > 0
    
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters,
    ) -> list[dict]:
        """列出记录"""
        from sqlalchemy import select
        
        async with self.session_factory() as session:
            query = select(self.model_class)
            
            for key, value in filters.items():
                if hasattr(self.model_class, key):
                    query = query.where(getattr(self.model_class, key) == value)
            
            query = query.offset(skip).limit(limit)
            result = await session.execute(query)
            instances = result.scalars().all()
            return [self._to_dict(i) for i in instances]
    
    async def count(self, **filters) -> int:
        """统计记录数"""
        from sqlalchemy import select, func
        
        async with self.session_factory() as session:
            query = select(func.count()).select_from(self.model_class)
            
            for key, value in filters.items():
                if hasattr(self.model_class, key):
                    query = query.where(getattr(self.model_class, key) == value)
            
            result = await session.execute(query)
            return result.scalar() or 0
    
    def _to_dict(self, instance) -> dict:
        """模型转字典"""
        return {c.name: getattr(instance, c.name) for c in instance.__table__.columns}


# 存储服务缓存
_storage_services: dict[str, StorageService] = {}


def get_storage_service(
    name: str,
    use_database: bool = False,
) -> StorageService:
    """获取存储服务
    
    Args:
        name: 服务名称 (workspaces, memories, etc.)
        use_database: 是否使用数据库存储
    
    Returns:
        StorageService: 存储服务实例
    """
    if name in _storage_services:
        return _storage_services[name]
    
    from auto.shared.config import DEFAULT_CONFIG_DIR
    
    # 目前默认使用文件存储
    file_path = DEFAULT_CONFIG_DIR / f"{name}.json"
    service = FileStorageService(file_path)
    
    _storage_services[name] = service
    return service
