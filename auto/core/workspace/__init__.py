"""
工作空间模块

支持:
- AGENTS.md: Agent 行为定义
- SOUL.md: AI 人格设定
- TOOLS.md: 工具使用说明
- 自动读取工作空间所有文件作为知识上下文
"""

from .prompts import (
    WorkspacePrompts,
    get_workspace_prompts,
    init_workspace_prompts,
    READABLE_EXTENSIONS,
    MAX_FILE_SIZE,
    MAX_CONTEXT_SIZE,
)

__all__ = [
    "WorkspacePrompts",
    "get_workspace_prompts",
    "init_workspace_prompts",
    "READABLE_EXTENSIONS",
    "MAX_FILE_SIZE",
    "MAX_CONTEXT_SIZE",
]
