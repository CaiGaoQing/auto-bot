"""
渠道基类定义

借鉴 OpenClaw 的渠道抽象设计，统一消息格式
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional, List
import asyncio


class ChannelType(str, Enum):
    """渠道类型"""
    TELEGRAM = "telegram"
    DISCORD = "discord"
    WECHAT_WORK = "wechat_work"
    SLACK = "slack"
    FEISHU = "feishu"
    WEBCHAT = "webchat"
    CLI = "cli"


class MessageType(str, Enum):
    """消息类型"""
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    AUDIO = "audio"
    VIDEO = "video"
    LOCATION = "location"
    COMMAND = "command"


@dataclass
class ChannelUser:
    """渠道用户"""
    id: str
    username: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_bot: bool = False
    raw_data: dict = field(default_factory=dict)


@dataclass
class ChannelMessage:
    """统一消息格式"""
    id: str
    channel_type: ChannelType
    channel_id: str  # 群组/频道 ID
    sender: ChannelUser
    content: str
    message_type: MessageType = MessageType.TEXT
    
    # 可选字段
    reply_to_id: Optional[str] = None
    attachments: List[dict] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    # 原始数据，用于特定渠道功能
    raw_data: dict = field(default_factory=dict)
    
    # 会话上下文
    session_id: Optional[str] = None
    workspace_id: Optional[str] = None


@dataclass
class ChannelResponse:
    """渠道回复"""
    content: str
    message_type: MessageType = MessageType.TEXT
    attachments: List[dict] = field(default_factory=list)
    reply_to_id: Optional[str] = None
    
    # 渠道特定选项
    parse_mode: Optional[str] = None  # Telegram: HTML/Markdown
    embed: Optional[dict] = None  # Discord embed
    buttons: Optional[List[dict]] = None  # 按钮


class BaseChannel(ABC):
    """
    渠道基类
    
    所有渠道实现需要继承此类并实现抽象方法
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.channel_type: ChannelType = ChannelType.WEBCHAT
        self._message_handler: Optional[Callable] = None
        self._running = False
        
    @property
    @abstractmethod
    def name(self) -> str:
        """渠道名称"""
        pass
    
    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._running
    
    def set_message_handler(self, handler: Callable[[ChannelMessage], Any]):
        """设置消息处理器"""
        self._message_handler = handler
    
    @abstractmethod
    async def connect(self) -> bool:
        """连接到渠道"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """断开连接"""
        pass
    
    @abstractmethod
    async def send_message(
        self,
        channel_id: str,
        response: ChannelResponse
    ) -> bool:
        """发送消息"""
        pass
    
    @abstractmethod
    async def send_typing(self, channel_id: str):
        """发送正在输入状态"""
        pass
    
    async def handle_message(self, message: ChannelMessage):
        """处理收到的消息"""
        if self._message_handler:
            await self._message_handler(message)
    
    # 可选方法
    async def get_channel_info(self, channel_id: str) -> Optional[dict]:
        """获取渠道信息"""
        return None
    
    async def get_user_info(self, user_id: str) -> Optional[ChannelUser]:
        """获取用户信息"""
        return None
    
    async def upload_file(
        self,
        channel_id: str,
        file_path: str,
        filename: Optional[str] = None
    ) -> Optional[str]:
        """上传文件，返回文件 URL"""
        return None
    
    def validate_config(self) -> tuple[bool, str]:
        """验证配置"""
        return True, "OK"


class ChannelError(Exception):
    """渠道错误"""
    def __init__(self, channel: str, message: str):
        self.channel = channel
        self.message = message
        super().__init__(f"[{channel}] {message}")


class ChannelAuthError(ChannelError):
    """认证错误"""
    pass


class ChannelConnectionError(ChannelError):
    """连接错误"""
    pass


class ChannelRateLimitError(ChannelError):
    """限流错误"""
    def __init__(self, channel: str, retry_after: int = 0):
        self.retry_after = retry_after
        super().__init__(channel, f"Rate limited, retry after {retry_after}s")
