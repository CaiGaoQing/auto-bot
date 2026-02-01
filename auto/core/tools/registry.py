"""
工具注册表

管理所有可用的工具，提供给 AI 调用
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Type, Any
import logging

from .base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


@dataclass
class Tool:
    """注册的工具信息"""
    name: str
    tool_class: Type[BaseTool]
    category: str = "general"
    enabled: bool = True


class ToolRegistry:
    """
    工具注册表
    
    OpenClaw 风格：
    - 集中管理所有工具
    - 提供工具发现和调用
    - 支持动态注册新工具
    """
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._initialized = False
    
    def register(self, tool_class: Type[BaseTool]) -> None:
        """
        注册工具
        
        Args:
            tool_class: 工具类
        """
        tool = Tool(
            name=tool_class.name,
            tool_class=tool_class,
            category=tool_class.category,
        )
        self._tools[tool.name] = tool
        logger.info(f"注册工具: {tool.name}")
    
    def unregister(self, name: str) -> bool:
        """取消注册工具"""
        if name in self._tools:
            del self._tools[name]
            return True
        return False
    
    def get_tool(self, name: str, workspace_id: Optional[str] = None) -> Optional[BaseTool]:
        """
        获取工具实例
        
        Args:
            name: 工具名称
            workspace_id: 工作空间 ID
            
        Returns:
            工具实例
        """
        tool = self._tools.get(name)
        if not tool or not tool.enabled:
            return None
        return tool.tool_class(workspace_id=workspace_id)
    
    def list_tools(self, category: Optional[str] = None) -> List[Tool]:
        """列出工具"""
        tools = list(self._tools.values())
        if category:
            tools = [t for t in tools if t.category == category]
        return [t for t in tools if t.enabled]
    
    def get_all_schemas(self, workspace_id: Optional[str] = None) -> List[dict]:
        """
        获取所有工具的 schema（用于 AI function calling）
        
        Args:
            workspace_id: 工作空间 ID
            
        Returns:
            工具 schema 列表
        """
        schemas = []
        for tool in self._tools.values():
            if tool.enabled:
                instance = tool.tool_class(workspace_id=workspace_id)
                schemas.append(instance.get_schema())
        return schemas
    
    async def execute(
        self, 
        tool_name: str, 
        workspace_id: Optional[str] = None,
        **kwargs
    ) -> ToolResult:
        """
        执行工具
        
        Args:
            tool_name: 工具名称
            workspace_id: 工作空间 ID
            **kwargs: 工具参数
            
        Returns:
            执行结果
        """
        tool = self.get_tool(tool_name, workspace_id)
        if not tool:
            return ToolResult(
                success=False,
                message=f"工具不存在: {tool_name}",
                error=f"未找到工具 {tool_name}",
            )
        
        # 验证参数
        error = tool.validate_params(**kwargs)
        if error:
            return ToolResult(
                success=False,
                message="参数验证失败",
                error=error,
            )
        
        try:
            return await tool.execute(**kwargs)
        except Exception as e:
            logger.error(f"工具执行失败 {tool_name}: {e}")
            return ToolResult(
                success=False,
                message="工具执行失败",
                error=str(e),
            )
    
    def get_categories(self) -> List[str]:
        """获取所有分类"""
        return list(set(t.category for t in self._tools.values()))


# 全局实例
_tool_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """获取全局工具注册表"""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
        # 自动注册内置工具
        _register_builtin_tools(_tool_registry)
    return _tool_registry


def _register_builtin_tools(registry: ToolRegistry):
    """注册内置工具"""
    from .file_tools import (
        CreateFileTool,
        SaveCodeTool,
        GeneratePPTTool,
        GenerateExcelTool,
    )
    
    registry.register(CreateFileTool)
    registry.register(SaveCodeTool)
    registry.register(GeneratePPTTool)
    registry.register(GenerateExcelTool)
