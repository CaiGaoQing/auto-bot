"""
对话路由 - OpenClaw 风格

核心设计：让 AI 决定做什么，不硬编码判断
"""

import json
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from auto.core.ai.router import get_router
from auto.core.tools import get_tool_registry
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
    save_to_workspace: bool = True


class ChatResponse(BaseModel):
    """聊天响应"""
    code: int = 0
    message: str = "success"
    data: dict


def _build_system_prompt(workspace_id: Optional[str] = None) -> str:
    """
    构建系统提示词
    
    告诉 AI 它有什么工具可用，让 AI 自己决定是否使用
    """
    prompt = """你是一个强大的 AI 助手。

## 你的能力

当用户需要创建文件时，你可以使用以下工具：

1. **create_file** - 创建单个文件
   - 用于：代码文件、SQL脚本、配置文件、文档等
   - 参数：filepath（文件路径）, content（内容）, folder（可选：code/scripts/docs/data）

2. **save_code_project** - 创建代码项目（多个文件）
   - 用于：SpringBoot项目、React项目等完整项目
   - 参数：project_name, files（文件列表）

3. **generate_ppt** - 生成 PPT 演示文稿
   - 用于：汇报PPT、产品介绍等
   - 参数：title, slides（幻灯片列表）

4. **generate_excel** - 生成 Excel 表格
   - 用于：数据表、报表等
   - 参数：title, headers, rows

## 使用原则

- 用户要求"生成"、"创建"、"写"文件时 → 调用对应工具
- 用户只是提问、询问时 → 直接回答，不调用工具
- 你来判断是否需要创建文件，不需要询问用户"""
    
    # 读取工作空间上下文
    if workspace_id:
        context = _read_workspace_context(workspace_id)
        if context:
            prompt += f"\n\n## 当前工作空间内容\n\n{context}"
    
    return prompt


def _read_workspace_context(workspace_id: str, max_files: int = 20) -> str:
    """读取工作空间上下文"""
    workspace_path = WORKSPACES_ROOT / workspace_id
    if not workspace_path.exists():
        return ""
    
    context_parts = []
    files_read = 0
    
    readable_exts = {'.md', '.txt', '.json', '.yaml', '.yml', '.sql', '.java', '.py', '.js', '.ts', '.xml'}
    skip_dirs = {'node_modules', '.git', '__pycache__', 'venv', 'dist', 'build', '.idea'}
    
    for file_path in workspace_path.rglob('*'):
        if files_read >= max_files:
            break
        
        if not file_path.is_file():
            continue
        
        if any(skip_dir in file_path.parts for skip_dir in skip_dirs):
            continue
        
        if file_path.suffix.lower() not in readable_exts:
            continue
        
        try:
            content = file_path.read_text(encoding='utf-8')
            if len(content) > 3000:
                content = content[:3000] + "\n... (已截断)"
            
            relative_path = file_path.relative_to(workspace_path)
            context_parts.append(f"### {relative_path}\n```\n{content}\n```")
            files_read += 1
        except:
            continue
    
    return "\n\n".join(context_parts) if context_parts else ""


@router.post("/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    """
    聊天接口 - OpenClaw 风格
    
    让 AI 通过工具调用来执行操作
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
        
        # 获取工具（如果有工作空间）
        tools = None
        if request.workspace_id and request.save_to_workspace:
            tools = tool_registry.get_all_schemas(request.workspace_id)
        
        # 调用 AI
        response = await router_instance.chat(
            messages=messages,
            model=request.model,
            tools=tools,
        )
        
        content = response.message.content or ""
        files_created = []
        tool_calls_info = []
        
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
                    "tool": tool_name,
                    "success": result.success,
                    "message": result.message,
                })
                
                files_created.extend(result.files_created)
                
                # 追加工具执行结果到内容
                if result.success and result.files_created:
                    content += f"\n\n📄 **已保存到**: {', '.join(result.files_created)}"
        
        return ChatResponse(
            data={
                "id": response.id,
                "content": content,
                "model": response.model,
                "saved_file": ", ".join(files_created) if files_created else None,
                "file_type": None,  # 不再硬编码判断
                "tool_calls": tool_calls_info if tool_calls_info else None,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                },
            }
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: str,
    request: ChatRequest,
) -> ChatResponse:
    """在会话中发送消息"""
    return await chat(request)
