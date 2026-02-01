"""
Telegram 渠道实现

使用 python-telegram-bot 库
参考 OpenClaw 的 grammY 实现
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


class TelegramChannel(BaseChannel):
    """
    Telegram 渠道
    
    配置示例:
    {
        "token": "123456:ABCDEF...",
        "allowed_users": [123456789],  # 可选：允许的用户 ID
        "allowed_groups": [-100123456789],  # 可选：允许的群组 ID
        "webhook_url": "https://...",  # 可选：Webhook URL
        "proxy": "http://..."  # 可选：代理
    }
    """
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.channel_type = ChannelType.TELEGRAM
        self.token = config.get("token", "")
        self.allowed_users = set(config.get("allowed_users", []))
        self.allowed_groups = set(config.get("allowed_groups", []))
        self.use_webhook = bool(config.get("webhook_url"))
        
        self._app = None
        self._bot = None
    
    @property
    def name(self) -> str:
        return "Telegram"
    
    def validate_config(self) -> tuple[bool, str]:
        if not self.token:
            return False, "缺少 Telegram Bot Token"
        if not self.token.count(":") == 1:
            return False, "Token 格式无效"
        return True, "OK"
    
    async def connect(self) -> bool:
        """连接到 Telegram"""
        try:
            from telegram import Bot, Update
            from telegram.ext import (
                Application,
                CommandHandler,
                MessageHandler,
                filters,
                ContextTypes,
            )
        except ImportError:
            raise ChannelConnectionError(
                "telegram",
                "请安装 python-telegram-bot: pip install python-telegram-bot"
            )
        
        valid, msg = self.validate_config()
        if not valid:
            raise ChannelAuthError("telegram", msg)
        
        # 创建 Application
        builder = Application.builder().token(self.token)
        
        # 配置代理
        if self.config.get("proxy"):
            builder.proxy(self.config["proxy"])
        
        self._app = builder.build()
        self._bot = self._app.bot
        
        # 注册处理器
        self._app.add_handler(CommandHandler("start", self._handle_start))
        self._app.add_handler(CommandHandler("help", self._handle_help))
        self._app.add_handler(CommandHandler("new", self._handle_new_session))
        self._app.add_handler(CommandHandler("status", self._handle_status))
        self._app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self._handle_text_message
            )
        )
        self._app.add_handler(
            MessageHandler(
                filters.PHOTO | filters.Document.ALL,
                self._handle_media_message
            )
        )
        
        # 启动
        await self._app.initialize()
        await self._app.start()
        
        if self.use_webhook:
            webhook_url = self.config["webhook_url"]
            await self._bot.set_webhook(webhook_url)
            logger.info(f"Telegram Webhook 已设置: {webhook_url}")
        else:
            await self._app.updater.start_polling(drop_pending_updates=True)
            logger.info("Telegram 轮询已启动")
        
        self._running = True
        
        # 获取 bot 信息
        me = await self._bot.get_me()
        logger.info(f"Telegram 已连接: @{me.username}")
        
        return True
    
    async def disconnect(self):
        """断开连接"""
        if self._app:
            if self._app.updater and self._app.updater.running:
                await self._app.updater.stop()
            await self._app.stop()
            await self._app.shutdown()
        self._running = False
        logger.info("Telegram 已断开")
    
    async def send_message(
        self,
        channel_id: str,
        response: ChannelResponse
    ) -> bool:
        """发送消息"""
        if not self._bot:
            return False
        
        try:
            chat_id = int(channel_id)
            
            # 发送文本
            if response.message_type == MessageType.TEXT:
                await self._bot.send_message(
                    chat_id=chat_id,
                    text=response.content,
                    parse_mode=response.parse_mode or "Markdown",
                    reply_to_message_id=int(response.reply_to_id) if response.reply_to_id else None,
                )
            
            # 发送文件附件
            for attachment in response.attachments:
                file_type = attachment.get("type", "document")
                file_path = attachment.get("path") or attachment.get("url")
                
                if file_type == "image":
                    await self._bot.send_photo(
                        chat_id=chat_id,
                        photo=file_path,
                        caption=attachment.get("caption", ""),
                    )
                elif file_type == "document":
                    await self._bot.send_document(
                        chat_id=chat_id,
                        document=file_path,
                        caption=attachment.get("caption", ""),
                        filename=attachment.get("filename"),
                    )
            
            return True
            
        except Exception as e:
            logger.error(f"Telegram 发送消息失败: {e}")
            return False
    
    async def send_typing(self, channel_id: str):
        """发送正在输入状态"""
        if self._bot:
            try:
                await self._bot.send_chat_action(
                    chat_id=int(channel_id),
                    action="typing"
                )
            except Exception as e:
                logger.warning(f"发送 typing 状态失败: {e}")
    
    def _is_allowed(self, user_id: int, chat_id: int) -> bool:
        """检查是否允许访问"""
        # 如果没有配置限制，允许所有
        if not self.allowed_users and not self.allowed_groups:
            return True
        
        # 检查用户白名单
        if user_id in self.allowed_users:
            return True
        
        # 检查群组白名单
        if chat_id in self.allowed_groups:
            return True
        
        return False
    
    def _convert_message(self, update) -> Optional[ChannelMessage]:
        """转换 Telegram 消息为统一格式"""
        message = update.message or update.edited_message
        if not message:
            return None
        
        user = message.from_user
        chat = message.chat
        
        # 检查权限
        if not self._is_allowed(user.id, chat.id):
            return None
        
        # 确定消息类型
        msg_type = MessageType.TEXT
        content = message.text or message.caption or ""
        attachments = []
        
        if message.photo:
            msg_type = MessageType.IMAGE
            # 获取最大尺寸的图片
            photo = message.photo[-1]
            attachments.append({
                "type": "image",
                "file_id": photo.file_id,
                "width": photo.width,
                "height": photo.height,
            })
        elif message.document:
            msg_type = MessageType.FILE
            attachments.append({
                "type": "document",
                "file_id": message.document.file_id,
                "filename": message.document.file_name,
                "mime_type": message.document.mime_type,
            })
        elif message.voice:
            msg_type = MessageType.AUDIO
            attachments.append({
                "type": "voice",
                "file_id": message.voice.file_id,
                "duration": message.voice.duration,
            })
        
        return ChannelMessage(
            id=str(message.message_id),
            channel_type=ChannelType.TELEGRAM,
            channel_id=str(chat.id),
            sender=ChannelUser(
                id=str(user.id),
                username=user.username,
                display_name=user.full_name,
                is_bot=user.is_bot,
            ),
            content=content,
            message_type=msg_type,
            reply_to_id=str(message.reply_to_message.message_id) if message.reply_to_message else None,
            attachments=attachments,
            timestamp=message.date,
            raw_data={"update": update.to_dict()},
        )
    
    async def _handle_start(self, update, context):
        """处理 /start 命令"""
        await update.message.reply_text(
            "👋 你好！我是 Auto Bot AI 助手。\n\n"
            "直接发送消息即可开始对话。\n\n"
            "常用命令：\n"
            "/new - 开始新对话\n"
            "/status - 查看状态\n"
            "/help - 获取帮助"
        )
    
    async def _handle_help(self, update, context):
        """处理 /help 命令"""
        await update.message.reply_text(
            "📖 Auto Bot 帮助\n\n"
            "我可以帮你完成各种任务：\n"
            "• 代码开发与调试\n"
            "• 文档撰写\n"
            "• 数据分析\n"
            "• PPT/Excel 生成\n"
            "• 翻译与总结\n\n"
            "命令列表：\n"
            "/new - 重置对话\n"
            "/status - 查看状态\n"
            "/help - 显示帮助"
        )
    
    async def _handle_new_session(self, update, context):
        """处理 /new 命令 - 重置会话"""
        # 这里可以清理会话状态
        await update.message.reply_text("✨ 对话已重置，开始新的对话吧！")
    
    async def _handle_status(self, update, context):
        """处理 /status 命令"""
        user = update.message.from_user
        chat = update.message.chat
        
        status_text = (
            f"📊 状态信息\n\n"
            f"用户: {user.full_name}\n"
            f"用户ID: {user.id}\n"
            f"聊天ID: {chat.id}\n"
            f"聊天类型: {chat.type}\n"
            f"渠道: Telegram"
        )
        await update.message.reply_text(status_text)
    
    async def _handle_text_message(self, update, context):
        """处理文本消息"""
        message = self._convert_message(update)
        if message:
            await self.handle_message(message)
    
    async def _handle_media_message(self, update, context):
        """处理媒体消息"""
        message = self._convert_message(update)
        if message:
            await self.handle_message(message)
    
    async def get_file_url(self, file_id: str) -> Optional[str]:
        """获取文件下载 URL"""
        if not self._bot:
            return None
        try:
            file = await self._bot.get_file(file_id)
            return file.file_path
        except Exception as e:
            logger.error(f"获取文件 URL 失败: {e}")
            return None
