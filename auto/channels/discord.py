"""
Discord 渠道实现

使用 discord.py 库
参考 OpenClaw 的 discord.js 实现
"""

import asyncio
import logging
from typing import Optional, List
from datetime import datetime

from .base import (
    BaseChannel,
    ChannelType,
    ChannelMessage,
    ChannelResponse,
    ChannelUser,
    MessageType,
    ChannelAuthError,
    ChannelConnectionError,
)

logger = logging.getLogger(__name__)


class DiscordChannel(BaseChannel):
    """
    Discord 渠道
    
    配置示例:
    {
        "token": "YOUR_BOT_TOKEN",
        "allowed_guilds": [123456789],  # 可选：允许的服务器 ID
        "allowed_channels": [123456789],  # 可选：允许的频道 ID
        "allowed_users": [123456789],  # 可选：允许的用户 ID
        "prefix": "!",  # 可选：命令前缀
        "dm_enabled": true,  # 是否允许 DM
    }
    """
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.channel_type = ChannelType.DISCORD
        self.token = config.get("token", "")
        self.allowed_guilds = set(config.get("allowed_guilds", []))
        self.allowed_channels = set(config.get("allowed_channels", []))
        self.allowed_users = set(config.get("allowed_users", []))
        self.prefix = config.get("prefix", "!")
        self.dm_enabled = config.get("dm_enabled", True)
        
        self._client = None
        self._ready = asyncio.Event()
    
    @property
    def name(self) -> str:
        return "Discord"
    
    def validate_config(self) -> tuple[bool, str]:
        if not self.token:
            return False, "缺少 Discord Bot Token"
        return True, "OK"
    
    async def connect(self) -> bool:
        """连接到 Discord"""
        try:
            import discord
            from discord import Intents
        except ImportError:
            raise ChannelConnectionError(
                "discord",
                "请安装 discord.py: pip install discord.py"
            )
        
        valid, msg = self.validate_config()
        if not valid:
            raise ChannelAuthError("discord", msg)
        
        # 配置 Intents
        intents = Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.dm_messages = self.dm_enabled
        
        self._client = discord.Client(intents=intents)
        
        # 注册事件处理器
        @self._client.event
        async def on_ready():
            logger.info(f"Discord 已连接: {self._client.user}")
            self._ready.set()
        
        @self._client.event
        async def on_message(message):
            await self._handle_message(message)
        
        # 启动客户端（非阻塞）
        asyncio.create_task(self._client.start(self.token))
        
        # 等待连接成功
        try:
            await asyncio.wait_for(self._ready.wait(), timeout=30)
        except asyncio.TimeoutError:
            raise ChannelConnectionError("discord", "连接超时")
        
        self._running = True
        return True
    
    async def disconnect(self):
        """断开连接"""
        if self._client:
            await self._client.close()
        self._running = False
        self._ready.clear()
        logger.info("Discord 已断开")
    
    async def send_message(
        self,
        channel_id: str,
        response: ChannelResponse
    ) -> bool:
        """发送消息"""
        if not self._client:
            return False
        
        try:
            import discord
            
            channel = self._client.get_channel(int(channel_id))
            if not channel:
                # 尝试获取 DM 频道
                user = await self._client.fetch_user(int(channel_id))
                if user:
                    channel = await user.create_dm()
            
            if not channel:
                logger.error(f"找不到频道: {channel_id}")
                return False
            
            # 构建消息
            kwargs = {}
            
            # 处理 embed
            if response.embed:
                embed = discord.Embed(
                    title=response.embed.get("title"),
                    description=response.embed.get("description"),
                    color=response.embed.get("color", 0x5865F2),
                )
                if response.embed.get("fields"):
                    for field in response.embed["fields"]:
                        embed.add_field(
                            name=field["name"],
                            value=field["value"],
                            inline=field.get("inline", False),
                        )
                kwargs["embed"] = embed
            
            # 处理回复
            if response.reply_to_id:
                try:
                    ref_message = await channel.fetch_message(int(response.reply_to_id))
                    kwargs["reference"] = ref_message
                except:
                    pass
            
            # 发送消息
            # Discord 单条消息限制 2000 字符
            content = response.content
            if len(content) > 2000:
                # 分段发送
                for i in range(0, len(content), 1900):
                    chunk = content[i:i+1900]
                    if i == 0:
                        await channel.send(chunk, **kwargs)
                    else:
                        await channel.send(chunk)
            else:
                await channel.send(content, **kwargs)
            
            # 发送附件
            for attachment in response.attachments:
                file_path = attachment.get("path")
                if file_path:
                    await channel.send(file=discord.File(file_path))
            
            return True
            
        except Exception as e:
            logger.error(f"Discord 发送消息失败: {e}")
            return False
    
    async def send_typing(self, channel_id: str):
        """发送正在输入状态"""
        if not self._client:
            return
        try:
            channel = self._client.get_channel(int(channel_id))
            if channel:
                await channel.typing()
        except Exception as e:
            logger.warning(f"发送 typing 状态失败: {e}")
    
    def _is_allowed(self, message) -> bool:
        """检查是否允许处理消息"""
        # 忽略自己的消息
        if message.author == self._client.user:
            return False
        
        # 忽略其他 Bot
        if message.author.bot:
            return False
        
        # 如果没有配置任何限制，允许所有
        if not self.allowed_guilds and not self.allowed_channels and not self.allowed_users:
            return True
        
        # 检查用户白名单
        if message.author.id in self.allowed_users:
            return True
        
        # 检查服务器白名单
        if message.guild and message.guild.id in self.allowed_guilds:
            return True
        
        # 检查频道白名单
        if message.channel.id in self.allowed_channels:
            return True
        
        # DM 消息
        if not message.guild and self.dm_enabled:
            return True
        
        return False
    
    async def _handle_message(self, message):
        """处理 Discord 消息"""
        import discord
        
        if not self._is_allowed(message):
            return
        
        # 确定消息类型
        msg_type = MessageType.TEXT
        attachments = []
        
        for att in message.attachments:
            if att.content_type and att.content_type.startswith("image/"):
                msg_type = MessageType.IMAGE
                attachments.append({
                    "type": "image",
                    "url": att.url,
                    "filename": att.filename,
                    "size": att.size,
                })
            else:
                attachments.append({
                    "type": "document",
                    "url": att.url,
                    "filename": att.filename,
                    "size": att.size,
                })
        
        # 构建统一消息
        channel_message = ChannelMessage(
            id=str(message.id),
            channel_type=ChannelType.DISCORD,
            channel_id=str(message.channel.id),
            sender=ChannelUser(
                id=str(message.author.id),
                username=message.author.name,
                display_name=message.author.display_name,
                avatar_url=str(message.author.avatar.url) if message.author.avatar else None,
                is_bot=message.author.bot,
            ),
            content=message.content,
            message_type=msg_type,
            reply_to_id=str(message.reference.message_id) if message.reference else None,
            attachments=attachments,
            mentions=[str(u.id) for u in message.mentions],
            timestamp=message.created_at,
            raw_data={
                "guild_id": str(message.guild.id) if message.guild else None,
                "guild_name": message.guild.name if message.guild else None,
            },
        )
        
        await self.handle_message(channel_message)
    
    async def get_channel_info(self, channel_id: str) -> Optional[dict]:
        """获取频道信息"""
        if not self._client:
            return None
        try:
            channel = self._client.get_channel(int(channel_id))
            if channel:
                return {
                    "id": str(channel.id),
                    "name": channel.name,
                    "type": str(channel.type),
                    "guild_id": str(channel.guild.id) if hasattr(channel, 'guild') else None,
                    "guild_name": channel.guild.name if hasattr(channel, 'guild') else None,
                }
        except Exception as e:
            logger.error(f"获取频道信息失败: {e}")
        return None
