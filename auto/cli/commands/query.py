"""查询命令"""

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

app = typer.Typer(help="查询系统信息")
console = Console()


@app.callback(invoke_without_command=True)
def query(ctx: typer.Context):
    """查询系统信息"""
    if ctx.invoked_subcommand is None:
        # 默认显示概览
        all_info()


@app.command("all")
def all_info():
    """显示系统概览"""
    from auto.shared.config import get_config
    
    config = get_config()
    
    console.print()
    console.print(Panel.fit(
        "[bold blue]系统概览[/bold blue]",
        border_style="blue",
    ))
    console.print()
    
    # 工作空间
    console.print("[bold]📁 工作空间[/bold]")
    ws_table = Table(show_header=True, header_style="bold")
    ws_table.add_column("名称")
    ws_table.add_column("角色")
    ws_table.add_column("状态")
    
    current_ws = config.workspace.current or "(无)"
    ws_table.add_row(current_ws, "general", "当前")
    console.print(ws_table)
    console.print()
    
    # AI 提供商
    console.print("[bold]🤖 AI 提供商[/bold]")
    if config.providers:
        provider_table = Table(show_header=True, header_style="bold")
        provider_table.add_column("名称")
        provider_table.add_column("类型")
        provider_table.add_column("状态")
        
        for p in config.providers:
            status = "[green]●[/green] 启用" if p.is_enabled else "[red]●[/red] 禁用"
            if p.is_default:
                status += " (默认)"
            provider_table.add_row(p.name, p.provider_type, status)
        console.print(provider_table)
    else:
        console.print("[dim]未配置 AI 提供商[/dim]")
        console.print("[dim]运行 auto config provider add 添加提供商[/dim]")
    console.print()
    
    # 运行模式
    console.print("[bold]⚙️ 配置[/bold]")
    console.print(f"  运行模式: {config.mode}")
    console.print(f"  默认模型: {config.default_model}")
    console.print(f"  存储类型: {config.storage.type}")
    console.print()


@app.command("providers")
def providers():
    """查询 AI 提供商"""
    from auto.shared.config import get_config
    
    config = get_config()
    
    console.print()
    console.print("[bold]AI 提供商列表[/bold]")
    console.print()
    
    if not config.providers:
        console.print("[dim]未配置 AI 提供商[/dim]")
        console.print()
        console.print("添加提供商:")
        console.print("  auto config provider add --name openai --api-key 'sk-xxx'")
        return
    
    table = Table(show_header=True, header_style="bold")
    table.add_column("名称")
    table.add_column("类型")
    table.add_column("Base URL")
    table.add_column("状态")
    
    for p in config.providers:
        status = "[green]●[/green]" if p.is_enabled else "[red]●[/red]"
        if p.is_default:
            status += " 默认"
        table.add_row(p.name, p.provider_type, p.base_url[:40] + "...", status)
    
    console.print(table)


@app.command("models")
def models():
    """查询可用模型"""
    from auto.shared.config import get_config
    
    config = get_config()
    
    console.print()
    console.print("[bold]可用模型[/bold]")
    console.print()
    
    # 默认模型列表
    default_models = [
        ("gpt-4o", "OpenAI GPT-4o"),
        ("gpt-4o-mini", "OpenAI GPT-4o Mini"),
        ("gpt-3.5-turbo", "OpenAI GPT-3.5"),
        ("claude-3-opus-20240229", "Claude 3 Opus"),
        ("claude-3-sonnet-20240229", "Claude 3 Sonnet"),
        ("claude-3-haiku-20240307", "Claude 3 Haiku"),
    ]
    
    table = Table(show_header=True, header_style="bold")
    table.add_column("模型")
    table.add_column("描述")
    table.add_column("状态")
    
    for model, desc in default_models:
        status = "[green]●[/green]" if model == config.default_model else ""
        table.add_row(model, desc, status)
    
    console.print(table)
    console.print()
    console.print(f"[dim]当前默认模型: {config.default_model}[/dim]")


@app.command("skills")
def skills():
    """查询可用技能"""
    console.print()
    console.print("[bold]技能包列表[/bold]")
    console.print()
    
    # TODO: 从技能引擎获取
    builtin_skills = [
        ("developer", "开发助手", "代码生成、审查、调试"),
        ("finance", "财务助手", "Excel 处理、报表生成"),
        ("devops", "运维助手", "Docker、数据库、Redis"),
        ("file_manager", "文件管理", "整理桌面、归档文件"),
        ("stock_research", "A股调研", "股票数据、财报分析"),
    ]
    
    table = Table(show_header=True, header_style="bold")
    table.add_column("名称")
    table.add_column("显示名称")
    table.add_column("描述")
    table.add_column("状态")
    
    for name, display, desc in builtin_skills:
        table.add_row(name, display, desc, "[green]内置[/green]")
    
    console.print(table)


@app.command("workspaces")
def workspaces():
    """查询工作空间"""
    from auto.shared.config import get_config
    
    config = get_config()
    
    console.print()
    console.print("[bold]工作空间列表[/bold]")
    console.print()
    
    # TODO: 从数据库获取
    console.print(f"  当前: {config.workspace.current or '(无)'}")
    console.print(f"  默认路径: {config.workspace.default_path}")
    console.print()
    console.print("[dim]创建工作空间: auto workspace create <name>[/dim]")


@app.command("mcp")
def mcp_servers():
    """查询 MCP 服务器"""
    console.print()
    console.print("[bold]MCP 服务器列表[/bold]")
    console.print()
    
    # TODO: 从配置获取
    console.print("[dim]未配置 MCP 服务器[/dim]")
    console.print()
    console.print("添加 MCP 服务器:")
    console.print("  auto mcp add <name> --transport stdio --command 'npx ...'")


@app.command("stats")
def stats():
    """查询使用统计"""
    console.print()
    console.print("[bold]使用统计[/bold]")
    console.print()
    
    # TODO: 从数据库获取
    console.print("  今日请求: 0")
    console.print("  今日 Token: 0")
    console.print("  今日成本: $0.00")
    console.print()
    console.print("[dim]详细统计: auto stats[/dim]")
