"""工作空间命令"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from auto.shared.config import get_config_manager
from auto.shared.models import Workspace
from auto.shared.utils import generate_id, slugify, relative_time

app = typer.Typer(help="工作空间管理")
console = Console()


# 简单的本地存储（后续可替换为数据库）
def _get_workspaces_file() -> Path:
    from auto.shared.config import DEFAULT_CONFIG_DIR
    return DEFAULT_CONFIG_DIR / "workspaces.json"


def _load_workspaces() -> list[dict]:
    """加载工作空间列表"""
    import json
    file = _get_workspaces_file()
    if file.exists():
        return json.loads(file.read_text())
    return []


def _save_workspaces(workspaces: list[dict]) -> None:
    """保存工作空间列表"""
    import json
    file = _get_workspaces_file()
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps(workspaces, ensure_ascii=False, indent=2, default=str))


@app.command("create")
def create(
    name: str = typer.Argument(..., help="工作空间名称"),
    role: str = typer.Option("general", "--role", "-r", help="角色"),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="本地路径"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="描述"),
):
    """创建工作空间
    
    Examples:
        auto workspace create my-project
        auto workspace create my-project --role developer
        auto workspace create my-project --path ~/projects/my-project
    """
    from datetime import datetime
    
    workspaces = _load_workspaces()
    
    # 检查是否已存在
    slug = slugify(name)
    if any(w["slug"] == slug for w in workspaces):
        console.print(f"[red]工作空间已存在: {name}[/red]")
        raise typer.Exit(1)
    
    # 创建工作空间
    workspace = {
        "id": generate_id("ws"),
        "name": name,
        "slug": slug,
        "description": description,
        "role": role,
        "local_path": path,
        "settings": {},
        "is_active": True,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    
    workspaces.append(workspace)
    _save_workspaces(workspaces)
    
    # 设置为当前工作空间
    config = get_config_manager()
    config.set("workspace.current", slug)
    
    console.print(f"[green]✓[/green] 创建工作空间: {name}")
    console.print(f"  ID: {workspace['id']}")
    console.print(f"  角色: {role}")
    if path:
        console.print(f"  路径: {path}")


@app.command("list")
def list_workspaces(
    all: bool = typer.Option(False, "--all", "-a", help="显示所有（包括禁用的）"),
):
    """列出工作空间"""
    from datetime import datetime
    
    workspaces = _load_workspaces()
    config = get_config_manager()
    current = config.get("workspace.current")
    
    if not workspaces:
        console.print("[dim]暂无工作空间[/dim]")
        console.print("[dim]使用 auto workspace create <name> 创建[/dim]")
        return
    
    # 过滤
    if not all:
        workspaces = [w for w in workspaces if w.get("is_active", True)]
    
    table = Table(title="工作空间列表")
    table.add_column("名称", style="cyan")
    table.add_column("角色", style="green")
    table.add_column("路径")
    table.add_column("更新时间")
    table.add_column("状态")
    
    for ws in workspaces:
        status = "当前" if ws["slug"] == current else ""
        if not ws.get("is_active", True):
            status = "禁用"
        
        updated = ws.get("updated_at", "")
        if updated:
            try:
                dt = datetime.fromisoformat(updated)
                updated = relative_time(dt)
            except:
                pass
        
        table.add_row(
            ws["name"],
            ws.get("role", "general"),
            ws.get("local_path", "-"),
            updated,
            status,
        )
    
    console.print(table)


@app.command("switch")
def switch(
    name: str = typer.Argument(..., help="工作空间名称或 slug"),
):
    """切换工作空间"""
    workspaces = _load_workspaces()
    
    # 查找工作空间
    ws = None
    for w in workspaces:
        if w["name"] == name or w["slug"] == name:
            ws = w
            break
    
    if not ws:
        console.print(f"[red]工作空间不存在: {name}[/red]")
        raise typer.Exit(1)
    
    # 切换
    config = get_config_manager()
    config.set("workspace.current", ws["slug"])
    
    console.print(f"[green]✓[/green] 已切换到: {ws['name']}")


@app.command("info")
def info(
    name: Optional[str] = typer.Argument(None, help="工作空间名称"),
):
    """查看工作空间详情"""
    config = get_config_manager()
    
    if not name:
        name = config.get("workspace.current")
        if not name:
            console.print("[yellow]未指定工作空间，使用 --help 查看帮助[/yellow]")
            return
    
    workspaces = _load_workspaces()
    ws = None
    for w in workspaces:
        if w["name"] == name or w["slug"] == name:
            ws = w
            break
    
    if not ws:
        console.print(f"[red]工作空间不存在: {name}[/red]")
        raise typer.Exit(1)
    
    console.print(f"[bold]工作空间: {ws['name']}[/bold]")
    console.print()
    console.print(f"  ID: {ws['id']}")
    console.print(f"  Slug: {ws['slug']}")
    console.print(f"  角色: {ws.get('role', 'general')}")
    console.print(f"  描述: {ws.get('description') or '-'}")
    console.print(f"  路径: {ws.get('local_path') or '-'}")
    console.print(f"  状态: {'激活' if ws.get('is_active', True) else '禁用'}")
    console.print(f"  创建时间: {ws.get('created_at', '-')}")
    console.print(f"  更新时间: {ws.get('updated_at', '-')}")


@app.command("delete")
def delete(
    name: str = typer.Argument(..., help="工作空间名称"),
    force: bool = typer.Option(False, "--force", "-f", help="强制删除"),
):
    """删除工作空间"""
    workspaces = _load_workspaces()
    
    # 查找工作空间
    ws_index = None
    for i, w in enumerate(workspaces):
        if w["name"] == name or w["slug"] == name:
            ws_index = i
            break
    
    if ws_index is None:
        console.print(f"[red]工作空间不存在: {name}[/red]")
        raise typer.Exit(1)
    
    if not force:
        confirm = typer.confirm(f"确定删除工作空间 '{name}'?")
        if not confirm:
            console.print("[dim]已取消[/dim]")
            return
    
    # 删除
    deleted = workspaces.pop(ws_index)
    _save_workspaces(workspaces)
    
    # 如果是当前工作空间，清除
    config = get_config_manager()
    if config.get("workspace.current") == deleted["slug"]:
        config.set("workspace.current", None)
    
    console.print(f"[green]✓[/green] 已删除: {name}")
