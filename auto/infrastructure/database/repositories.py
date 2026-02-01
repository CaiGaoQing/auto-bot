"""数据库仓库层 (Repository Pattern)"""

from datetime import datetime
from typing import Any, Generic, Optional, TypeVar
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from auto.infrastructure.database.models import (
    Base,
    User,
    Workspace,
    Conversation,
    Message,
    WorkspaceMemory,
    AIProvider,
    TokenUsage,
    MCPServer,
    InstalledSkill,
)

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """基础仓库类"""
    
    def __init__(self, session: AsyncSession, model: type[T]):
        self.session = session
        self.model = model
    
    async def get_by_id(self, id: int) -> Optional[T]:
        """根据 ID 获取"""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> list[T]:
        """获取所有记录"""
        result = await self.session.execute(
            select(self.model).offset(offset).limit(limit)
        )
        return list(result.scalars().all())
    
    async def create(self, **kwargs) -> T:
        """创建记录"""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        return instance
    
    async def update(self, id: int, **kwargs) -> Optional[T]:
        """更新记录"""
        await self.session.execute(
            update(self.model)
            .where(self.model.id == id)
            .values(**kwargs, updated_at=datetime.utcnow())
        )
        return await self.get_by_id(id)
    
    async def delete(self, id: int) -> bool:
        """删除记录"""
        result = await self.session.execute(
            delete(self.model).where(self.model.id == id)
        )
        return result.rowcount > 0
    
    async def count(self) -> int:
        """计数"""
        result = await self.session.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar() or 0


