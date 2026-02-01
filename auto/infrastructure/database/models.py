"""数据库模型 (SQLAlchemy)"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    BigInteger,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True)
    password_hash = Column(String(255))
    display_name = Column(String(100))
    status = Column(Enum("active", "inactive", "suspended"), default="active")
    settings = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    
    # 关系
    workspaces = relationship("Workspace", back_populates="user")
    api_keys = relationship("APIKey", back_populates="user")


class Workspace(Base):
    """工作空间表"""
    __tablename__ = "workspaces"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False)
    description = Column(Text)
    role = Column(String(50), default="general")
    local_path = Column(String(500))
    settings = Column(JSON)
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    
    # 关系
    user = relationship("User", back_populates="workspaces")
    conversations = relationship("Conversation", back_populates="workspace")
    memories = relationship("WorkspaceMemory", back_populates="workspace")


class Conversation(Base):
    """会话表"""
    __tablename__ = "conversations"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    workspace_id = Column(BigInteger, ForeignKey("workspaces.id"), nullable=False)
    title = Column(String(200))
    summary = Column(Text)
    role = Column(String(50))
    model = Column(String(100))
    status = Column(Enum("active", "archived", "deleted"), default="active")
    message_count = Column(Integer, default=0)
    token_count = Column(Integer, default=0)
    metadata = Column(JSON)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    workspace = relationship("Workspace", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    """消息表"""
    __tablename__ = "messages"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id = Column(BigInteger, ForeignKey("conversations.id"), nullable=False)
    role = Column(Enum("system", "user", "assistant", "tool"), nullable=False)
    content = Column(Text, nullable=False)
    content_type = Column(Enum("text", "image", "file", "mixed"), default="text")
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    tool_calls = Column(JSON)
    tool_call_id = Column(String(100))
    attachments = Column(JSON)
    model = Column(String(100))
    finish_reason = Column(String(50))
    latency_ms = Column(Integer)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    conversation = relationship("Conversation", back_populates="messages")


class WorkspaceMemory(Base):
    """工作空间记忆表"""
    __tablename__ = "workspace_memories"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    workspace_id = Column(BigInteger, ForeignKey("workspaces.id"), nullable=False)
    content = Column(Text, nullable=False)
    memory_type = Column(Enum("preference", "rule", "knowledge", "context", "summary"), nullable=False)
    source_type = Column(Enum("user", "auto", "conversation"), default="user")
    source_id = Column(BigInteger)
    importance = Column(Integer, default=50)
    is_pinned = Column(Boolean, default=False)
    embedding_id = Column(String(100))
    access_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime)
    expires_at = Column(DateTime)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime)
    
    # 关系
    workspace = relationship("Workspace", back_populates="memories")


class AIProvider(Base):
    """AI 提供商表"""
    __tablename__ = "ai_providers"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"))
    name = Column(String(100), nullable=False)
    display_name = Column(String(100))
    provider_type = Column(Enum("official", "proxy", "custom"), nullable=False)
    base_url = Column(String(500), nullable=False)
    api_key_encrypted = Column(String(512))
    proxy_config = Column(JSON)
    load_balance_config = Column(JSON)
    failover_config = Column(JSON)
    available_models = Column(JSON)
    health_status = Column(Enum("healthy", "degraded", "unhealthy", "unknown"), default="unknown")
    last_health_check = Column(DateTime)
    health_check_config = Column(JSON)
    is_default = Column(Boolean, default=False)
    is_enabled = Column(Boolean, default=True)
    priority = Column(Integer, default=100)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class APIKey(Base):
    """API Key 表"""
    __tablename__ = "api_keys"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    key_prefix = Column(String(10), nullable=False)
    key_hash = Column(String(64), nullable=False, unique=True)
    permissions = Column(JSON)
    allowed_ips = Column(JSON)
    rate_limit = Column(Integer, default=1000)
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime)
    usage_count = Column(BigInteger, default=0)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="api_keys")


class TokenUsage(Base):
    """Token 使用统计表"""
    __tablename__ = "token_usage"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    workspace_id = Column(BigInteger, ForeignKey("workspaces.id"))
    conversation_id = Column(BigInteger)
    message_id = Column(BigInteger)
    provider_id = Column(BigInteger)
    model = Column(String(100), nullable=False)
    prompt_tokens = Column(Integer, nullable=False, default=0)
    completion_tokens = Column(Integer, nullable=False, default=0)
    request_type = Column(Enum("chat", "completion", "embedding", "image"), default="chat")
    latency_ms = Column(Integer)
    status = Column(Enum("success", "error", "timeout"), default="success")
    created_at = Column(DateTime, default=datetime.utcnow)


class MCPServer(Base):
    """MCP 服务器配置表"""
    __tablename__ = "mcp_servers"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"))
    name = Column(String(100), nullable=False)
    display_name = Column(String(100))
    description = Column(Text)
    transport = Column(Enum("stdio", "sse"), nullable=False)
    command = Column(String(500))
    args = Column(JSON)
    url = Column(String(500))
    env = Column(JSON)
    source = Column(Enum("local", "npm", "custom"), default="local")
    package_name = Column(String(200))
    package_version = Column(String(50))
    tools = Column(JSON)
    resources = Column(JSON)
    prompts = Column(JSON)
    is_enabled = Column(Boolean, default=True)
    connection_status = Column(Enum("connected", "disconnected", "error", "unknown"), default="unknown")
    last_connected_at = Column(DateTime)
    last_error = Column(Text)
    call_count = Column(BigInteger, default=0)
    error_count = Column(BigInteger, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class InstalledSkill(Base):
    """已安装技能包表"""
    __tablename__ = "installed_skills"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"))
    name = Column(String(100), nullable=False)
    display_name = Column(String(100))
    version = Column(String(50), nullable=False)
    description = Column(Text)
    source = Column(Enum("builtin", "official", "github", "npm", "pypi", "url", "local"), nullable=False)
    source_url = Column(String(500))
    install_path = Column(String(500))
    config = Column(JSON)
    permissions = Column(JSON)
    mcp_dependencies = Column(JSON)
    is_enabled = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    use_count = Column(BigInteger, default=0)
    last_used_at = Column(DateTime)
    latest_version = Column(String(50))
    update_available = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
