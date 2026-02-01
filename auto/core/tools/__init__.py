"""
工具系统

OpenClaw 风格的工具调用架构：
- AI 通过 function calling 调用工具
- 工具执行实际操作（创建文件、执行代码等）
- 可扩展的工具注册机制
"""

from .registry import ToolRegistry, Tool, get_tool_registry
from .base import BaseTool, ToolResult
from .file_tools import (
    CreateFileTool,
    SaveCodeTool, 
    GeneratePPTTool,
    GenerateExcelTool,
)

__all__ = [
    "ToolRegistry",
    "Tool",
    "get_tool_registry",
    "BaseTool",
    "ToolResult",
    "CreateFileTool",
    "SaveCodeTool",
    "GeneratePPTTool",
    "GenerateExcelTool",
]
