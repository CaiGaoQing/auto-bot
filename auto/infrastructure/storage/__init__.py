"""存储服务模块"""

from auto.infrastructure.storage.service import (
    StorageService,
    FileStorageService,
    get_storage_service,
)

__all__ = [
    "StorageService",
    "FileStorageService",
    "get_storage_service",
]
