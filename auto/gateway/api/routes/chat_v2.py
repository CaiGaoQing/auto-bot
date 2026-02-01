"""
对话路由 V2 - OpenClaw 风格

核心设计思想：
1. AI 通过工具调用来执行操作，而不是我们解析 AI 输出
2. 工具是可扩展的，新功能通过添加工具实现
3. AI 决定调用什么工具，而不是代码硬编码判断
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from auto.core.ai.router import get_router
from auto.core.tools import get_tool_registry, ToolResult
from auto.shared.models import Message, MessageRole

router = APIRouter()

# 工作空间根目录
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
WORKSPACES_ROOT = _PROJECT_ROOT / "data" / "workspaces"


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    model: Optional[str] = None
    workspace_id: Optional[str] = None
    role: Optional[str] = None
    stream: bool = False
    enable_tools: bool = True  # 是否启用工具调用


class ToolCallInfo(BaseModel):
    """工具调用信息"""
    name: str
    arguments: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """聊天响应"""
    code: int = 0
    message: str = "success"
    data: dict


def _build_system_prompt(workspace_id: Optional[str] = None) -> str:
    """
    构建系统提示词
    
    OpenClaw 风格：告诉 AI 它有哪些能力，让 AI 自己决定如何使用
    """
    base_prompt = """你是一个强大的 AI 助手，可以帮助用户完成各种任务。

你有以下能力：
1. **创建文件** - 使用 create_file 工具在工作空间创建代码、配置、文档等文件
2. **创建代码项目** - 使用 save_code_project 工具批量创建完整的代码项目
3. **生成 PPT** - 使用 generate_ppt 工具创建演示文稿
4. **生成 Excel** - 使用 generate_excel 工具创建表格

重要原则：
- 当用户要求生成代码、文件时，使用对应的工具来创建文件
- 当用户只是询问问题时，直接回答，不需要创建文件
- 创建代码时，确保代码是完整可运行的
- 创建项目时，包含必要的配置文件和目录结构
"""
    
    # 如果有工作空间，读取工作空间上下文
    if workspace_id:
        workspace_path = WORKSPACES_ROOT / workspace_id
        if workspace_path.exists():
            context = _read_workspace_context(workspace_path)
            if context:
                base_prompt += f"\n\n当前工作空间内容:\n{context}"
    
    return base_prompt


def _read_workspace_context(workspace_path: Path, max_files: int = 20) -> str:
    """读取工作空间上下文"""
    context_parts = []
    files_read = 0
    
    # 读取文件扩展名
    readable_exts = {'.md', '.txt', '.json', '.yaml', '.yml', '.sql', '.java', '.py', '.js', '.ts'}
    skip_dirs = {'node_modules', '.git', '__pycache__', 'venv', 'dist', 'build'}
    
    for file_path in workspace_path.rglob('*'):
        if files_read >= max_files:
            break
        
        if not file_path.is_file():
            continue
        
        # 跳过特定目录
        if any(skip_dir in file_path.parts for skip_dir in skip_dirs):
            continue
        
        # 只读取指定扩展名
        if file_path.suffix.lower() not in readable_exts:
            continue
        
        try:
            content = file_path.read_text(encoding='utf-8')
            if len(content) > 2000:
                content = content[:2000] + "\n... (内容已截断)"
            
            relative_path = file_path.relative_to(workspace_path)
            context_parts.append(f"### {relative_path}\n```\n{content}\n```")
            files_read += 1
        except:
            continue
    
    if context_parts:
        return "\n\n".join(context_parts)
    return ""


@router.post("/chat/v2")
async def chat_v2(request: ChatRequest) -> ChatResponse:
    """
    V2 聊天接口 - OpenClaw 风格
    
    使用工具调用让 AI 执行操作
    """
    try:
        router_instance = get_router()
        tool_registry = get_tool_registry()
        
        # 构建系统提示
        system_prompt = _build_system_prompt(request.workspace_id)
        
        # 构建消息
        messages = [
            Message(role=MessageRole.SYSTEM, content=system_prompt),
            Message(role=MessageRole.USER, content=request.message),
        ]
        
        # 获取工具 schema（如果启用工具）
        tools = []
        if request.enable_tools and request.workspace_id:
            tools = tool_registry.get_all_schemas(request.workspace_id)
        
        # 调用 AI（带工具调用）
        response = await router_instance.chat(
            messages=messages,
            model=request.model,
            tools=tools if tools else None,
        )
        
        content = response.message.content
        tool_calls_info = []
        files_created = []
        
        # 处理工具调用
        if hasattr(response.message, 'tool_calls') and response.message.tool_calls:
            for tool_call in response.message.tool_calls:
                tool_name = tool_call.function.name
                try:
                    arguments = json.loads(tool_call.function.arguments)
                except:
                    arguments = {}
                
                # 执行工具
                result = await tool_registry.execute(
                    tool_name=tool_name,
                    workspace_id=request.workspace_id,
                    **arguments
                )
                
                tool_calls_info.append({
                    "name": tool_name,
                    "arguments": arguments,
                    "result": result.to_dict(),
                })
                
                # 收集创建的文件
                files_created.extend(result.files_created)
                
                # 如果有工具调用结果，追加到内容
                if result.success:
                    content += f"\n\n{result.to_ai_message()}"
        
        return ChatResponse(
            data={
                "id": response.id,
                "content": content,
                "model": response.model,
                "tool_calls": tool_calls_info if tool_calls_info else None,
                "files_created": files_created if files_created else None,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                } if response.usage else None,
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools")
async def list_tools() -> dict:
    """
    列出所有可用工具
    """
    tool_registry = get_tool_registry()
    tools = tool_registry.list_tools()
    
    return {
        "code": 0,
        "message": "success",
        "data": {
            "tools": [
                {
                    "name": t.name,
                    "category": t.category,
                    "enabled": t.enabled,
                }
                for t in tools
            ],
            "categories": tool_registry.get_categories(),
        }
    }


@router.get("/tools/{tool_name}/schema")
async def get_tool_schema(tool_name: str) -> dict:
    """
    获取工具 schema
    """
    tool_registry = get_tool_registry()
    tool = tool_registry.get_tool(tool_name)
    
    if not tool:
        raise HTTPException(status_code=404, detail=f"工具不存在: {tool_name}")
    
    return {
        "code": 0,
        "message": "success",
        "data": tool.get_schema(),
    }
