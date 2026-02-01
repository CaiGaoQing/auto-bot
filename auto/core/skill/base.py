"""技能包基类"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from auto.core.tool.result import ToolResult
from auto.core.tool.context import ToolContext


@dataclass
class ToolDefinition:
    """工具定义"""
    name: str
    description: str
    module: str = ""
    function: str = ""
    parameters: dict = field(default_factory=dict)
    dangerous: bool = False
    requires_confirmation: bool = False
    confirm_message: str = ""
    
    # 运行时绑定的处理函数
    handler: Optional[Callable] = None


@dataclass
class SkillDefinition:
    """技能定义"""
    name: str
    display_name: str
    version: str
    description: str
    category: str = "general"
    tags: list[str] = field(default_factory=list)
    roles: list[str] = field(default_factory=list)
    
    # 工具列表
    tools: list[ToolDefinition] = field(default_factory=list)
    
    # 依赖
    dependencies: dict = field(default_factory=dict)
    mcp_dependencies: list[dict] = field(default_factory=list)
    
    # 权限
    permissions: dict = field(default_factory=dict)
    
    # 安全限制
    security: dict = field(default_factory=dict)
    
    # 提示词
    system_prompt: str = ""
    
    # 输出格式
    output_formats: list[str] = field(default_factory=list)
    
    # 元数据
    is_builtin: bool = False
    is_enabled: bool = True
    install_path: str = ""


class Skill(ABC):
    """技能包抽象基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """技能名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """技能描述"""
        pass
    
    @property
    def version(self) -> str:
        """版本"""
        return "1.0.0"
    
    @property
    def display_name(self) -> str:
        """显示名称"""
        return self.name
    
    @property
    def category(self) -> str:
        """分类"""
        return "general"
    
    @property
    def tools(self) -> list[ToolDefinition]:
        """技能包含的工具列表"""
        return []
    
    @property
    def system_prompt(self) -> str:
        """系统提示词"""
        return ""
    
    def on_load(self) -> None:
        """技能加载时回调"""
        pass
    
    def on_unload(self) -> None:
        """技能卸载时回调"""
        pass
    
    def get_definition(self) -> SkillDefinition:
        """获取技能定义"""
        return SkillDefinition(
            name=self.name,
            display_name=self.display_name,
            version=self.version,
            description=self.description,
            category=self.category,
            tools=self.tools,
            system_prompt=self.system_prompt,
            is_builtin=True,
        )


class Tool(ABC):
    """工具抽象基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述"""
        pass
    
    @property
    def parameters(self) -> dict:
        """参数定义 (JSON Schema)"""
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }
    
    @property
    def dangerous(self) -> bool:
        """是否危险操作"""
        return False
    
    @property
    def requires_confirmation(self) -> bool:
        """是否需要用户确认"""
        return self.dangerous
    
    @abstractmethod
    async def execute(self, ctx: ToolContext, **params: Any) -> ToolResult:
        """执行工具"""
        pass
    
    def get_definition(self) -> ToolDefinition:
        """获取工具定义"""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=self.parameters,
            dangerous=self.dangerous,
            requires_confirmation=self.requires_confirmation,
            handler=self.execute,
        )
