"""
多渠道消息支持模块

支持的渠道:
- Telegram
- Discord
- 企业微信 (WeCom)
- Slack (计划中)
- 飞书 (计划中)
"""

from .base import BaseChannel, ChannelMessage, ChannelType
from .manager import ChannelManager

__all__ = [
    "BaseChannel",
    "ChannelMessage",
    "ChannelType",
    "ChannelManager",
]
