"""定时任务调度引擎"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Optional
import logging

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScheduleType(Enum):
    """调度类型"""
    ONCE = "once"           # 一次性
    INTERVAL = "interval"   # 间隔执行
    CRON = "cron"           # Cron 表达式
    DAILY = "daily"         # 每日
    WEEKLY = "weekly"       # 每周
    MONTHLY = "monthly"     # 每月


@dataclass
class Task:
    """定时任务"""
    id: str
    name: str
    handler: Callable
    schedule_type: ScheduleType
    
    # 调度配置
    interval_seconds: Optional[int] = None
    cron_expression: Optional[str] = None
    run_at: Optional[str] = None  # HH:MM 格式
    run_on: Optional[list[int]] = None  # 周几 (1-7) 或 月几号 (1-31)
    
    # 执行参数
    args: tuple = ()
    kwargs: dict = field(default_factory=dict)
    
    # 状态
    status: TaskStatus = TaskStatus.PENDING
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    
    # 配置
    enabled: bool = True
    max_retries: int = 3
    timeout_seconds: int = 3600
    
    # 元数据
    workspace_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def calculate_next_run(self) -> Optional[datetime]:
        """计算下次执行时间"""
        now = datetime.now()
        
        if self.schedule_type == ScheduleType.ONCE:
            if self.run_count == 0 and self.next_run:
                return self.next_run
            return None
        
        elif self.schedule_type == ScheduleType.INTERVAL:
            if self.interval_seconds:
                return now + timedelta(seconds=self.interval_seconds)
        
        elif self.schedule_type == ScheduleType.DAILY:
            if self.run_at:
                hour, minute = map(int, self.run_at.split(":"))
                next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                if next_run <= now:
                    next_run += timedelta(days=1)
                
                return next_run
        
        elif self.schedule_type == ScheduleType.WEEKLY:
            if self.run_at and self.run_on:
                hour, minute = map(int, self.run_at.split(":"))
                
                # 找到下一个匹配的周几
                for days_ahead in range(8):
                    check_date = now + timedelta(days=days_ahead)
                    weekday = check_date.isoweekday()  # 1-7
                    
                    if weekday in self.run_on:
                        next_run = check_date.replace(
                            hour=hour, minute=minute, second=0, microsecond=0
                        )
                        if next_run > now:
                            return next_run
        
        elif self.schedule_type == ScheduleType.MONTHLY:
            if self.run_at and self.run_on:
                hour, minute = map(int, self.run_at.split(":"))
                
                # 找到下一个匹配的日期
                for months_ahead in range(2):
                    if months_ahead == 0:
                        check_month = now.month
                        check_year = now.year
                    else:
                        check_month = now.month + 1
                        check_year = now.year
                        if check_month > 12:
                            check_month = 1
                            check_year += 1
                    
                    for day in sorted(self.run_on):
                        try:
                            next_run = datetime(
                                check_year, check_month, day,
                                hour, minute, 0
                            )
                            if next_run > now:
                                return next_run
                        except ValueError:
                            continue
        
        elif self.schedule_type == ScheduleType.CRON:
            # 简化的 Cron 解析
            if self.cron_expression:
                return self._parse_cron(self.cron_expression, now)
        
        return None
    
    def _parse_cron(self, expression: str, now: datetime) -> Optional[datetime]:
        """解析 Cron 表达式 (简化版)
        
        格式: 分 时 日 月 周
        """
        try:
            parts = expression.split()
            if len(parts) != 5:
                return None
            
            minute_part, hour_part, day_part, month_part, weekday_part = parts
            
            # 简化实现：只支持固定时间
            if minute_part.isdigit() and hour_part.isdigit():
                minute = int(minute_part)
                hour = int(hour_part)
                
                next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                if next_run <= now:
                    next_run += timedelta(days=1)
                
                return next_run
            
            return None
        except Exception:
            return None


class SchedulerEngine:
    """定时任务调度引擎"""
    
    def __init__(self):
        self._tasks: dict[str, Task] = {}
        self._running = False
        self._loop_task: Optional[asyncio.Task] = None
    
    def add_task(self, task: Task) -> None:
        """添加任务"""
        task.next_run = task.calculate_next_run()
        self._tasks[task.id] = task
        logger.info(f"添加任务: {task.name}, 下次执行: {task.next_run}")
    
    def remove_task(self, task_id: str) -> bool:
        """移除任务"""
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        return self._tasks.get(task_id)
    
    def list_tasks(self) -> list[Task]:
        """列出所有任务"""
        return list(self._tasks.values())
    
    def enable_task(self, task_id: str) -> bool:
        """启用任务"""
        task = self._tasks.get(task_id)
        if task:
            task.enabled = True
            task.next_run = task.calculate_next_run()
            return True
        return False
    
    def disable_task(self, task_id: str) -> bool:
        """禁用任务"""
        task = self._tasks.get(task_id)
        if task:
            task.enabled = False
            return True
        return False
    
    async def start(self) -> None:
        """启动调度器"""
        if self._running:
            return
        
        self._running = True
        self._loop_task = asyncio.create_task(self._run_loop())
        logger.info("调度器已启动")
    
    async def stop(self) -> None:
        """停止调度器"""
        self._running = False
        
        if self._loop_task:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass
        
        logger.info("调度器已停止")
    
    async def _run_loop(self) -> None:
        """调度循环"""
        while self._running:
            try:
                now = datetime.now()
                
                for task in self._tasks.values():
                    if not task.enabled:
                        continue
                    
                    if task.next_run and task.next_run <= now:
                        # 执行任务
                        asyncio.create_task(self._execute_task(task))
                
                # 休眠一段时间
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"调度循环错误: {str(e)}")
                await asyncio.sleep(10)
    
    async def _execute_task(self, task: Task) -> None:
        """执行任务"""
        task.status = TaskStatus.RUNNING
        task.last_run = datetime.now()
        
        logger.info(f"执行任务: {task.name}")
        
        try:
            # 执行处理函数
            if asyncio.iscoroutinefunction(task.handler):
                result = await asyncio.wait_for(
                    task.handler(*task.args, **task.kwargs),
                    timeout=task.timeout_seconds,
                )
            else:
                result = task.handler(*task.args, **task.kwargs)
            
            task.status = TaskStatus.COMPLETED
            task.run_count += 1
            
            logger.info(f"任务完成: {task.name}")
        
        except asyncio.TimeoutError:
            task.status = TaskStatus.FAILED
            task.error_count += 1
            task.last_error = "执行超时"
            logger.error(f"任务超时: {task.name}")
        
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_count += 1
            task.last_error = str(e)
            logger.error(f"任务失败: {task.name}, 错误: {str(e)}")
        
        finally:
            # 计算下次执行时间
            task.next_run = task.calculate_next_run()
    
    async def run_task_now(self, task_id: str) -> bool:
        """立即执行任务"""
        task = self._tasks.get(task_id)
        if not task:
            return False
        
        asyncio.create_task(self._execute_task(task))
        return True
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        tasks = list(self._tasks.values())
        
        return {
            "total_tasks": len(tasks),
            "enabled_tasks": sum(1 for t in tasks if t.enabled),
            "running_tasks": sum(1 for t in tasks if t.status == TaskStatus.RUNNING),
            "completed_runs": sum(t.run_count for t in tasks),
            "total_errors": sum(t.error_count for t in tasks),
            "is_running": self._running,
        }


# 全局调度器实例
_scheduler: Optional[SchedulerEngine] = None


def get_scheduler() -> SchedulerEngine:
    """获取全局调度器"""
    global _scheduler
    if _scheduler is None:
        _scheduler = SchedulerEngine()
    return _scheduler


# 便捷装饰器
def scheduled(
    schedule_type: ScheduleType,
    task_id: Optional[str] = None,
    name: Optional[str] = None,
    interval_seconds: Optional[int] = None,
    cron_expression: Optional[str] = None,
    run_at: Optional[str] = None,
    run_on: Optional[list[int]] = None,
):
    """定时任务装饰器"""
    def decorator(func: Callable):
        from auto.shared.utils import generate_id
        
        task = Task(
            id=task_id or generate_id("task"),
            name=name or func.__name__,
            handler=func,
            schedule_type=schedule_type,
            interval_seconds=interval_seconds,
            cron_expression=cron_expression,
            run_at=run_at,
            run_on=run_on,
        )
        
        # 自动注册到调度器
        get_scheduler().add_task(task)
        
        return func
    
    return decorator
