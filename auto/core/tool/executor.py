"""工具执行器"""

from typing import Any, Optional

from auto.core.tool.context import ToolContext
from auto.core.tool.registry import UnifiedToolRegistry, get_tool_registry
from auto.core.tool.result import ToolResult


class ToolExecutor:
    """工具执行器
    
    负责:
    - 执行工具
    - 权限检查
    - 确认机制
    - 结果处理
    """
    
    def __init__(self, registry: Optional[UnifiedToolRegistry] = None):
        self.registry = registry or get_tool_registry()
    
    async def execute(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        context: Optional[ToolContext] = None,
        skip_confirmation: bool = False,
    ) -> ToolResult:
        """执行工具
        
        Args:
            tool_name: 工具名称 (格式: skill_name.tool_name)
            arguments: 工具参数
            context: 执行上下文
            skip_confirmation: 跳过确认
        
        Returns:
            ToolResult: 执行结果
        """
        tool = self.registry.get_tool(tool_name)
        if not tool:
            return ToolResult.error_result(f"工具未找到: {tool_name}")
        
        # 创建默认上下文
        if context is None:
            context = ToolContext()
        
        # 安全检查
        if tool.dangerous:
            # 检查是否有危险操作
            for key, value in arguments.items():
                if isinstance(value, str):
                    if context.security.is_dangerous_operation(value):
                        return ToolResult.error_result(
                            f"检测到危险操作: {value}"
                        )
        
        # 确认机制
        if not skip_confirmation and (tool.dangerous or tool.requires_confirmation):
            # 在 CLI 模式下，这里应该返回待确认状态
            # 实际确认由调用方处理
            pass
        
        # 执行工具
        return await self.registry.execute(tool_name, arguments, context)
    
    async def execute_tool_calls(
        self,
        tool_calls: list[dict],
        context: Optional[ToolContext] = None,
    ) -> list[dict]:
        """执行多个工具调用 (OpenAI 格式)
        
        Args:
            tool_calls: OpenAI 格式的工具调用列表
            context: 执行上下文
        
        Returns:
            list[dict]: 工具响应列表
        """
        import json
        
        results = []
        
        for call in tool_calls:
            call_id = call.get("id", "")
            function = call.get("function", {})
            name = function.get("name", "")
            arguments_str = function.get("arguments", "{}")
            
            try:
                arguments = json.loads(arguments_str)
            except json.JSONDecodeError:
                arguments = {}
            
            result = await self.execute(name, arguments, context)
            
            results.append({
                "tool_call_id": call_id,
                "role": "tool",
                "name": name,
                "content": json.dumps(result.to_dict(), ensure_ascii=False),
            })
        
        return results
    
    def list_available_tools(self) -> list[dict]:
        """列出可用工具 (OpenAI 格式)"""
        return self.registry.to_openai_tools()


# 全局执行器实例
_executor: Optional[ToolExecutor] = None


def get_tool_executor() -> ToolExecutor:
    """获取全局工具执行器"""
    global _executor
    if _executor is None:
        _executor = ToolExecutor()
    return _executor
