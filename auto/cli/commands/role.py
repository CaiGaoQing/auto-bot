"""角色管理命令"""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from auto.core.role import get_role_manager

app = typer.Typer()
console = Console()


@app.command("list")
def list_roles():
    """列出所有角色"""
    manager = get_role_manager()
    roles = manager.list_roles()
    
    table = Table(title="可用角色")
    table.add_column("ID", style="cyan")
    table.add_column("图标")
    table.add_column("名称", style="green")
    table.add_column("说明")
    table.add_column("技能")
    table.add_column("类型", style="dim")
    
    for role in roles:
        skills = ", ".join(role.config.enabled_skills[:3])
        if len(role.config.enabled_skills) > 3:
            skills += f" (+{len(role.config.enabled_skills) - 3})"
        
        table.add_row(
            role.id,
            role.icon,
            role.display_name,
            role.description[:30] + "..." if len(role.description) > 30 else role.description,
            skills or "-",
            "内置" if role.builtin else "自定义",
        )
    
    console.print(table)
    console.print(f"\n共 {len(roles)} 个角色")


@app.command("show")
def show_role(role_id: str = typer.Argument(..., help="角色 ID")):
    """查看角色详情"""
    manager = get_role_manager()
    role = manager.get_role(role_id)
    
    if not role:
        console.print(f"[red]角色不存在: {role_id}[/red]")
        raise typer.Exit(1)
    
    # 角色信息
    content = f"""[bold]{role.icon} {role.display_name}[/bold]

[dim]ID:[/dim] {role.id}
[dim]类型:[/dim] {"内置" if role.builtin else "自定义"}
[dim]说明:[/dim] {role.description}

[yellow]启用技能:[/yellow]
{chr(10).join(f"  • {s}" for s in role.config.enabled_skills) or "  无限制"}

[yellow]权限:[/yellow]
{chr(10).join(f"  • {p}" for p in role.config.permissions) or "  无特殊权限"}

[yellow]交付物类型:[/yellow]
{chr(10).join(f"  • {t}" for t in role.config.output_types) or "  无限制"}
"""
    
    console.print(Panel(content, title=f"角色: {role.name}", expand=False))
    
    # 系统提示词
    if role.system_prompt:
        console.print("\n[yellow]系统提示词:[/yellow]")
        console.print(Panel(role.system_prompt, expand=False))


@app.command("use")
def use_role(role_id: str = typer.Argument(..., help="角色 ID")):
    """切换当前角色"""
    manager = get_role_manager()
    
    if manager.set_current_role(role_id):
        role = manager.get_role(role_id)
        console.print(f"[green]✓[/green] 已切换到: {role.icon} {role.display_name}")
        console.print(f"[dim]启用技能: {', '.join(role.config.enabled_skills) or '全部'}[/dim]")
    else:
        console.print(f"[red]角色不存在: {role_id}[/red]")
        raise typer.Exit(1)


@app.command("current")
def current_role():
    """显示当前角色"""
    manager = get_role_manager()
    role = manager.get_current_role()
    
    if role:
        console.print(f"当前角色: {role.icon} [bold]{role.display_name}[/bold]")
        console.print(f"[dim]ID: {role.id}[/dim]")
    else:
        console.print("[yellow]未设置当前角色[/yellow]")


@app.command("create")
def create_role(
    role_id: str = typer.Argument(..., help="角色 ID"),
    name: str = typer.Option(..., "--name", "-n", help="角色名称"),
    description: str = typer.Option("", "--desc", "-d", help="角色描述"),
    icon: str = typer.Option("👤", "--icon", "-i", help="角色图标"),
    skills: str = typer.Option("", "--skills", "-s", help="启用技能 (逗号分隔)"),
):
    """创建自定义角色"""
    manager = get_role_manager()
    
    # 检查是否已存在
    if manager.get_role(role_id):
        console.print(f"[red]角色 ID 已存在: {role_id}[/red]")
        raise typer.Exit(1)
    
    enabled_skills = [s.strip() for s in skills.split(",") if s.strip()] if skills else []
    
    console.print("[yellow]请输入系统提示词 (输入空行结束):[/yellow]")
    lines = []
    while True:
        try:
            line = input()
            if not line:
                break
            lines.append(line)
        except EOFError:
            break
    
    system_prompt = "\n".join(lines)
    
    role = manager.create_custom_role(
        role_id=role_id,
        name=name,
        display_name=name,
        description=description,
        system_prompt=system_prompt,
        enabled_skills=enabled_skills,
        icon=icon,
    )
    
    console.print(f"[green]✓[/green] 角色已创建: {role.icon} {role.display_name}")


@app.command("delete")
def delete_role(
    role_id: str = typer.Argument(..., help="角色 ID"),
    force: bool = typer.Option(False, "--force", "-f", help="强制删除"),
):
    """删除自定义角色"""
    manager = get_role_manager()
    
    role = manager.get_role(role_id)
    if not role:
        console.print(f"[red]角色不存在: {role_id}[/red]")
        raise typer.Exit(1)
    
    if role.builtin:
        console.print("[red]无法删除内置角色[/red]")
        raise typer.Exit(1)
    
    if not force:
        if not typer.confirm(f"确定删除角色 '{role.display_name}' ?"):
            raise typer.Abort()
    
    if manager.remove_role(role_id):
        console.print(f"[green]✓[/green] 角色已删除: {role.display_name}")
    else:
        console.print("[red]删除失败[/red]")
        raise typer.Exit(1)


@app.command("export")
def export_role(
    role_id: str = typer.Argument(..., help="角色 ID"),
    output: str = typer.Option(None, "--output", "-o", help="输出文件路径"),
):
    """导出角色配置"""
    import json
    from pathlib import Path
    
    manager = get_role_manager()
    
    data = manager.export_role(role_id)
    if not data:
        console.print(f"[red]角色不存在: {role_id}[/red]")
        raise typer.Exit(1)
    
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    
    if output:
        Path(output).write_text(json_str, encoding="utf-8")
        console.print(f"[green]✓[/green] 已导出到: {output}")
    else:
        console.print(json_str)


@app.command("import")
def import_role(
    file_path: str = typer.Argument(..., help="配置文件路径"),
):
    """导入角色配置"""
    import json
    from pathlib import Path
    
    path = Path(file_path)
    if not path.exists():
        console.print(f"[red]文件不存在: {file_path}[/red]")
        raise typer.Exit(1)
    
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        console.print(f"[red]JSON 解析错误: {e}[/red]")
        raise typer.Exit(1)
    
    manager = get_role_manager()
    
    # 检查是否已存在
    if manager.get_role(data.get("id", "")):
        if not typer.confirm(f"角色 '{data.get('id')}' 已存在，是否覆盖?"):
            raise typer.Abort()
    
    role = manager.import_role(data)
    console.print(f"[green]✓[/green] 角色已导入: {role.icon} {role.display_name}")
