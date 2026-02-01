"""技能引擎"""

from pathlib import Path
from typing import Any, Optional
import importlib
import yaml

from auto.core.skill.base import Skill, SkillDefinition, ToolDefinition
from auto.core.tool.context import ToolContext
from auto.core.tool.result import ToolResult
from auto.core.tool.registry import UnifiedToolRegistry, UnifiedTool, ToolSource


class SkillEngine:
    """技能引擎
    
    负责:
    - 加载技能包
    - 管理技能生命周期
    - 执行技能工具
    - 构建技能提示词
    """
    
    def __init__(self, skills_dir: Optional[Path] = None):
        self._skills: dict[str, SkillDefinition] = {}
        self._tool_handlers: dict[str, Any] = {}  # skill.tool -> handler
        self._skills_dir = skills_dir or Path(__file__).parent.parent.parent / "skills"
        self._registry: Optional[UnifiedToolRegistry] = None
    
    def set_registry(self, registry: UnifiedToolRegistry) -> None:
        """设置工具注册表"""
        self._registry = registry
    
    def load_skill(self, skill_path: Path | str) -> Optional[SkillDefinition]:
        """加载技能包
        
        Args:
            skill_path: 技能包路径 (包含 skill.yaml)
        
        Returns:
            SkillDefinition: 技能定义
        """
        skill_path = Path(skill_path)
        config_file = skill_path / "skill.yaml"
        
        if not config_file.exists():
            return None
        
        # 读取配置
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        # 解析工具定义
        tools = []
        for tool_config in config.get("tools", []):
            tool_def = ToolDefinition(
                name=tool_config["name"],
                description=tool_config.get("description", ""),
                module=tool_config.get("module", ""),
                function=tool_config.get("function", ""),
                parameters=tool_config.get("parameters", {}),
                dangerous=tool_config.get("dangerous", False),
                requires_confirmation=tool_config.get("requires_confirmation", False),
                confirm_message=tool_config.get("confirm_message", ""),
            )
            tools.append(tool_def)
            
            # 尝试加载处理函数
            if tool_def.module and tool_def.function:
                try:
                    module = importlib.import_module(
                        f"auto.skills.{skill_path.name}.{tool_def.module}"
                    )
                    handler = getattr(module, tool_def.function, None)
                    if handler:
                        tool_def.handler = handler
                        self._tool_handlers[f"{config['name']}.{tool_def.name}"] = handler
                except (ImportError, AttributeError):
                    pass
        
        # 创建技能定义
        skill_def = SkillDefinition(
            name=config["name"],
            display_name=config.get("display_name", config["name"]),
            version=config.get("version", "1.0.0"),
            description=config.get("description", ""),
            category=config.get("category", "general"),
            tags=config.get("tags", []),
            roles=config.get("roles", []),
            tools=tools,
            dependencies=config.get("dependencies", {}),
            mcp_dependencies=config.get("mcp_dependencies", []),
            permissions=config.get("permissions", {}),
            security=config.get("security", {}),
            system_prompt=config.get("system_prompt", ""),
            output_formats=config.get("output_formats", []),
            is_builtin=str(skill_path).startswith(str(self._skills_dir / "builtin")),
            is_enabled=True,
            install_path=str(skill_path),
        )
        
        self._skills[skill_def.name] = skill_def
        
        # 注册到工具注册表
        if self._registry:
            self._register_tools(skill_def)
        
        return skill_def
    
    def _register_tools(self, skill_def: SkillDefinition) -> None:
        """注册技能工具到注册表"""
        if not self._registry:
            return
        
        for tool_def in skill_def.tools:
            # 转换参数格式
            parameters = tool_def.parameters
            if not isinstance(parameters, dict):
                parameters = {"type": "object", "properties": {}}
            elif "type" not in parameters:
                # 转换列表格式为 JSON Schema
                parameters = self._convert_parameters(tool_def.parameters)
            
            tool = UnifiedTool(
                name=tool_def.name,
                description=tool_def.description,
                parameters=parameters,
                source=ToolSource.BUILTIN if skill_def.is_builtin else ToolSource.EXTERNAL,
                source_name=skill_def.name,
                handler=tool_def.handler,
                dangerous=tool_def.dangerous,
                requires_confirmation=tool_def.requires_confirmation,
                confirm_message=tool_def.confirm_message,
            )
            self._registry.register(tool)
    
    def _convert_parameters(self, params: Any) -> dict:
        """转换参数格式为 JSON Schema"""
        if isinstance(params, list):
            properties = {}
            required = []
            
            for param in params:
                name = param.get("name", "")
                if not name:
                    continue
                
                properties[name] = {
                    "type": param.get("type", "string"),
                    "description": param.get("description", ""),
                }
                
                if param.get("default") is not None:
                    properties[name]["default"] = param["default"]
                
                if param.get("required", False):
                    required.append(name)
            
            return {
                "type": "object",
                "properties": properties,
                "required": required,
            }
        
        return params
    
    def load_builtin_skills(self) -> None:
        """加载内置技能包"""
        builtin_dir = self._skills_dir / "builtin"
        if not builtin_dir.exists():
            return
        
        for skill_dir in builtin_dir.iterdir():
            if skill_dir.is_dir() and (skill_dir / "skill.yaml").exists():
                self.load_skill(skill_dir)
    
    def load_external_skills(self) -> None:
        """加载外部安装的技能包"""
        external_dir = self._skills_dir / "external"
        if not external_dir.exists():
            return
        
        for skill_dir in external_dir.iterdir():
            if skill_dir.is_dir() and (skill_dir / "skill.yaml").exists():
                self.load_skill(skill_dir)
    
    def register_skill(self, skill: Skill) -> None:
        """注册 Python 技能类"""
        skill_def = skill.get_definition()
        self._skills[skill_def.name] = skill_def
        
        # 注册工具处理函数
        for tool_def in skill_def.tools:
            if tool_def.handler:
                self._tool_handlers[f"{skill_def.name}.{tool_def.name}"] = tool_def.handler
        
        # 注册到工具注册表
        if self._registry:
            self._register_tools(skill_def)
        
        # 调用加载回调
        skill.on_load()
    
    def unload_skill(self, skill_name: str) -> None:
        """卸载技能"""
        if skill_name not in self._skills:
            return
        
        skill_def = self._skills[skill_name]
        
        # 移除工具处理函数
        for tool_def in skill_def.tools:
            key = f"{skill_name}.{tool_def.name}"
            if key in self._tool_handlers:
                del self._tool_handlers[key]
            
            # 从注册表移除
            if self._registry:
                self._registry.unregister(key)
        
        del self._skills[skill_name]
    
    def get_skill(self, name: str) -> Optional[SkillDefinition]:
        """获取技能"""
        return self._skills.get(name)
    
    def list_skills(self) -> list[dict]:
        """列出所有技能"""
        return [
            {
                "name": s.name,
                "display_name": s.display_name,
                "version": s.version,
                "description": s.description,
                "category": s.category,
                "is_builtin": s.is_builtin,
                "is_enabled": s.is_enabled,
                "tools": [{"name": t.name, "description": t.description} for t in s.tools],
            }
            for s in self._skills.values()
        ]
    
    async def execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        context: Optional[ToolContext] = None,
    ) -> ToolResult:
        """执行工具
        
        Args:
            tool_name: 工具名称 (格式: skill_name.tool_name)
            arguments: 工具参数
            context: 执行上下文
        
        Returns:
            ToolResult: 执行结果
        """
        handler = self._tool_handlers.get(tool_name)
        if not handler:
            return ToolResult.error_result(f"工具未找到: {tool_name}")
        
        if context is None:
            context = ToolContext()
        
        try:
            result = await handler(context, **arguments)
            if isinstance(result, ToolResult):
                return result
            return ToolResult.success_result(data=result)
        except Exception as e:
            return ToolResult.error_result(f"工具执行错误: {str(e)}")
    
    def get_system_prompt(self, skill_name: str) -> str:
        """获取技能系统提示词"""
        skill = self._skills.get(skill_name)
        if skill:
            return skill.system_prompt
        return ""
    
    def get_tools_for_skill(self, skill_name: str) -> list[dict]:
        """获取技能的工具列表 (OpenAI 格式)"""
        skill = self._skills.get(skill_name)
        if not skill:
            return []
        
        tools = []
        for tool_def in skill.tools:
            parameters = tool_def.parameters
            if not isinstance(parameters, dict):
                parameters = self._convert_parameters(parameters)
            
            tools.append({
                "type": "function",
                "function": {
                    "name": f"{skill_name}.{tool_def.name}",
                    "description": tool_def.description,
                    "parameters": parameters,
                }
            })
        
        return tools


# 全局引擎实例
_engine: Optional[SkillEngine] = None


def get_skill_engine() -> SkillEngine:
    """获取全局技能引擎"""
    global _engine
    if _engine is None:
        _engine = SkillEngine()
    return _engine
