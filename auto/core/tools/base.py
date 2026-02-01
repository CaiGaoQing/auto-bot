"""
工具基类

定义工具的基本接口和结果类型
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class ToolResultType(str, Enum):
    """工具结果类型"""
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"


@dataclass
class ToolResult:
    """
    工具执行结果
    
    OpenClaw 风格：工具返回结构化结果，AI 可以理解并继续操作
    """
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    
    # 生成的文件列表
    files_created: List[str] = field(default_factory=list)
    
    # 错误信息
    error: Optional[str] = None
    error_code: Optional[str] = None
    
    # 下一步建议（AI 可以参考）
    suggestions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "files_created": self.files_created,
            "error": self.error,
            "suggestions": self.suggestions,
        }
    
    def to_ai_message(self) -> str:
        """转换为 AI 可理解的消息格式"""
        if self.success:
            msg = f"✅ {self.message}"
            if self.files_created:
                msg += f"\n\n已创建的文件:\n"
                for f in self.files_created:
                    msg += f"  - {f}\n"
            if self.data:
                msg += f"\n详情: {self.data}"
        else:
            msg = f"❌ 操作失败: {self.error or self.message}"
            if self.suggestions:
                msg += "\n\n建议:\n"
                for s in self.suggestions:
                    msg += f"  - {s}\n"
        return msg


@dataclass
class ToolParameter:
    """工具参数定义"""
    name: str
    description: str
    type: str  # string, number, boolean, array, object
    required: bool = True
    default: Any = None
    enum: Optional[List[Any]] = None


class BaseTool(ABC):
    """
    工具基类
    
    所有工具都需要实现这个接口
    """
    
    # 工具名称（唯一标识）
    name: str = ""
    
    # 工具显示名称
    display_name: str = ""
    
    # 工具描述（给 AI 看的）
    description: str = ""
    
    # 工具分类
    category: str = "general"
    
    # 工具参数
    parameters: List[ToolParameter] = []
    
    def __init__(self, workspace_id: Optional[str] = None):
        """
        初始化工具
        
        Args:
            workspace_id: 工作空间 ID（如果需要文件操作）
        """
        self.workspace_id = workspace_id
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        执行工具
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            ToolResult: 执行结果
        """
        pass
    
    def get_schema(self) -> dict:
        """
        获取 OpenAI function calling 格式的 schema
        
        这是 AI 调用工具时需要的格式
        """
        properties = {}
        required = []
        
        for param in self.parameters:
            prop = {
                "type": param.type,
                "description": param.description,
            }
            if param.enum:
                prop["enum"] = param.enum
            if param.default is not None:
                prop["default"] = param.default
            
            properties[param.name] = prop
            
            if param.required:
                required.append(param.name)
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                }
            }
        }
    
    def validate_params(self, **kwargs) -> Optional[str]:
        """验证参数"""
        for param in self.parameters:
            if param.required and param.name not in kwargs:
                return f"缺少必填参数: {param.name}"
        return None
