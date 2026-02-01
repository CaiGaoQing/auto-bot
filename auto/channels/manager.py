"""
渠道管理器

统一管理所有消息渠道，路由消息到 AI 处理
"""

import asyncio
import logging
from typing import Dict, Optional, Callable, Any, List
from datetime import datetime

from .base import (
    BaseChannel,
    ChannelType,
    ChannelMessage,
    ChannelResponse,
    ChannelError,
    MessageType,
)
from .telegram import TelegramChannel
from .discord import DiscordChannel
from .wechat_work import WeComChannel

logger = logging.getLogger(__name__)


# 渠道类型映射
CHANNEL_CLASSES = {
    ChannelType.TELEGRAM: TelegramChannel,
    ChannelType.DISCORD: DiscordChannel,
    ChannelType.WECHAT_WORK: WeComChannel,
}


class ChannelManager:
    """
    渠道管理器
    
    负责:
    - 管理多个渠道的连接
    - 统一消息路由
    - 会话管理
    """
    
    def __init__(self):
        self._channels: Dict[str, BaseChannel] = {}
        self._message_handler: Optional[Callable] = None
        self._sessions: Dict[str, dict] = {}  # session_id -> session_data
    
    @property
    def channels(self) -> Dict[str, BaseChannel]:
        return self._channels
    
    @property
    def connected_channels(self) -> List[str]:
        return [
            name for name, ch in self._channels.items()
            if ch.is_connected
        ]
    
    def set_message_handler(self, handler: Callable[[ChannelMessage], Any]):
        """
        设置全局消息处理器
        
        handler 签名: async def handler(message: ChannelMessage) -> ChannelResponse
        """
        self._message_handler = handler
    
    async def add_channel(
        self,
        name: str,
        channel_type: ChannelType,
        config: dict
    ) -> BaseChannel:
        """
        添加渠道
        
        Args:
            name: 渠道名称（唯一标识）
            channel_type: 渠道类型
            config: 渠道配置
        
        Returns:
            渠道实例
        """
        if name in self._channels:
            raise ValueError(f"渠道 {name} 已存在")
        
        channel_class = CHANNEL_CLASSES.get(channel_type)
        if not channel_class:
            raise ValueError(f"不支持的渠道类型: {channel_type}")
        
        channel = channel_class(config)
        channel.set_message_handler(self._on_message)
        
        self._channels[name] = channel
        logger.info(f"添加渠道: {name} ({channel_type.value})")
        
        return channel
    
    def remove_channel(self, name: str):
        """移除渠道"""
        if name in self._channels:
            del self._channels[name]
            logger.info(f"移除渠道: {name}")
    
    async def connect_channel(self, name: str) -> bool:
        """连接指定渠道"""
        channel = self._channels.get(name)
        if not channel:
            raise ValueError(f"渠道不存在: {name}")
        
        try:
            result = await channel.connect()
            logger.info(f"渠道已连接: {name}")
            return result
        except ChannelError as e:
            logger.error(f"渠道连接失败: {e}")
            return False
    
    async def disconnect_channel(self, name: str):
        """断开指定渠道"""
        channel = self._channels.get(name)
        if channel:
            await channel.disconnect()
            logger.info(f"渠道已断开: {name}")
    
    async def connect_all(self) -> Dict[str, bool]:
        """连接所有渠道"""
        results = {}
        for name in self._channels:
            try:
                results[name] = await self.connect_channel(name)
            except Exception as e:
                logger.error(f"连接渠道 {name} 失败: {e}")
                results[name] = False
        return results
    
    async def disconnect_all(self):
        """断开所有渠道"""
        for name in list(self._channels.keys()):
            await self.disconnect_channel(name)
    
    async def _on_message(self, message: ChannelMessage):
        """
        内部消息处理
        
        1. 生成/获取会话 ID
        2. 发送 typing 状态
        3. 调用消息处理器
        4. 发送响应
        """
        # 生成会话 ID
        session_id = self._get_session_id(message)
        message.session_id = session_id
        
        # 获取渠道
        channel = self._get_channel_for_message(message)
        if not channel:
            logger.error(f"找不到消息对应的渠道: {message.channel_type}")
            return
        
        # 发送 typing 状态
        await channel.send_typing(message.channel_id)
        
        # 调用处理器
        if self._message_handler:
            try:
                response = await self._message_handler(message)
                
                if response:
                    # 如果返回字符串，转换为 ChannelResponse
                    if isinstance(response, str):
                        response = ChannelResponse(content=response)
                    
                    # 设置回复目标
                    if not response.reply_to_id:
                        response.reply_to_id = message.id
                    
                    # 发送响应
                    await channel.send_message(message.channel_id, response)
                    
            except Exception as e:
                logger.error(f"消息处理失败: {e}", exc_info=True)
                # 发送错误提示
                error_response = ChannelResponse(
                    content=f"❌ 处理消息时出错: {str(e)}"
                )
                await channel.send_message(message.channel_id, error_response)
    
    def _get_session_id(self, message: ChannelMessage) -> str:
        """
        获取会话 ID
        
        会话隔离规则:
        - 每个 channel_type + channel_id 组合一个会话
        - 可以根据用户 ID 进一步隔离
        """
        return f"{message.channel_type.value}:{message.channel_id}"
    
    def _get_channel_for_message(self, message: ChannelMessage) -> Optional[BaseChannel]:
        """获取消息对应的渠道"""
        for channel in self._channels.values():
            if channel.channel_type == message.channel_type:
                return channel
        return None
    
    async def send_message(
        self,
        channel_name: str,
        channel_id: str,
        response: ChannelResponse
    ) -> bool:
        """
        主动发送消息
        
        Args:
            channel_name: 渠道名称
            channel_id: 目标 ID（用户/群组/频道）
            response: 响应内容
        """
        channel = self._channels.get(channel_name)
        if not channel:
            logger.error(f"渠道不存在: {channel_name}")
            return False
        
        if not channel.is_connected:
            logger.error(f"渠道未连接: {channel_name}")
            return False
        
        return await channel.send_message(channel_id, response)
    
    async def broadcast(
        self,
        response: ChannelResponse,
        channel_ids: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, List[bool]]:
        """
        广播消息
        
        Args:
            response: 响应内容
            channel_ids: {channel_name: [channel_id, ...]}
                        如果为 None，则发送到所有已知会话
        
        Returns:
            {channel_name: [success, ...]}
        """
        results = {}
        
        if channel_ids:
            for channel_name, ids in channel_ids.items():
                results[channel_name] = []
                for cid in ids:
                    success = await self.send_message(channel_name, cid, response)
                    results[channel_name].append(success)
        
        return results
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """获取会话数据"""
        return self._sessions.get(session_id)
    
    def set_session_data(self, session_id: str, key: str, value: Any):
        """设置会话数据"""
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "created_at": datetime.now().isoformat(),
            }
        self._sessions[session_id][key] = value
    
    def clear_session(self, session_id: str):
        """清除会话"""
        if session_id in self._sessions:
            del self._sessions[session_id]
    
    def get_status(self) -> dict:
        """获取管理器状态"""
        return {
            "total_channels": len(self._channels),
            "connected_channels": len(self.connected_channels),
            "active_sessions": len(self._sessions),
            "channels": {
                name: {
                    "type": ch.channel_type.value,
                    "connected": ch.is_connected,
                }
                for name, ch in self._channels.items()
            }
        }


# 全局实例
_channel_manager: Optional[ChannelManager] = None


def get_channel_manager() -> ChannelManager:
    """获取全局渠道管理器"""
    global _channel_manager
    if _channel_manager is None:
        _channel_manager = ChannelManager()
    return _channel_manager