class UserRepository(BaseRepository[User]):
    """用户仓库"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()


class WorkspaceRepository(BaseRepository[Workspace]):
    """工作空间仓库"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Workspace)
    
    async def get_by_user(
        self,
        user_id: int,
        include_deleted: bool = False,
    ) -> list[Workspace]:
        """获取用户的工作空间"""
        query = select(Workspace).where(Workspace.user_id == user_id)
        if not include_deleted:
            query = query.where(Workspace.deleted_at.is_(None))
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_slug(self, user_id: int, slug: str) -> Optional[Workspace]:
        """根据 slug 获取工作空间"""
        result = await self.session.execute(
            select(Workspace).where(
                Workspace.user_id == user_id,
                Workspace.slug == slug,
                Workspace.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()


class ConversationRepository(BaseRepository[Conversation]):
    """会话仓库"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Conversation)
    
    async def get_by_workspace(
        self,
        workspace_id: int,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> list[Conversation]:
        """获取工作空间的会话"""
        query = select(Conversation).where(
            Conversation.workspace_id == workspace_id
        )
        if status:
            query = query.where(Conversation.status == status)
        
        query = query.order_by(Conversation.updated_at.desc()).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update_message_count(
        self,
        conversation_id: int,
        token_count: int,
    ) -> None:
        """更新消息统计"""
        await self.session.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(
                message_count=Conversation.message_count + 1,
                token_count=Conversation.token_count + token_count,
                updated_at=datetime.utcnow(),
            )
        )


class MessageRepository(BaseRepository[Message]):
    """消息仓库"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Message)
    
    async def get_by_conversation(
        self,
        conversation_id: int,
        limit: int = 100,
    ) -> list[Message]:
        """获取会话的消息"""
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_recent(
        self,
        conversation_id: int,
        limit: int = 10,
    ) -> list[Message]:
        """获取最近的消息"""
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        return list(reversed(result.scalars().all()))


class MemoryRepository(BaseRepository[WorkspaceMemory]):
    """记忆仓库"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, WorkspaceMemory)
    
    async def get_by_workspace(
        self,
        workspace_id: int,
        memory_type: Optional[str] = None,
        is_pinned: Optional[bool] = None,
        limit: int = 100,
    ) -> list[WorkspaceMemory]:
        """获取工作空间的记忆"""
        query = select(WorkspaceMemory).where(
            WorkspaceMemory.workspace_id == workspace_id,
            WorkspaceMemory.deleted_at.is_(None),
        )
        
        if memory_type:
            query = query.where(WorkspaceMemory.memory_type == memory_type)
        if is_pinned is not None:
            query = query.where(WorkspaceMemory.is_pinned == is_pinned)
        
        query = query.order_by(
            WorkspaceMemory.is_pinned.desc(),
            WorkspaceMemory.importance.desc(),
        ).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def increment_access(self, memory_id: int) -> None:
        """增加访问计数"""
        await self.session.execute(
            update(WorkspaceMemory)
            .where(WorkspaceMemory.id == memory_id)
            .values(
                access_count=WorkspaceMemory.access_count + 1,
                last_accessed_at=datetime.utcnow(),
            )
        )


class AIProviderRepository(BaseRepository[AIProvider]):
    """AI 提供商仓库"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, AIProvider)
    
    async def get_enabled(self, user_id: Optional[int] = None) -> list[AIProvider]:
        """获取启用的提供商"""
        query = select(AIProvider).where(AIProvider.is_enabled == True)
        if user_id:
            query = query.where(
                (AIProvider.user_id == user_id) | (AIProvider.user_id.is_(None))
            )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_default(self, user_id: Optional[int] = None) -> Optional[AIProvider]:
        """获取默认提供商"""
        query = select(AIProvider).where(
            AIProvider.is_enabled == True,
            AIProvider.is_default == True,
        )
        if user_id:
            query = query.where(
                (AIProvider.user_id == user_id) | (AIProvider.user_id.is_(None))
            )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class TokenUsageRepository(BaseRepository[TokenUsage]):
    """Token 使用统计仓库"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, TokenUsage)
    
    async def get_user_stats(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict:
        """获取用户统计"""
        query = select(
            func.sum(TokenUsage.prompt_tokens).label("prompt_tokens"),
            func.sum(TokenUsage.completion_tokens).label("completion_tokens"),
            func.count().label("request_count"),
        ).where(TokenUsage.user_id == user_id)
        
        if start_date:
            query = query.where(TokenUsage.created_at >= start_date)
        if end_date:
            query = query.where(TokenUsage.created_at <= end_date)
        
        result = await self.session.execute(query)
        row = result.one()
        
        return {
            "prompt_tokens": row.prompt_tokens or 0,
            "completion_tokens": row.completion_tokens or 0,
            "total_tokens": (row.prompt_tokens or 0) + (row.completion_tokens or 0),
            "request_count": row.request_count or 0,
        }
    
    async def record_usage(
        self,
        user_id: int,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        workspace_id: Optional[int] = None,
        conversation_id: Optional[int] = None,
        status: str = "success",
    ) -> TokenUsage:
        """记录 Token 使用"""
        return await self.create(
            user_id=user_id,
            workspace_id=workspace_id,
            conversation_id=conversation_id,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            status=status,
        )


class MCPServerRepository(BaseRepository[MCPServer]):
    """MCP 服务器仓库"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, MCPServer)
    
    async def get_enabled(self, user_id: Optional[int] = None) -> list[MCPServer]:
        """获取启用的 MCP 服务器"""
        query = select(MCPServer).where(MCPServer.is_enabled == True)
        if user_id:
            query = query.where(
                (MCPServer.user_id == user_id) | (MCPServer.user_id.is_(None))
            )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())


class SkillRepository(BaseRepository[InstalledSkill]):
    """技能包仓库"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, InstalledSkill)
    
    async def get_enabled(self, user_id: Optional[int] = None) -> list[InstalledSkill]:
        """获取启用的技能包"""
        query = select(InstalledSkill).where(InstalledSkill.is_enabled == True)
        if user_id:
            query = query.where(
                (InstalledSkill.user_id == user_id) | (InstalledSkill.user_id.is_(None))
            )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_name(
        self,
        name: str,
        user_id: Optional[int] = None,
    ) -> Optional[InstalledSkill]:
        """根据名称获取技能包"""
        query = select(InstalledSkill).where(InstalledSkill.name == name)
        if user_id:
            query = query.where(
                (InstalledSkill.user_id == user_id) | (InstalledSkill.user_id.is_(None))
            )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
