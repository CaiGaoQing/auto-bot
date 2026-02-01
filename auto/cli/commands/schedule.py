"""定时任务命令"""

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="定时任务管理")
console = Console()


@app.command("list")
def list_tasks():
    """列出所有定时任务"""
    from auto.core.scheduler import get_scheduler
    
    scheduler = get_scheduler()
    tasks = scheduler.list_tasks()
    
    console.print()
    console.print("[bold]定时任务列表[/bold]")
    console.print()
    
    if not tasks:
        console.print("[dim]暂无定时任务[/dim]")
        return
    
    table = Table(show_header=True, header_style="bold")
    table.add_column("ID")
    table.add_column("名称")
    table.add_column("类型")
    table.add_column("状态")
    table.add_column("上次执行")
    table.add_column("下次执行")
    table.add_column("执行次数")
    
    for task in tasks:
        status = "[green]●[/green]" if task.enabled else "[red]●[/red]"
        if task.status.value == "running":
            status = "[yellow]●[/yellow]"
        
        table.add_row(
            task.id[:8],
            task.name,
            task.schedule_type.value,
            status,
            task.last_run.strftime("%m-%d %H:%M") if task.last_run else "-",
            task.next_run.strftime("%m-%d %H:%M") if task.next_run else "-",
            str(task.run_count),
        )
    
    console.print(table)


@app.command("add")
def add_task(
    name: str = typer.Argument(..., help="任务名称"),
    command: str = typer.Option(..., "--command", "-c", help="执行命令或 AI 指令"),
    schedule_type: str = typer.Option("daily", "--type", "-t", help="调度类型 (once, interval, daily, weekly)"),
    run_at: Optional[str] = typer.Option(None, "--at", help="执行时间 (HH:MM)"),
    interval: Optional[int] = typer.Option(None, "--interval", "-i", help="间隔秒数"),
    run_on: Optional[str] = typer.Option(None, "--on", help="执行日期 (周几用1-7，用逗号分隔)"),
):
    """添加定时任务"""
    from auto.core.scheduler import get_scheduler, Task, ScheduleType
    from auto.shared.utils import generate_id
    
    # 创建执行函数
    async def execute_command():
        from auto.core.ai.router import get_router
        from auto.shared.models import Message, MessageRole
        
        router = get_router()
        messages = [Message(role=MessageRole.USER, content=command)]
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
    
    stype = type_map.get(schedule_type, ScheduleType.DAILY)
    
    # 解析 run_on
    run_on_list = None
    if run_on:
        run_on_list = [int(x.strip()) for x in run_on.split(",")]
    
    task = Task(
        id=generate_id("task"),
        name=name,
        handler=execute_command,
        schedule_type=stype,
        interval_seconds=interval,
        run_at=run_at,
        run_on=run_on_list,
    )
    
    scheduler = get_scheduler()
    scheduler.add_task(task)
    
    console.print(f"[green]✓[/green] 任务已添加: {task.id}")
    if task.next_run:
        console.print(f"  下次执行: {task.next_run}")


@app.command("remove")
def remove_task(
    task_id: str = typer.Argument(..., help="任务 ID"),
):
    """移除定时任务"""
    from auto.core.scheduler import get_scheduler
    
    scheduler = get_scheduler()
    
    if scheduler.remove_task(task_id):
        console.print(f"[green]✓[/green] 任务已移除: {task_id}")
    else:
        console.print(f"[red]✗[/red] 任务不存在: {task_id}")


@app.command("enable")
def enable_task(
    task_id: str = typer.Argument(..., help="任务 ID"),
):
    """启用任务"""
    from auto.core.scheduler import get_scheduler
    
    scheduler = get_scheduler()
    
    if scheduler.enable_task(task_id):
        console.print(f"[green]✓[/green] 任务已启用: {task_id}")
    else:
        console.print(f"[red]✗[/red] 任务不存在: {task_id}")


@app.command("disable")
def disable_task(
    task_id: str = typer.Argument(..., help="任务 ID"),
):
    """禁用任务"""
    from auto.core.scheduler import get_scheduler
    
    scheduler = get_scheduler()
    
    if scheduler.disable_task(task_id):
        console.print(f"[green]✓[/green] 任务已禁用: {task_id}")
    else:
        console.print(f"[red]✗[/red] 任务不存在: {task_id}")


@app.command("run")
def run_task(
    task_id: str = typer.Argument(..., help="任务 ID"),
):
    """立即执行任务"""
    import asyncio
    from auto.core.scheduler import get_scheduler
    
    scheduler = get_scheduler()
    
    async def run():
        if await scheduler.run_task_now(task_id):
            console.print(f"[green]✓[/green] 任务已触发: {task_id}")
        else:
            console.print(f"[red]✗[/red] 任务不存在: {task_id}")
    
    asyncio.run(run())


@app.command("status")
def show_status():
    """显示调度器状态"""
    from auto.core.scheduler import get_scheduler
    
    scheduler = get_scheduler()
    stats = scheduler.get_stats()
    
    console.print()
    console.print("[bold]调度器状态[/bold]")
    console.print()
    console.print(f"  运行状态: {'[green]运行中[/green]' if stats['is_running'] else '[red]已停止[/red]'}")
    console.print(f"  总任务数: {stats['total_tasks']}")
    console.print(f"  启用任务: {stats['enabled_tasks']}")
    console.print(f"  正在执行: {stats['running_tasks']}")
    console.print(f"  总执行次数: {stats['completed_runs']}")
    console.print(f"  总错误次数: {stats['total_errors']}")
    console.print()


@app.command("start")
def start_scheduler():
    """启动调度器 (后台运行)"""
    import asyncio
    from auto.core.scheduler import get_scheduler
    
    scheduler = get_scheduler()
    
    console.print("[dim]启动调度器...[/dim]")
    
    async def run():
        await scheduler.start()
        console.print("[green]✓[/green] 调度器已启动")
        
        # 保持运行
        try:
            while True:
                await asyncio.sleep(60)
        except KeyboardInterrupt:
            await scheduler.stop()
            console.print("\n[dim]调度器已停止[/dim]")
    
    asyncio.run(run())
