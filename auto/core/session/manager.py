"""
会话管理器

实现多会话隔离和管理
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any, Callable
import logging

logger = logging.getLogger(__name__)


class SessionStatus(str, Enum):
    """会话状态"""
    ACTIVE = "active"
    IDLE = "idle"
    PROCESSING = "processing"
    PAUSED = "paused"
    CLOSED = "closed"


@dataclass
class Message:
    """会话消息"""
    id: str
    role: str  # user, assistant, system
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class Session:
    """
    会话
    
    代表一个独立的对话上下文
    """
    id: str
    channel_type: str  # telegram, discord, webchat, cli
    channel_id: str    # 群组/频道/用户 ID
    
    # 状态
    status: SessionStatus = SessionStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # 消息历史
    messages: List[Message] = field(default_factory=list)
    
    # 配置
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    thinking_level: str = "medium"  # off, low, medium, high
    
    # 上下文
    workspace_id: Optional[str] = None
    role_id: Optional[str] = None
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Token 统计
    total_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    
    @property
    def message_count(self) -> int:
        return len(self.messages)
    
    def add_message(self, role: str, content: str, metadata: Optional[dict] = None) -> Message:
        """添加消息"""
        message = Message(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            metadata=metadata or {},
        )
        self.messages.append(message)
        self.updated_at = datetime.now()
        return message
    
    def get_history(self, limit: Optional[int] = None) -> List[Message]:
        """获取历史消息"""
        if limit:
            return self.messages[-limit:]
        return self.messages
    
    def get_context_messages(self, max_messages: int = 50) -> List[dict]:
        """
        获取用于 AI 上下文的消息
        
        Returns:
            消息列表，格式为 [{"role": "user", "content": "..."}]
        """
        messages = self.get_history(max_messages)
        return [{"role": m.role, "content": m.content} for m in messages if m.role != "system"]
    
    def clear(self):
        """清空消息"""
        self.messages = []
        self.updated_at = datetime.now()
        self.total_tokens = 0
        self.input_tokens = 0
        self.output_tokens = 0
    
    def compact(self, summary: str):
        """
        压缩会话
        
        将历史消息压缩为摘要
        """
        # 保留系统消息
        system_messages = [m for m in self.messages if m.role == "system"]
        
        # 创建摘要消息
        summary_message = Message(
            id=str(uuid.uuid4()),
            role="system",
            content=f"[会话摘要]\n{summary}",
            metadata={"compacted": True, "original_count": len(self.messages)},
        )
        
        # 重置消息
        self.messages = system_messages + [summary_message]
        self.updated_at = datetime.now()
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "channel_type": self.channel_type,
            "channel_id": self.channel_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "message_count": self.message_count,
            "model": self.model,
            "thinking_level": self.thinking_level,
            "workspace_id": self.workspace_id,
            "role_id": self.role_id,
            "total_tokens": self.total_tokens,
            "metadata": self.metadata,
        }


class SessionManager:
    """
    会话管理器
    
    功能:
    - 创建和管理会话
    - 会话隔离
    - 会话持久化
    - Agent 间通信
    """
    
    def __init__(self):
        self._sessions: Dict[str, Session] = {}
        self._channel_sessions: Dict[str, str] = {}  # channel_key -> session_id
        self._listeners: List[Callable] = []
    
    def create_session(
        self,
        channel_type: str,
        channel_id: str,
        workspace_id: Optional[str] = None,
        role_id: Optional[str] = None,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> Session:
        """
        创建新会话
        
        Args:
            channel_type: 渠道类型
            channel_id: 渠道 ID
            workspace_id: 工作空间 ID
            role_id: 角色 ID
            model: 模型名称
            system_prompt: 系统提示词
        
        Returns:
            新创建的会话
        """
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        
        session = Session(
            id=session_id,
            channel_type=channel_type,
            channel_id=channel_id,
            workspace_id=workspace_id,
            role_id=role_id,
            model=model,
            system_prompt=system_prompt,
        )
        
        # 添加系统提示词
        if system_prompt:
            session.add_message("system", system_prompt)
        
        self._sessions[session_id] = session
        
        # 建立渠道映射
        channel_key = f"{channel_type}:{channel_id}"
        self._channel_sessions[channel_key] = session_id
        
        logger.info(f"创建会话: {session_id} ({channel_type}:{channel_id})")
        self._notify("session_created", session)
        
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        return self._sessions.get(session_id)
    
    def get_session_by_channel(
        self,
        channel_type: str,
        channel_id: str,
        create_if_missing: bool = True,
        **create_kwargs
    ) -> Optional[Session]:
        """
        根据渠道获取会话
        
        如果会话不存在且 create_if_missing=True，则创建新会话
        """
        channel_key = f"{channel_type}:{channel_id}"
        session_id = self._channel_sessions.get(channel_key)
        
        if session_id:
            session = self._sessions.get(session_id)
            if session:
                return session
        
        if create_if_missing:
            return self.create_session(channel_type, channel_id, **create_kwargs)
        
        return None
    
    def list_sessions(
        self,
        channel_type: Optional[str] = None,
        status: Optional[SessionStatus] = None,
    ) -> List[Session]:
        """
        列出会话
        
        Args:
            channel_type: 按渠道类型过滤
            status: 按状态过滤
        
        Returns:
            会话列表
        """
        sessions = list(self._sessions.values())
        
        if channel_type:
            sessions = [s for s in sessions if s.channel_type == channel_type]
        
        if status:
            sessions = [s for s in sessions if s.status == status]
        
        return sessions
    
    def close_session(self, session_id: str):
        """关闭会话"""
        session = self._sessions.get(session_id)
        if session:
            session.status = SessionStatus.CLOSED
            session.updated_at = datetime.now()
            self._notify("session_closed", session)
            logger.info(f"关闭会话: {session_id}")
    
    def delete_session(self, session_id: str):
        """删除会话"""
        if session_id in self._sessions:
            session = self._sessions.pop(session_id)
            
            # 移除渠道映射
            channel_key = f"{session.channel_type}:{session.channel_id}"
            if channel_key in self._channel_sessions:
                del self._channel_sessions[channel_key]
            
            self._notify("session_deleted", session)
            logger.info(f"删除会话: {session_id}")
    
    def reset_session(self, session_id: str) -> Optional[Session]:
        """重置会话（清空消息）"""
        session = self._sessions.get(session_id)
        if session:
            # 保留系统提示词
            system_prompt = session.system_prompt
            session.clear()
            if system_prompt:
                session.add_message("system", system_prompt)
            self._notify("session_reset", session)
            logger.info(f"重置会话: {session_id}")
        return session
    
    async def send_to_session(
        self,
        target_session_id: str,
        message: str,
        sender_session_id: Optional[str] = None,
        reply_back: bool = False,
    ) -> Optional[str]:
        """
        发送消息到另一个会话
        
        用于 Agent 间通信
        
        Args:
            target_session_id: 目标会话 ID
            message: 消息内容
            sender_session_id: 发送者会话 ID
            reply_back: 是否需要回复
        
        Returns:
            如果 reply_back=True，返回目标会话的回复
        """
        target_session = self._sessions.get(target_session_id)
        if not target_session:
            logger.warning(f"目标会话不存在: {target_session_id}")
            return None
        
        # 添加消息到目标会话
        metadata = {}
        if sender_session_id:
            metadata["from_session"] = sender_session_id
        
        target_session.add_message("user", message, metadata)
        
        self._notify("message_forwarded", {
            "from": sender_session_id,
            "to": target_session_id,
            "message": message,
        })
        
        # 如果需要回复，等待处理
        if reply_back:
            # 这里需要集成 AI 处理逻辑
            # 简化处理：返回确认消息
            return f"[消息已转发到会话 {target_session_id}]"
        
        return None
    
    def get_session_history(
        self,
        session_id: str,
        limit: Optional[int] = None,
    ) -> List[dict]:
        """获取会话历史"""
        session = self._sessions.get(session_id)
        if not session:
            return []
        return [m.to_dict() for m in session.get_history(limit)]
    
    def update_session_metadata(
        self,
        session_id: str,
        **kwargs
    ) -> Optional[Session]:
        """更新会话元数据"""
        session = self._sessions.get(session_id)
        if not session:
            return None
        
        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)
            else:
                session.metadata[key] = value
        
        session.updated_at = datetime.now()
        return session
    
    def add_listener(self, callback: Callable):
        """添加事件监听器"""
        self._listeners.append(callback)
    
    def _notify(self, event: str, data: Any):
        """通知监听器"""
        for listener in self._listeners:
            try:
                listener(event, data)
            except Exception as e:
                logger.error(f"监听器错误: {e}")
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        sessions = list(self._sessions.values())
        
        return {
            "total_sessions": len(sessions),
            "active_sessions": sum(1 for s in sessions if s.status == SessionStatus.ACTIVE),
            "processing_sessions": sum(1 for s in sessions if s.status == SessionStatus.PROCESSING),
            "total_messages": sum(s.message_count for s in sessions),
            "total_tokens": sum(s.total_tokens for s in sessions),
            "by_channel": {
                channel: sum(1 for s in sessions if s.channel_type == channel)
                for channel in set(s.channel_type for s in sessions)
            }
        }


# 全局实例
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """获取全局会话管理器"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
