"""工具执行上下文"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional
import logging


@dataclass
class SecurityChecker:
    """安全检查器"""
    
    allowed_paths: list[str] = field(default_factory=list)
    blocked_paths: list[str] = field(default_factory=lambda: ["/", "/etc", "/usr", "~/.ssh"])
    dangerous_operations: list[str] = field(default_factory=lambda: ["rm -rf", "DROP", "DELETE FROM"])
    
    def is_allowed_path(self, path: str | Path) -> bool:
        """检查路径是否在允许范围内"""
        path = Path(path).expanduser().resolve()
        
        # 检查是否在禁止列表
        for blocked in self.blocked_paths:
            blocked_path = Path(blocked).expanduser().resolve()
            try:
                path.relative_to(blocked_path)
                return False
            except ValueError:
                continue
        
        # 如果有允许列表，检查是否在允许列表
        if self.allowed_paths:
            for allowed in self.allowed_paths:
                allowed_path = Path(allowed).expanduser().resolve()
                try:
                    path.relative_to(allowed_path)
                    return True
                except ValueError:
                    continue
            return False
        
        return True
    
    def is_dangerous_operation(self, operation: str) -> bool:
        """检查是否是危险操作"""
        operation_lower = operation.lower()
        for dangerous in self.dangerous_operations:
            if dangerous.lower() in operation_lower:
                return True
        return False
    
    def check_permission(self, permission: str) -> bool:
        """检查权限"""
        # TODO: 实现权限检查
        return True


@dataclass
class ProgressReporter:
    """进度报告器"""
    
    callback: Optional[Callable[[int, int, str], None]] = None
    
    def update(self, current: int, total: int, message: str = "") -> None:
        """更新进度"""
        if self.callback:
            self.callback(current, total, message)


@dataclass
class ToolContext:
    """工具执行上下文"""
    
    # 工作空间信息
    workspace_id: str = ""
    workspace_path: Path = field(default_factory=lambda: Path.cwd())
    
    # 用户信息
    user_id: str = ""
    role: str = "general"
    
    # 会话信息
    conversation_id: str = ""
    message_id: str = ""
    
    # 安全检查器
    security: SecurityChecker = field(default_factory=SecurityChecker)
    
    # 配置
    config: dict[str, Any] = field(default_factory=dict)
    
    # 全局记忆 (只读)
    memories: list[Any] = field(default_factory=list)
    
    # 日志记录器
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger("auto.tool"))
    
    # 进度报告
    progress: ProgressReporter = field(default_factory=ProgressReporter)
    
    # MCP 客户端 (用于调用 MCP 工具)
    mcp_client: Any = None
    
    # 技能引擎 (用于调用其他技能)
    skill_engine: Any = None
    
    def report_progress(self, current: int, total: int, message: str = "") -> None:
        """报告进度"""
        self.progress.update(current, total, message)
    
    def log(self, level: str, message: str, **kwargs: Any) -> None:
        """记录日志"""
        log_func = getattr(self.logger, level.lower(), self.logger.info)
        log_func(message, extra=kwargs)
    
    async def call_tool(self, tool_name: str, **arguments: Any) -> Any:
        """调用其他工具"""
        if self.skill_engine:
            return await self.skill_engine.execute_tool(tool_name, arguments, self)
        raise RuntimeError("技能引擎未初始化")
    
    async def call_mcp_tool(
        self,
        server: str,
        tool: str,
        arguments: dict[str, Any],
    ) -> Any:
        """调用 MCP 工具"""
        if self.mcp_client:
            return await self.mcp_client.call_tool(server, tool, arguments)
        raise RuntimeError("MCP 客户端未初始化")
