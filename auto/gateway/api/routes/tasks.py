"""任务 API - 简化的移动端友好接口

移动端工作流程:
1. POST /api/v1/tasks/process - 上传文件 + 任务描述 → 返回结果和下载链接
2. GET /api/v1/tasks/{task_id}/files/{filename} - 下载生成的文件
"""

import os
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel

from auto.core.task import TaskExecutor, TaskResult, OutputFormat

router = APIRouter()

# 任务存储目录
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
TASKS_ROOT = _PROJECT_ROOT / "data" / "tasks"
TASKS_ROOT.mkdir(parents=True, exist_ok=True)

# 任务状态存储
task_status: dict[str, dict] = {}


def generate_task_id() -> str:
    """生成任务 ID"""
    import hashlib
    import time
    return f"task_{hashlib.md5(str(time.time()).encode()).hexdigest()[:12]}"


class TaskResponse(BaseModel):
    """任务响应"""
    code: int = 0
    message: str = "success"
    data: dict


@router.post("/tasks/process")
async def process_task(
    task: str = Form(..., description="任务描述，如：分析这份财报"),
    output_format: str = Form("md", description="输出格式: md/xlsx/pptx/pdf/json"),
    files: List[UploadFile] = File(default=[], description="要处理的文件"),
) -> TaskResponse:
    """
    处理任务 - 一体化接口
    
    移动端只需调用这一个接口:
    - 上传文件（可选）
    - 指定任务描述
    - 指定输出格式
    - 返回处理结果和下载链接
    """
    # 生成任务 ID
    task_id = generate_task_id()
    task_path = TASKS_ROOT / task_id
    task_path.mkdir(parents=True, exist_ok=True)
    
    # 保存上传的文件
    input_files = []
    for file in files:
        if file.filename:
            safe_filename = file.filename.replace("/", "_").replace("\\", "_")
            file_path = task_path / "files" / safe_filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            content = await file.read()
            file_path.write_bytes(content)
            input_files.append(safe_filename)
    
    # 解析输出格式
    try:
        fmt = OutputFormat(output_format.lower())
    except ValueError:
        fmt = OutputFormat.MARKDOWN
    
    # 执行任务
    executor = TaskExecutor(task_path)
    result = await executor.execute(
        task=task,
        input_files=input_files,
        output_format=fmt,
    )
    
    if not result.success:
        return TaskResponse(
            code=500,
            message=result.message,
            data={
                "task_id": task_id,
                "error": result.error,
            }
        )
    
    # 构建下载链接
    download_files = []
    for file_info in result.output_files:
        download_files.append({
            "name": file_info["name"],
            "size": file_info["size"],
            "type": file_info["type"],
            "download_url": f"/api/v1/tasks/{task_id}/files/{file_info['name']}",
        })
    
    return TaskResponse(
        data={
            "task_id": task_id,
            "status": "completed",
            "message": result.message,
            "content_preview": result.content,  # 文本预览
            "files": download_files,  # 下载链接列表
        }
    )


@router.post("/tasks/process-async")
async def process_task_async(
    background_tasks: BackgroundTasks,
    task: str = Form(..., description="任务描述"),
    output_format: str = Form("md", description="输出格式"),
    files: List[UploadFile] = File(default=[], description="要处理的文件"),
) -> TaskResponse:
    """
    异步处理任务 - 适合长时间任务
    
    返回任务 ID，通过 GET /tasks/{task_id}/status 查询状态
    """
    # 生成任务 ID
    task_id = generate_task_id()
    task_path = TASKS_ROOT / task_id
    task_path.mkdir(parents=True, exist_ok=True)
    
    # 保存上传的文件
    input_files = []
    for file in files:
        if file.filename:
            safe_filename = file.filename.replace("/", "_").replace("\\", "_")
            file_path = task_path / "files" / safe_filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            content = await file.read()
            file_path.write_bytes(content)
            input_files.append(safe_filename)
    
    # 初始化状态
    task_status[task_id] = {
        "task_id": task_id,
        "status": "processing",
        "task": task,
        "output_format": output_format,
        "started_at": datetime.now().isoformat(),
        "files": [],
    }
    
    # 在后台执行
    background_tasks.add_task(
        _execute_task_background,
        task_id,
        task_path,
        task,
        input_files,
        output_format,
    )
    
    return TaskResponse(
        data={
            "task_id": task_id,
            "status": "processing",
            "message": "任务已提交，正在处理中",
            "status_url": f"/api/v1/tasks/{task_id}/status",
        }
    )


async def _execute_task_background(
    task_id: str,
    task_path: Path,
    task: str,
    input_files: List[str],
    output_format: str,
):
    """后台执行任务"""
    try:
        fmt = OutputFormat(output_format.lower())
    except ValueError:
        fmt = OutputFormat.MARKDOWN
    
    executor = TaskExecutor(task_path)
    result = await executor.execute(
        task=task,
        input_files=input_files,
        output_format=fmt,
    )
    
    # 更新状态
    if result.success:
        download_files = []
        for file_info in result.output_files:
            download_files.append({
                "name": file_info["name"],
                "size": file_info["size"],
                "type": file_info["type"],
                "download_url": f"/api/v1/tasks/{task_id}/files/{file_info['name']}",
            })
        
        task_status[task_id] = {
            "task_id": task_id,
            "status": "completed",
            "message": result.message,
            "content_preview": result.content,
            "files": download_files,
            "completed_at": datetime.now().isoformat(),
        }
    else:
        task_status[task_id] = {
            "task_id": task_id,
            "status": "failed",
            "message": result.message,
            "error": result.error,
            "failed_at": datetime.now().isoformat(),
        }


@router.get("/tasks/{task_id}/status")
async def get_task_status(task_id: str) -> TaskResponse:
    """获取任务状态"""
    if task_id not in task_status:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return TaskResponse(data=task_status[task_id])


@router.get("/tasks/{task_id}/files/{filename}")
async def download_task_file(task_id: str, filename: str):
    """下载任务生成的文件"""
    task_path = TASKS_ROOT / task_id / "outputs" / filename
    
    if not task_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 根据文件类型设置 Content-Type
    content_types = {
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".pdf": "application/pdf",
        ".json": "application/json",
        ".md": "text/markdown",
    }
    
    suffix = Path(filename).suffix.lower()
    media_type = content_types.get(suffix, "application/octet-stream")
    
    return FileResponse(
        path=task_path,
        filename=filename,
        media_type=media_type,
    )


@router.get("/tasks")
async def list_tasks(limit: int = 20) -> TaskResponse:
    """列出最近的任务"""
    tasks = []
    
    if TASKS_ROOT.exists():
        for task_dir in sorted(TASKS_ROOT.iterdir(), reverse=True)[:limit]:
            if task_dir.is_dir():
                task_id = task_dir.name
                outputs_path = task_dir / "outputs"
                
                files = []
                if outputs_path.exists():
                    for f in outputs_path.glob("*"):
                        if f.is_file():
                            files.append({
                                "name": f.name,
                                "size": f.stat().st_size,
                                "download_url": f"/api/v1/tasks/{task_id}/files/{f.name}",
                            })
                
                tasks.append({
                    "task_id": task_id,
                    "files": files,
                    "created_at": datetime.fromtimestamp(task_dir.stat().st_ctime).isoformat(),
                })
    
    return TaskResponse(
        data={
            "items": tasks,
            "total": len(tasks),
        }
    )
