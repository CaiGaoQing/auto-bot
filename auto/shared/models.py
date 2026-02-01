"""共享数据模型"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """消息角色"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class Message(BaseModel):
    """对话消息"""
    role: MessageRole
    content: str
    name: Optional[str] = None
    tool_calls: Optional[list[dict]] = None
    tool_call_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class Conversation(BaseModel):
    """对话"""
    id: str
    workspace_id: str
    title: Optional[str] = None
    messages: list[Message] = Field(default_factory=list)
    role: str = "general"
    model: str = "gpt-4o"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Workspace(BaseModel):
    """工作空间"""
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    role: str = "general"
    local_path: Optional[str] = None
    settings: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Memory(BaseModel):
    """记忆"""
    id: str
    workspace_id: str
    content: str
    memory_type: str = "preference"  # preference, rule, knowledge, context, summary
    source_type: str = "user"  # user, auto, conversation
    importance: int = 50
    is_pinned: bool = False
    access_count: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class TokenUsage(BaseModel):
    """Token 使用统计"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    @property
    def calculated_total(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class ChatRequest(BaseModel):
    """聊天请求"""
    messages: list[Message]
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream: bool = False
    tools: Optional[list[dict]] = None
    tool_choice: Optional[str] = None


class ChatResponse(BaseModel):
    """聊天响应"""
    id: str
    message: Message
    model: str
    usage: TokenUsage
    finish_reason: str = "stop"
    created_at: datetime = Field(default_factory=datetime.now)


class SkillInfo(BaseModel):
    """技能信息"""
    name: str
    display_name: str
    version: str
    description: str
    category: str = "general"
    tools: list[str] = Field(default_factory=list)
    is_installed: bool = False
    is_enabled: bool = True


class MCPServerInfo(BaseModel):
    """MCP 服务器信息"""
    name: str
    display_name: Optional[str] = None
    transport: str  # stdio, sse
    command: Optional[str] = None
    args: list[str] = Field(default_factory=list)
    url: Optional[str] = None
    is_enabled: bool = True
    is_connected: bool = False
    tools: list[str] = Field(default_factory=list)
