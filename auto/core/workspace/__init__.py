"""
工作空间模块

支持:
- AGENTS.md: Agent 行为定义
- SOUL.md: AI 人格设定
- TOOLS.md: 工具使用说明
"""

from .prompts import WorkspacePrompts, get_workspace_prompts

__all__ = [
    "WorkspacePrompts",
    "get_workspace_prompts",
]
