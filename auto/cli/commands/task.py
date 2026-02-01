"""任务命令 - CLI 执行任务生成文件"""

import asyncio
from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

app = typer.Typer(help="任务执行 - 处理文件生成 PPT/Excel/PDF")
console = Console()


@app.command("run")
def run_task(
    task: str = typer.Argument(..., help="任务描述，如：分析这份财报并生成总结"),
    files: Optional[List[Path]] = typer.Option(
        None, "-f", "--file", help="输入文件路径（可多个）"
    ),
    output_format: str = typer.Option(
        "md", "-o", "--output", help="输出格式: md/xlsx/pptx/pdf/json"
    ),
    output_dir: Optional[Path] = typer.Option(
        None, "-d", "--dir", help="输出目录（默认当前目录）"
    ),
):
    """
    执行任务并生成文件
    
    示例:
        auto task run "分析财报" -f report.xlsx -o pptx
        auto task run "总结会议记录" -f meeting.txt -o pdf
        auto task run "生成月度报告" -f data.csv -o xlsx
    """
    console.print(Panel(f"[bold blue]任务:[/] {task}", title="AI 任务执行"))
    
    # 准备工作目录
    work_dir = output_dir or Path.cwd()
    task_dir = work_dir / f".task_{_generate_id()}"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "files").mkdir(exist_ok=True)
    (task_dir / "outputs").mkdir(exist_ok=True)
    
    # 复制输入文件
    input_files = []
    if files:
        console.print("\n[dim]输入文件:[/]")
        for f in files:
            if f.exists():
                import shutil
                dest = task_dir / "files" / f.name
                shutil.copy(f, dest)
                input_files.append(f.name)
                console.print(f"  • {f.name}")
            else:
                console.print(f"  [red]✗ {f} 不存在[/]")
    
    # 执行任务
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task(description="正在处理...", total=None)
        
        result = asyncio.run(_execute_task(
            task_dir, task, input_files, output_format
        ))
    
    if not result.success:
        console.print(f"\n[red]✗ 执行失败: {result.error}[/]")
        return
    
    # 移动输出文件到目标目录
    console.print("\n[green]✓ 任务完成[/]")
    console.print("\n[bold]生成的文件:[/]")
    
    for file_info in result.output_files:
        src = Path(file_info["path"])
        dest = work_dir / file_info["name"]
        
        # 移动文件
        if src.exists():
            import shutil
            shutil.move(str(src), str(dest))
            
            size_kb = file_info["size"] / 1024
            console.print(f"  [green]✓[/] {dest.name} ({size_kb:.1f} KB)")
    
    # 清理临时目录
    import shutil
    shutil.rmtree(task_dir, ignore_errors=True)
    
    # 显示预览
    if result.content:
        console.print("\n[bold]内容预览:[/]")
        preview = result.content[:500] + ("..." if len(result.content) > 500 else "")
        console.print(Panel(preview, border_style="dim"))


@app.command("list")
def list_formats():
    """列出支持的输出格式"""
    table = Table(title="支持的输出格式")
    table.add_column("格式", style="cyan")
    table.add_column("扩展名", style="green")
    table.add_column("说明")
    
    table.add_row("md", ".md", "Markdown 文档")
    table.add_row("xlsx", ".xlsx", "Excel 表格")
    table.add_row("pptx", ".pptx", "PowerPoint 演示文稿")
    table.add_row("pdf", ".pdf", "PDF 文档")
    table.add_row("json", ".json", "JSON 数据")
    
    console.print(table)


@app.command("examples")
def show_examples():
    """显示使用示例"""
    examples = """
[bold]任务执行示例:[/]

[cyan]1. 分析财报生成 PPT:[/]
   auto task run "分析这份财报，生成投资建议报告" -f 财报.xlsx -o pptx

[cyan]2. 总结会议纪要:[/]
   auto task run "总结会议要点，列出待办事项" -f 会议记录.txt -o pdf

[cyan]3. 数据分析生成 Excel:[/]
   auto task run "分析销售数据，按月份汇总" -f sales.csv -o xlsx

[cyan]4. 多文件处理:[/]
   auto task run "对比两份文档的差异" -f doc1.pdf -f doc2.pdf -o md

[cyan]5. 生成报告到指定目录:[/]
   auto task run "生成月度总结" -f data.xlsx -o pdf -d ~/reports/
"""
    console.print(Panel(examples, title="使用示例"))


async def _execute_task(
    task_dir: Path,
    task: str,
    input_files: List[str],
    output_format: str,
):
    """执行任务"""
    from auto.core.task import TaskExecutor, OutputFormat
    
    try:
        fmt = OutputFormat(output_format.lower())
    except ValueError:
        fmt = OutputFormat.MARKDOWN
    
    executor = TaskExecutor(task_dir)
    return await executor.execute(
        task=task,
        input_files=input_files,
        output_format=fmt,
    )


def _generate_id() -> str:
    """生成随机 ID"""
    import hashlib
    import time
    return hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
