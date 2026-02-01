"""数据库会话管理"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
import os

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool

from auto.infrastructure.database.models import Base


class DatabaseManager:
    """数据库管理器
    
    支持 MySQL 和 SQLite 两种数据库。
    """
    
    def __init__(
        self,
        database_url: Optional[str] = None,
        echo: bool = False,
    ):
        """初始化数据库管理器
        
        Args:
            database_url: 数据库连接 URL
                - MySQL: mysql+aiomysql://user:pass@host:port/db
                - SQLite: sqlite+aiosqlite:///path/to/db.sqlite
            echo: 是否打印 SQL 语句
        """
        self._database_url = database_url or self._get_default_url()
        self._echo = echo
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None
    
    def _get_default_url(self) -> str:
        """获取默认数据库 URL"""
        # 从环境变量读取
        url = os.getenv("DATABASE_URL")
        if url:
            return url
        
        # 从配置读取
        try:
            from auto.shared.config import get_config
            config = get_config()
            
            if config.storage.type == "mysql":
                return (
                    f"mysql+aiomysql://{config.storage.mysql_user}:"
                    f"{config.storage.mysql_password}@"
                    f"{config.storage.mysql_host}:{config.storage.mysql_port}/"
                    f"{config.storage.mysql_database}"
                )
            else:
                return f"sqlite+aiosqlite:///{config.storage.sqlite_path}"
        except Exception:
            pass
        
        # 默认使用 SQLite
        from pathlib import Path
        default_path = Path.home() / ".auto" / "data.db"
        default_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite+aiosqlite:///{default_path}"
    
    @property
    def engine(self) -> AsyncEngine:
        """获取数据库引擎"""
        if self._engine is None:
            # 根据数据库类型配置连接池
            if "sqlite" in self._database_url:
                # SQLite 不支持连接池
                self._engine = create_async_engine(
                    self._database_url,
                    echo=self._echo,
                    poolclass=NullPool,
                )
            else:
                # MySQL 使用连接池
                self._engine = create_async_engine(
                    self._database_url,
                    echo=self._echo,
                    pool_size=5,
                    max_overflow=10,
                    pool_pre_ping=True,
                    pool_recycle=3600,
                )
        return self._engine
    
    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """获取会话工厂"""
        if self._session_factory is None:
            self._session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
            )
        return self._session_factory
    
    async def init_db(self) -> None:
        """初始化数据库（创建表）"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def drop_db(self) -> None:
        """删除所有表"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话（上下文管理器）
        
        Usage:
            async with db.session() as session:
                result = await session.execute(query)
        """
        session = self.session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    async def close(self) -> None:
        """关闭数据库连接"""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None


# 全局数据库管理器实例
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """获取全局数据库管理器"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话（用于依赖注入）
    
    Usage with FastAPI:
        @router.get("/users")
        async def get_users(session: AsyncSession = Depends(get_session)):
            ...
    """
    db = get_db_manager()
    async with db.session() as session:
        yield session
