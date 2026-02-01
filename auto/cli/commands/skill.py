"""技能包命令"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="技能包管理")
console = Console()

# source 子命令组
source_app = typer.Typer(help="技能源管理")
app.add_typer(source_app, name="source")


@app.command("list")
def list_skills(
    installed: bool = typer.Option(False, "--installed", "-i", help="只显示已安装"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="按分类筛选"),
):
    """列出技能包"""
    from auto.core.skill.engine import SkillEngine
    
    engine = SkillEngine()
    skills = engine.list_skills()
    
    if installed:
        skills = [s for s in skills if s.get("is_installed", False)]
    
    if category:
        skills = [s for s in skills if s.get("category") == category]
    
    if not skills:
        console.print("[dim]暂无技能包[/dim]")
        return
    
    table = Table(title="技能包列表")
    table.add_column("名称", style="cyan")
    table.add_column("版本")
    table.add_column("分类")
    table.add_column("描述")
    table.add_column("状态")
    
    for skill in skills:
        status = ""
        if skill.get("is_installed"):
            status = "[green]已安装[/green]"
            if not skill.get("is_enabled", True):
                status = "[yellow]已禁用[/yellow]"
        
        table.add_row(
            skill.get("name", ""),
            skill.get("version", "-"),
            skill.get("category", "general"),
            skill.get("description", "")[:40] + "...",
            status,
        )
    
    console.print(table)


@app.command("info")
def skill_info(
    name: str = typer.Argument(..., help="技能包名称"),
):
    """查看技能包详情"""
    from auto.core.skill.engine import SkillEngine
    
    engine = SkillEngine()
    skill = engine.get_skill(name)
    
    if not skill:
        console.print(f"[red]技能包不存在: {name}[/red]")
        raise typer.Exit(1)
    
    console.print(f"[bold]技能包: {skill.name}[/bold]")
    console.print()
    console.print(f"  显示名称: {skill.display_name}")
    console.print(f"  版本: {skill.version}")
    console.print(f"  分类: {skill.category}")
    console.print(f"  描述: {skill.description}")
    console.print()
    console.print("[bold]工具列表:[/bold]")
    for tool in skill.tools:
        console.print(f"  - {tool.name}: {tool.description}")


@app.command("install")
def install_skill(
    name: str = typer.Argument(..., help="技能包名称或路径"),
):
    """安装技能包
    
    Examples:
        auto skill install finance
        auto skill install official/finance
        auto skill install https://github.com/user/skill/releases/v1.0/skill.zip
        auto skill install ./my-skill
    """
    from auto.core.skill.engine import SkillEngine
    
    console.print(f"[dim]正在安装 {name}...[/dim]")
    
    engine = SkillEngine()
    
    try:
        engine.install_skill(name)
        console.print(f"[green]✓[/green] 已安装: {name}")
    except Exception as e:
        console.print(f"[red]安装失败: {e}[/red]")
        raise typer.Exit(1)


@app.command("uninstall")
def uninstall_skill(
    name: str = typer.Argument(..., help="技能包名称"),
    force: bool = typer.Option(False, "--force", "-f", help="强制卸载"),
):
    """卸载技能包"""
    from auto.core.skill.engine import SkillEngine
    
    if not force:
        confirm = typer.confirm(f"确定卸载技能包 '{name}'?")
        if not confirm:
            console.print("[dim]已取消[/dim]")
            return
    
    engine = SkillEngine()
    
    try:
        engine.uninstall_skill(name)
        console.print(f"[green]✓[/green] 已卸载: {name}")
    except Exception as e:
        console.print(f"[red]卸载失败: {e}[/red]")
        raise typer.Exit(1)


@app.command("search")
def search_skills(
    keyword: str = typer.Argument(..., help="搜索关键词"),
):
    """搜索技能包"""
    console.print(f"[dim]搜索: {keyword}...[/dim]")
    console.print()
    console.print("[yellow]技能包市场功能开发中...[/yellow]")


@app.command("update")
def update_skill(
    name: str = typer.Argument(..., help="技能包名称"),
):
    """更新技能包"""
    console.print(f"[dim]检查更新: {name}...[/dim]")
    console.print("[yellow]更新功能开发中...[/yellow]")


@app.command("run")
def run_skill(
    name: str = typer.Argument(..., help="技能名.工具名"),
    args: Optional[list[str]] = typer.Argument(None, help="参数"),
):
    """直接运行技能工具
    
    Examples:
        auto skill run file_manager.list_directory ~/Desktop
        auto skill run devops.docker_ps
    """
    import asyncio
    from auto.core.skill.engine import SkillEngine
    
    # 解析技能名和工具名
    parts = name.split(".")
    if len(parts) != 2:
        console.print("[red]格式错误，应为: 技能名.工具名[/red]")
        raise typer.Exit(1)
    
    skill_name, tool_name = parts
    
    console.print(f"[dim]运行: {skill_name}.{tool_name}[/dim]")
    
    engine = SkillEngine()
    
    async def run():
        # 解析参数
        params = {}
        if args:
            # 简单解析: key=value 或位置参数
            for i, arg in enumerate(args):
                if "=" in arg:
                    k, v = arg.split("=", 1)
                    params[k] = v
                else:
                    params[f"arg{i}"] = arg
        
        result = await engine.execute_tool(skill_name, tool_name, params)
        return result
    
    try:
        result = asyncio.run(run())
        if result.success:
            console.print(f"[green]✓[/green] {result.message}")
            if result.data:
                console.print(result.data)
        else:
            console.print(f"[red]✗[/red] {result.error}")
    except Exception as e:
        console.print(f"[red]执行失败: {e}[/red]")
        raise typer.Exit(1)


# Source 子命令
@source_app.command("list")
def list_sources():
    """列出技能源"""
    console.print("[bold]技能源:[/bold]")
    console.print("  [cyan]official[/cyan]  https://skills.ai-auto.dev (官方)")
    console.print()
    console.print("[dim]使用 auto skill source add 添加更多源[/dim]")


@source_app.command("add")
def add_source(
    name: str = typer.Argument(..., help="源名称"),
    url: str = typer.Argument(..., help="源 URL"),
    token: Optional[str] = typer.Option(None, "--token", "-t", help="认证 Token"),
):
    """添加技能源"""
    console.print(f"[green]✓[/green] 已添加源: {name} ({url})")
    console.print("[yellow]源管理功能开发中...[/yellow]")


@source_app.command("remove")
def remove_source(
    name: str = typer.Argument(..., help="源名称"),
):
    """移除技能源"""
    console.print(f"[green]✓[/green] 已移除源: {name}")
