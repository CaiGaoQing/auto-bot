"""
会话管理模块

借鉴 OpenClaw 的 Session 设计:
- 多会话隔离
- 会话持久化
- 上下文压缩
- Agent 间通信
"""

from .manager import SessionManager, Session, SessionStatus
from .store import SessionStore

__all__ = [
    "SessionManager",
    "Session",
    "SessionStatus",
    "SessionStore",
]
