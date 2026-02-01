"""CLI 主入口"""

import typer
from rich.console import Console

from auto import __version__
from auto.cli.commands import chat, config, mcp, query, skill, workspace, schedule, role, task, onboard, doctor

# 创建主应用
app = typer.Typer(
    name="auto",
    help="AI 个人助手 - 智能工作平台",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

# 控制台
console = Console()

# 注册子命令
app.add_typer(chat.app, name="chat", help="对话命令")
app.add_typer(workspace.app, name="workspace", help="工作空间管理")
app.add_typer(skill.app, name="skill", help="技能包管理")
app.add_typer(config.app, name="config", help="配置管理")
app.add_typer(mcp.app, name="mcp", help="MCP 服务器管理")
app.add_typer(query.app, name="query", help="查询命令")
app.add_typer(schedule.app, name="schedule", help="定时任务管理")
app.add_typer(role.app, name="role", help="角色管理")
app.add_typer(task.app, name="task", help="任务执行（生成 PPT/Excel/PDF）")
app.add_typer(onboard.app, name="onboard", help="向导式安装配置")
app.add_typer(doctor.app, name="doctor", help="系统健康诊断")


@app.command()
def version():
    """显示版本信息"""
    console.print(f"[bold blue]AI Auto[/bold blue] v{__version__}")


@app.command()
def init():
    """初始化配置"""
    from pathlib import Path
    from auto.shared.config import DEFAULT_CONFIG_DIR, get_config_manager
    
    console.print("[bold]初始化 AI Auto...[/bold]")
    
    # 创建配置目录
    DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    (DEFAULT_CONFIG_DIR / "logs").mkdir(exist_ok=True)
    (DEFAULT_CONFIG_DIR / "skills").mkdir(exist_ok=True)
    (DEFAULT_CONFIG_DIR / "mcp_servers").mkdir(exist_ok=True)
    
    # 初始化配置
    config_manager = get_config_manager()
    config_manager.save()
    
    console.print(f"[green]✓[/green] 配置目录: {DEFAULT_CONFIG_DIR}")
    console.print(f"[green]✓[/green] 配置文件: {config_manager.config_path}")
    console.print()
    console.print("[dim]下一步: 配置 AI 提供商[/dim]")
    console.print("  auto config provider add --name openai --api-key 'sk-xxx'")


@app.command()
def help(command: str = typer.Argument(None, help="命令名称")):
    """显示帮助信息"""
    if command:
        # 显示特定命令的帮助
        console.print(f"[bold]命令: {command}[/bold]")
        console.print()
        console.print(f"运行 [cyan]auto {command} --help[/cyan] 查看详细帮助")
    else:
        # 显示总体帮助
        console.print("[bold blue]AI Auto - AI 个人助手[/bold blue]")
        console.print()
        console.print("[bold]可用命令:[/bold]")
        console.print()
        commands = [
            ("chat", "交互式对话或单次对话"),
            ("workspace", "工作空间管理"),
            ("skill", "技能包管理"),
            ("role", "角色管理"),
            ("config", "配置管理"),
            ("mcp", "MCP 服务器管理"),
            ("query", "查询系统信息"),
            ("schedule", "定时任务管理"),
            ("onboard", "🚀 向导式安装配置"),
            ("doctor", "🩺 系统健康诊断"),
            ("init", "初始化配置"),
            ("version", "显示版本"),
        ]
        for cmd, desc in commands:
            console.print(f"  [cyan]{cmd:12}[/cyan] {desc}")
        console.print()
        console.print("[dim]使用 auto <command> --help 查看具体命令帮助[/dim]")


# 快捷命令 - 直接对话
@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    message: str = typer.Argument(None, help="直接发送消息"),
):
    """AI 个人助手 - 智能工作平台"""
    if ctx.invoked_subcommand is None and message:
        # 直接对话模式
        import asyncio
        from auto.cli.commands.chat import single_chat
        asyncio.run(single_chat(message))


if __name__ == "__main__":
    app()
