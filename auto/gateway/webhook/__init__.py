"""Webhook 处理模块"""

from auto.gateway.webhook.handlers import WebhookHandler, WebhookRouter
from auto.gateway.webhook.providers import (
    WeChatWorkHandler,
    DingTalkHandler,
    FeishuHandler,
)

__all__ = [
    "WebhookHandler",
    "WebhookRouter",
    "WeChatWorkHandler",
    "DingTalkHandler",
    "FeishuHandler",
]
