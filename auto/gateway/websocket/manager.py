"""WebSocket 连接管理器"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from fastapi import WebSocket


@dataclass
class Connection:
    """WebSocket 连接"""
    websocket: WebSocket
    user_id: str
    workspace_id: Optional[str] = None
    connected_at: datetime = field(default_factory=datetime.now)
    
    async def send_json(self, data: dict) -> bool:
        """发送 JSON 数据"""
        try:
            await self.websocket.send_json(data)
            return True
        except Exception:
            return False
    
    async def send_text(self, text: str) -> bool:
        """发送文本"""
        try:
            await self.websocket.send_text(text)
            return True
        except Exception:
            return False


class ConnectionManager:
    """WebSocket 连接管理器
    
    管理所有 WebSocket 连接，支持：
    - 用户级连接管理
    - 工作空间级广播
    - 流式消息推送
    """
    
    def __init__(self):
        self._connections: dict[str, Connection] = {}  # connection_id -> Connection
        self._user_connections: dict[str, set[str]] = {}  # user_id -> {connection_ids}
        self._workspace_connections: dict[str, set[str]] = {}  # workspace_id -> {connection_ids}
        self._lock = asyncio.Lock()
    
    async def connect(
        self,
        websocket: WebSocket,
        connection_id: str,
        user_id: str,
        workspace_id: Optional[str] = None,
    ) -> Connection:
        """接受连接"""
        await websocket.accept()
        
        connection = Connection(
            websocket=websocket,
            user_id=user_id,
            workspace_id=workspace_id,
        )
        
        async with self._lock:
            self._connections[connection_id] = connection
            
            # 用户级映射
            if user_id not in self._user_connections:
                self._user_connections[user_id] = set()
            self._user_connections[user_id].add(connection_id)
            
            # 工作空间级映射
            if workspace_id:
                if workspace_id not in self._workspace_connections:
                    self._workspace_connections[workspace_id] = set()
                self._workspace_connections[workspace_id].add(connection_id)
        
        return connection
    
    async def disconnect(self, connection_id: str) -> None:
        """断开连接"""
        async with self._lock:
            connection = self._connections.pop(connection_id, None)
            
            if connection:
                # 清理用户映射
                user_conns = self._user_connections.get(connection.user_id)
                if user_conns:
                    user_conns.discard(connection_id)
                    if not user_conns:
                        del self._user_connections[connection.user_id]
                
                # 清理工作空间映射
                if connection.workspace_id:
                    ws_conns = self._workspace_connections.get(connection.workspace_id)
                    if ws_conns:
                        ws_conns.discard(connection_id)
                        if not ws_conns:
                            del self._workspace_connections[connection.workspace_id]
    
    async def send_to_connection(
        self,
        connection_id: str,
        message: dict,
    ) -> bool:
        """发送消息到指定连接"""
        connection = self._connections.get(connection_id)
        if connection:
            return await connection.send_json(message)
        return False
    
    async def send_to_user(
        self,
        user_id: str,
        message: dict,
    ) -> int:
        """发送消息到用户的所有连接"""
        connection_ids = self._user_connections.get(user_id, set())
        sent = 0
        
        for conn_id in connection_ids:
            if await self.send_to_connection(conn_id, message):
                sent += 1
        
        return sent
    
    async def send_to_workspace(
        self,
        workspace_id: str,
        message: dict,
    ) -> int:
        """发送消息到工作空间的所有连接"""
        connection_ids = self._workspace_connections.get(workspace_id, set())
        sent = 0
        
        for conn_id in connection_ids:
            if await self.send_to_connection(conn_id, message):
                sent += 1
        
        return sent
    
    async def broadcast(self, message: dict) -> int:
        """广播消息到所有连接"""
        sent = 0
        
        for conn_id in list(self._connections.keys()):
            if await self.send_to_connection(conn_id, message):
                sent += 1
        
        return sent
    
    async def stream_to_connection(
        self,
        connection_id: str,
        stream_generator,
        message_type: str = "stream",
    ) -> None:
        """流式发送数据到连接"""
        connection = self._connections.get(connection_id)
        if not connection:
            return
        
        try:
            async for chunk in stream_generator:
                message = {
                    "type": message_type,
                    "data": chunk,
                    "timestamp": datetime.now().isoformat(),
                }
                await connection.send_json(message)
            
            # 发送完成消息
            await connection.send_json({
                "type": f"{message_type}_end",
                "timestamp": datetime.now().isoformat(),
            })
        except Exception as e:
            await connection.send_json({
                "type": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            })
    
    def get_connection(self, connection_id: str) -> Optional[Connection]:
        """获取连接"""
        return self._connections.get(connection_id)
    
    def get_user_connections(self, user_id: str) -> list[str]:
        """获取用户的所有连接 ID"""
        return list(self._user_connections.get(user_id, set()))
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "total_connections": len(self._connections),
            "total_users": len(self._user_connections),
            "total_workspaces": len(self._workspace_connections),
        }


# 全局连接管理器
_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """获取全局连接管理器"""
    global _manager
    if _manager is None:
        _manager = ConnectionManager()
    return _manager
