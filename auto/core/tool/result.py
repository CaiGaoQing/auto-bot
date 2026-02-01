"""工具执行结果"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ToolResult:
    """工具执行结果"""
    
    success: bool
    data: Any = None
    message: str = ""
    error: Optional[str] = None
    
    # 输出建议
    output_type: str = "text"  # text, table, file, chart, image, code
    output_format: Optional[str] = None  # json, csv, xlsx, pdf, etc.
    
    # 元数据
    metadata: dict = field(default_factory=dict)
    
    @classmethod
    def success_result(
        cls,
        data: Any = None,
        message: str = "",
        output_type: str = "text",
        output_format: Optional[str] = None,
    ) -> "ToolResult":
        """创建成功结果"""
        return cls(
            success=True,
            data=data,
            message=message,
            output_type=output_type,
            output_format=output_format,
        )
    
    @classmethod
    def error_result(cls, error: str) -> "ToolResult":
        """创建错误结果"""
        return cls(
            success=False,
            error=error,
        )
    
    @classmethod
    def table(cls, data: list[dict], message: str = "") -> "ToolResult":
        """创建表格结果"""
        return cls(
            success=True,
            data=data,
            message=message,
            output_type="table",
        )
    
    @classmethod
    def file(cls, path: str, message: str = "") -> "ToolResult":
        """创建文件结果"""
        return cls(
            success=True,
            data={"path": path},
            message=message,
            output_type="file",
        )
    
    @classmethod
    def code(cls, content: str, language: str = "python", message: str = "") -> "ToolResult":
        """创建代码结果"""
        return cls(
            success=True,
            data={"content": content, "language": language},
            message=message,
            output_type="code",
        )
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "success": self.success,
            "data": self.data,
            "message": self.message,
            "error": self.error,
            "output_type": self.output_type,
            "output_format": self.output_format,
            "metadata": self.metadata,
        }
