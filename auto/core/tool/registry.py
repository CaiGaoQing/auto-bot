"""统一工具注册表"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

from auto.core.tool.context import ToolContext
from auto.core.tool.result import ToolResult


class ToolSource(Enum):
    """工具来源"""
    BUILTIN = "builtin"      # 内置技能包
    EXTERNAL = "external"    # 外部安装的技能包
    MCP = "mcp"              # MCP 服务器
    API = "api"              # HTTP API


@dataclass
class ToolParameter:
    """工具参数定义"""
    name: str
    type: str
    description: str = ""
    required: bool = False
    default: Any = None


@dataclass
class UnifiedTool:
    """统一工具定义"""
    name: str                    # 工具名称
    description: str             # 描述
    parameters: dict             # 参数 schema (JSON Schema 格式)
    source: ToolSource           # 来源类型
    source_name: str             # 来源名称 (skill名 / MCP服务器名)
    
    # 执行函数 (本地工具)
    handler: Optional[Callable] = None
    
    # 元数据
    requires_confirmation: bool = False
    confirm_message: str = ""
    dangerous: bool = False
    
    @property
    def full_name(self) -> str:
        """完整名称: source_name.tool_name"""
        return f"{self.source_name}.{self.name}"
    
    def to_openai_tool(self) -> dict:
        """转换为 OpenAI 工具格式"""
        return {
            "type": "function",
            "function": {
                "name": self.full_name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }


class UnifiedToolRegistry:
    """统一工具注册表
    
    管理来自不同来源的工具:
    - 内置技能包
    - 外部安装的技能包
    - MCP 服务器
    """
    
    def __init__(self):
        self._tools: dict[str, UnifiedTool] = {}
        self._skill_engine = None
        self._mcp_client = None
    
    def set_skill_engine(self, engine: Any) -> None:
        """设置技能引擎"""
        self._skill_engine = engine
    
    def set_mcp_client(self, client: Any) -> None:
        """设置 MCP 客户端"""
        self._mcp_client = client
    
    def register(self, tool: UnifiedTool) -> None:
        """注册工具"""
        self._tools[tool.full_name] = tool
    
    def unregister(self, full_name: str) -> None:
        """注销工具"""
        if full_name in self._tools:
            del self._tools[full_name]
    
    def get_tool(self, full_name: str) -> Optional[UnifiedTool]:
        """获取工具"""
        return self._tools.get(full_name)
    
    def list_tools(
        self,
        source: Optional[ToolSource] = None,
        source_name: Optional[str] = None,
    ) -> list[UnifiedTool]:
        """列出工具"""
        tools = list(self._tools.values())
        
        if source:
            tools = [t for t in tools if t.source == source]
        
        if source_name:
            tools = [t for t in tools if t.source_name == source_name]
        
        return tools
    
    async def execute(
        self,
        full_name: str,
        arguments: dict[str, Any],
        context: Optional[ToolContext] = None,
    ) -> ToolResult:
        """执行工具"""
        tool = self.get_tool(full_name)
        if not tool:
            return ToolResult.error_result(f"工具未找到: {full_name}")
        
        # 创建默认上下文
        if context is None:
            context = ToolContext()
        
        # 检查是否需要确认
        if tool.dangerous or tool.requires_confirmation:
            # TODO: 实现确认机制
            pass
        
        try:
            if tool.source == ToolSource.MCP:
                # MCP 工具
                if self._mcp_client is None:
                    return ToolResult.error_result("MCP 客户端未初始化")
                
                result = await self._mcp_client.call_tool(
                    tool.source_name,
                    tool.name,
                    arguments,
                )
                return ToolResult.success_result(data=result)
            
            elif tool.handler:
                # 本地工具
                result = await tool.handler(context, **arguments)
                if isinstance(result, ToolResult):
                    return result
                return ToolResult.success_result(data=result)
            
            else:
                return ToolResult.error_result(f"工具没有处理函数: {full_name}")
        
        except Exception as e:
            return ToolResult.error_result(f"工具执行错误: {str(e)}")
    
    def to_openai_tools(self) -> list[dict]:
        """转换为 OpenAI tools 格式"""
        return [tool.to_openai_tool() for tool in self._tools.values()]
    
    async def refresh(self) -> None:
        """刷新工具列表 (从技能引擎和 MCP 客户端)"""
        # 清空非内置工具
        self._tools = {
            k: v for k, v in self._tools.items()
            if v.source == ToolSource.BUILTIN
        }
        
        # 从技能引擎加载
        if self._skill_engine:
            for skill in self._skill_engine.list_skills():
                for tool_def in skill.get("tools", []):
                    tool = UnifiedTool(
                        name=tool_def["name"],
                        description=tool_def.get("description", ""),
                        parameters=tool_def.get("parameters", {}),
                        source=ToolSource.BUILTIN if skill.get("is_builtin") else ToolSource.EXTERNAL,
                        source_name=skill["name"],
                        dangerous=tool_def.get("dangerous", False),
                        requires_confirmation=tool_def.get("requires_confirmation", False),
                    )
                    self.register(tool)
        
        # 从 MCP 客户端加载
        if self._mcp_client:
            mcp_tools = await self._mcp_client.discover_tools()
            for mcp_tool in mcp_tools:
                tool = UnifiedTool(
                    name=mcp_tool.name,
                    description=mcp_tool.description,
                    parameters=mcp_tool.input_schema,
                    source=ToolSource.MCP,
                    source_name=mcp_tool.server_name,
                )
                self.register(tool)


# 全局注册表实例
_registry: Optional[UnifiedToolRegistry] = None


def get_tool_registry() -> UnifiedToolRegistry:
    """获取全局工具注册表"""
    global _registry
    if _registry is None:
        _registry = UnifiedToolRegistry()
    return _registry
