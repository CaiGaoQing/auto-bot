"""定时任务 API 路由"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from auto.core.scheduler import get_scheduler, Task, ScheduleType

router = APIRouter()


class TaskCreate(BaseModel):
    """创建任务请求"""
    name: str
    command: str
    schedule_type: str = "daily"
    interval_seconds: Optional[int] = None
    cron_expression: Optional[str] = None
    run_at: Optional[str] = None
    run_on: Optional[list[int]] = None
    enabled: bool = True


class TaskResponse(BaseModel):
    """任务响应"""
    code: int = 0
    message: str = "success"
    data: dict = {}


@router.get("/scheduler/tasks")
async def list_tasks() -> TaskResponse:
    """列出所有任务"""
    scheduler = get_scheduler()
    tasks = scheduler.list_tasks()
    
    items = []
    for task in tasks:
        items.append({
            "id": task.id,
            "name": task.name,
            "schedule_type": task.schedule_type.value,
            "status": task.status.value,
            "enabled": task.enabled,
            "last_run": task.last_run.isoformat() if task.last_run else None,
            "next_run": task.next_run.isoformat() if task.next_run else None,
            "run_count": task.run_count,
            "error_count": task.error_count,
        })
    
    return TaskResponse(
        data={
            "items": items,
            "total": len(items),
        }
    )


@router.post("/scheduler/tasks")
async def create_task(request: TaskCreate) -> TaskResponse:
    """创建任务"""
    from auto.shared.utils import generate_id
    
    # 创建执行函数
    async def execute_command():
        from auto.core.ai.router import get_router
        from auto.shared.models import Message, MessageRole
        
        router = get_router()
        messages = [Message(role=MessageRole.USER, content=request.command)]
        response = await router.chat(messages)
        return response.message.content
    
    # 解析调度类型
    type_map = {
        "once": ScheduleType.ONCE,
        "interval": ScheduleType.INTERVAL,
        "daily": ScheduleType.DAILY,
        "weekly": ScheduleType.WEEKLY,
        "monthly": ScheduleType.MONTHLY,
        "cron": ScheduleType.CRON,
    }
    
    stype = type_map.get(request.schedule_type, ScheduleType.DAILY)
    
    task = Task(
        id=generate_id("task"),
        name=request.name,
        handler=execute_command,
        schedule_type=stype,
        interval_seconds=request.interval_seconds,
        cron_expression=request.cron_expression,
        run_at=request.run_at,
        run_on=request.run_on,
        enabled=request.enabled,
    )
    
    scheduler = get_scheduler()
    scheduler.add_task(task)
    
    return TaskResponse(
        message="任务已创建",
        data={
            "id": task.id,
            "name": task.name,
            "next_run": task.next_run.isoformat() if task.next_run else None,
        }
    )


@router.get("/scheduler/tasks/{task_id}")
async def get_task(task_id: str) -> TaskResponse:
    """获取任务详情"""
    scheduler = get_scheduler()
    task = scheduler.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return TaskResponse(
        data={
            "id": task.id,
            "name": task.name,
            "schedule_type": task.schedule_type.value,
            "status": task.status.value,
            "enabled": task.enabled,
            "interval_seconds": task.interval_seconds,
            "run_at": task.run_at,
            "run_on": task.run_on,
            "last_run": task.last_run.isoformat() if task.last_run else None,
            "next_run": task.next_run.isoformat() if task.next_run else None,
            "run_count": task.run_count,
            "error_count": task.error_count,
            "last_error": task.last_error,
        }
    )


@router.delete("/scheduler/tasks/{task_id}")
async def delete_task(task_id: str) -> TaskResponse:
    """删除任务"""
    scheduler = get_scheduler()
    
    if scheduler.remove_task(task_id):
        return TaskResponse(message="任务已删除")
    else:
        raise HTTPException(status_code=404, detail="任务不存在")


@router.post("/scheduler/tasks/{task_id}/enable")
async def enable_task(task_id: str) -> TaskResponse:
    """启用任务"""
    scheduler = get_scheduler()
    
    if scheduler.enable_task(task_id):
        return TaskResponse(message="任务已启用")
    else:
        raise HTTPException(status_code=404, detail="任务不存在")


@router.post("/scheduler/tasks/{task_id}/disable")
async def disable_task(task_id: str) -> TaskResponse:
    """禁用任务"""
    scheduler = get_scheduler()
    
    if scheduler.disable_task(task_id):
        return TaskResponse(message="任务已禁用")
    else:
        raise HTTPException(status_code=404, detail="任务不存在")


@router.post("/scheduler/tasks/{task_id}/run")
async def run_task(task_id: str) -> TaskResponse:
    """立即执行任务"""
    scheduler = get_scheduler()
    
    if await scheduler.run_task_now(task_id):
        return TaskResponse(message="任务已触发")
    else:
        raise HTTPException(status_code=404, detail="任务不存在")


@router.get("/scheduler/status")
async def scheduler_status() -> TaskResponse:
    """获取调度器状态"""
    scheduler = get_scheduler()
    stats = scheduler.get_stats()
    
    return TaskResponse(data=stats)


@router.post("/scheduler/start")
async def start_scheduler() -> TaskResponse:
    """启动调度器"""
    scheduler = get_scheduler()
    await scheduler.start()
    
    return TaskResponse(message="调度器已启动")


@router.post("/scheduler/stop")
async def stop_scheduler() -> TaskResponse:
    """停止调度器"""
    scheduler = get_scheduler()
    await scheduler.stop()
    
    return TaskResponse(message="调度器已停止")
