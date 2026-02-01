"""WebSocket 消息处理器"""

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Optional

from auto.gateway.websocket.manager import ConnectionManager, get_connection_manager


@dataclass
class WebSocketMessage:
    """WebSocket 消息"""
    type: str
    data: Any
    connection_id: str
    user_id: str
    workspace_id: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class WebSocketHandler:
    """WebSocket 消息处理器
    
    处理不同类型的 WebSocket 消息。
    """
    
    def __init__(self, manager: Optional[ConnectionManager] = None):
        self._manager = manager or get_connection_manager()
        self._handlers: dict[str, Callable] = {}
        
        # 注册默认处理器
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """注册默认处理器"""
        self.register("ping", self._handle_ping)
        self.register("chat", self._handle_chat)
        self.register("execute_tool", self._handle_execute_tool)
        self.register("subscribe", self._handle_subscribe)
    
    def register(
        self,
        message_type: str,
        handler: Callable,
    ) -> None:
        """注册消息处理器"""
        self._handlers[message_type] = handler
    
    async def handle(
        self,
        connection_id: str,
        raw_message: str,
        user_id: str,
        workspace_id: Optional[str] = None,
    ) -> Optional[dict]:
        """处理消息"""
        try:
            data = json.loads(raw_message)
        except json.JSONDecodeError:
            return {
                "type": "error",
                "error": "Invalid JSON",
            }
        
        message_type = data.get("type", "unknown")
        message_data = data.get("data", {})
        
        message = WebSocketMessage(
            type=message_type,
            data=message_data,
            connection_id=connection_id,
            user_id=user_id,
            workspace_id=workspace_id,
        )
        
        handler = self._handlers.get(message_type)
        
        if not handler:
            return {
                "type": "error",
                "error": f"Unknown message type: {message_type}",
            }
        
        try:
            result = await handler(message)
            return result
        except Exception as e:
            return {
                "type": "error",
                "error": str(e),
            }
    
    async def _handle_ping(self, message: WebSocketMessage) -> dict:
        """处理 ping"""
        return {
            "type": "pong",
            "timestamp": datetime.now().isoformat(),
        }
    
    async def _handle_chat(self, message: WebSocketMessage) -> dict:
        """处理聊天消息，流式返回"""
        from auto.core.ai.router import get_router
        from auto.shared.models import Message, MessageRole
        
        content = message.data.get("content", "")
        model = message.data.get("model")
        stream = message.data.get("stream", True)
        
        if not content:
            return {"type": "error", "error": "Empty message"}
        
        router = get_router()
        messages = [Message(role=MessageRole.USER, content=content)]
        
        if stream:
            # 流式响应
            async def stream_response():
                try:
                    async for chunk in router.chat_stream(messages=messages, model=model):
                        yield {
                            "type": "chat_chunk",
                            "content": chunk,
                            "timestamp": datetime.now().isoformat(),
                        }
                except Exception as e:
                    yield {
                        "type": "error",
                        "error": str(e),
                    }
            
            # 发送流式数据
            connection = self._manager.get_connection(message.connection_id)
            if connection:
                async for chunk_data in stream_response():
                    await connection.send_json(chunk_data)
            
            return {
                "type": "chat_end",
                "timestamp": datetime.now().isoformat(),
            }
        else:
            # 非流式响应
            response = await router.chat(messages=messages, model=model)
            
            return {
                "type": "chat_response",
                "content": response.message.content,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                },
                "timestamp": datetime.now().isoformat(),
            }
    
    async def _handle_execute_tool(self, message: WebSocketMessage) -> dict:
        """处理工具执行请求"""
        from auto.core.tool.executor import ToolExecutor
        from auto.core.tool.context import ToolContext
        
        tool_name = message.data.get("tool")
        arguments = message.data.get("arguments", {})
        
        if not tool_name:
            return {"type": "error", "error": "Tool name required"}
        
        executor = ToolExecutor()
        context = ToolContext(
            workspace_id=message.workspace_id or "",
            user_id=message.user_id,
        )
        
        result = await executor.execute(
            tool_name=tool_name,
            arguments=arguments,
            context=context,
        )
        
        return {
            "type": "tool_result",
            "tool": tool_name,
            "success": result.success,
            "data": result.data,
            "message": result.message,
            "error": result.error,
            "timestamp": datetime.now().isoformat(),
        }
    
    async def _handle_subscribe(self, message: WebSocketMessage) -> dict:
        """处理订阅请求"""
        channel = message.data.get("channel")
        
        if not channel:
            return {"type": "error", "error": "Channel required"}
        
        # TODO: 实现订阅逻辑
        
        return {
            "type": "subscribed",
            "channel": channel,
            "timestamp": datetime.now().isoformat(),
        }


# WebSocket 路由
async def websocket_endpoint(
    websocket,
    connection_id: str,
    user_id: str,
    workspace_id: Optional[str] = None,
):
    """WebSocket 端点处理函数"""
    manager = get_connection_manager()
    handler = WebSocketHandler(manager)
    
    connection = await manager.connect(
        websocket=websocket,
        connection_id=connection_id,
        user_id=user_id,
        workspace_id=workspace_id,
    )
    
    try:
        # 发送连接成功消息
        await connection.send_json({
            "type": "connected",
            "connection_id": connection_id,
            "timestamp": datetime.now().isoformat(),
        })
        
        # 消息循环
        while True:
            data = await websocket.receive_text()
            
            response = await handler.handle(
                connection_id=connection_id,
                raw_message=data,
                user_id=user_id,
                workspace_id=workspace_id,
            )
            
            if response:
                await connection.send_json(response)
    
    except Exception:
        pass
    finally:
        await manager.disconnect(connection_id)
