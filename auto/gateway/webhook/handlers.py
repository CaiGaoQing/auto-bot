"""Webhook 处理器基类"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
import hashlib
import hmac


@dataclass
class WebhookEvent:
    """Webhook 事件"""
    source: str  # 来源 (wechat_work, dingtalk, feishu, custom)
    event_type: str  # 事件类型 (message, callback, etc.)
    user_id: str  # 用户标识
    content: str  # 内容
    raw_data: dict = field(default_factory=dict)  # 原始数据
    timestamp: datetime = field(default_factory=datetime.now)
    
    # 上下文信息
    conversation_id: Optional[str] = None
    workspace_id: Optional[str] = None
    
    # 回复信息
    reply_url: Optional[str] = None
    reply_token: Optional[str] = None


@dataclass
class WebhookResponse:
    """Webhook 响应"""
    success: bool
    message: str = ""
    data: dict = field(default_factory=dict)
    reply_content: Optional[str] = None


class WebhookHandler(ABC):
    """Webhook 处理器抽象基类"""
    
    @property
    @abstractmethod
    def source(self) -> str:
        """处理器来源标识"""
        pass
    
    @abstractmethod
    async def verify(self, request_data: dict, headers: dict) -> bool:
        """验证请求签名"""
        pass
    
    @abstractmethod
    async def parse(self, request_data: dict, headers: dict) -> Optional[WebhookEvent]:
        """解析请求为事件"""
        pass
    
    @abstractmethod
    async def reply(self, event: WebhookEvent, content: str) -> WebhookResponse:
        """发送回复"""
        pass
    
    async def handle(
        self,
        request_data: dict,
        headers: dict,
    ) -> WebhookResponse:
        """处理 Webhook 请求
        
        1. 验证签名
        2. 解析事件
        3. 处理事件
        4. 返回响应
        """
        # 验证签名
        if not await self.verify(request_data, headers):
            return WebhookResponse(
                success=False,
                message="签名验证失败",
            )
        
        # 解析事件
        event = await self.parse(request_data, headers)
        if not event:
            return WebhookResponse(
                success=False,
                message="无法解析事件",
            )
        
        # 处理事件 (调用 AI)
        response = await self.process_event(event)
        
        # 发送回复
        if response.reply_content:
            await self.reply(event, response.reply_content)
        
        return response
    
    async def process_event(self, event: WebhookEvent) -> WebhookResponse:
        """处理事件 (可被子类覆盖)"""
        from auto.core.ai.router import get_router
        from auto.shared.models import Message, MessageRole
        
        try:
            router = get_router()
            
            messages = [Message(role=MessageRole.USER, content=event.content)]
            
            response = await router.chat(messages)
            
            return WebhookResponse(
                success=True,
                message="处理成功",
                reply_content=response.message.content,
            )
        except Exception as e:
            return WebhookResponse(
                success=False,
                message=f"处理失败: {str(e)}",
            )


class WebhookRouter:
    """Webhook 路由器
    
    管理多个 Webhook 处理器。
    """
    
    def __init__(self):
        self._handlers: dict[str, WebhookHandler] = {}
    
    def register(self, handler: WebhookHandler) -> None:
        """注册处理器"""
        self._handlers[handler.source] = handler
    
    def get_handler(self, source: str) -> Optional[WebhookHandler]:
        """获取处理器"""
        return self._handlers.get(source)
    
    def list_handlers(self) -> list[str]:
        """列出所有处理器"""
        return list(self._handlers.keys())
    
    async def handle(
        self,
        source: str,
        request_data: dict,
        headers: dict,
    ) -> WebhookResponse:
        """处理 Webhook 请求"""
        handler = self.get_handler(source)
        
        if not handler:
            return WebhookResponse(
                success=False,
                message=f"未知的来源: {source}",
            )
        
        return await handler.handle(request_data, headers)


# 全局路由器实例
_router: Optional[WebhookRouter] = None


def get_webhook_router() -> WebhookRouter:
    """获取全局 Webhook 路由器"""
    global _router
    if _router is None:
        _router = WebhookRouter()
    return _router
