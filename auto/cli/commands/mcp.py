"""MCP 服务器命令"""

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="MCP 服务器管理")
console = Console()


@app.command("list")
def list_servers():
    """列出 MCP 服务器"""
    from auto.integration.mcp.client import MCPClient
    
    client = MCPClient()
    servers = client.list_servers()
    
    if not servers:
        console.print("[dim]暂无 MCP 服务器[/dim]")
        console.print("[dim]使用 auto mcp add 或 auto mcp install 添加[/dim]")
        return
    
    table = Table(title="MCP 服务器")
    table.add_column("名称", style="cyan")
    table.add_column("传输")
    table.add_column("命令/URL")
    table.add_column("工具数")
    table.add_column("状态")
    
    for server in servers:
        status = "[green]已连接[/green]" if server.get("is_connected") else "[dim]未连接[/dim]"
        if not server.get("is_enabled", True):
            status = "[yellow]已禁用[/yellow]"
        
        cmd_or_url = server.get("command") or server.get("url") or "-"
        
        table.add_row(
            server.get("name", ""),
            server.get("transport", ""),
            cmd_or_url[:40],
            str(len(server.get("tools", []))),
            status,
        )
    
    console.print(table)


@app.command("add")
def add_server(
    name: str = typer.Argument(..., help="服务器名称"),
    transport: str = typer.Option("stdio", "--transport", "-t", help="传输方式 (stdio/sse)"),
    command: Optional[str] = typer.Option(None, "--command", "-c", help="stdio 命令"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="SSE URL"),
):
    """添加 MCP 服务器
    
    Examples:
        auto mcp add filesystem --command "npx -y @modelcontextprotocol/server-filesystem /tmp"
        auto mcp add my-db --transport sse --url http://localhost:3001/sse
    """
    from auto.integration.mcp.client import MCPClient
    
    if transport == "stdio" and not command:
        console.print("[red]stdio 传输需要指定 --command[/red]")
        raise typer.Exit(1)
    
    if transport == "sse" and not url:
        console.print("[red]sse 传输需要指定 --url[/red]")
        raise typer.Exit(1)
    
    client = MCPClient()
    
    try:
        client.add_server(
            name=name,
            transport=transport,
            command=command,
            url=url,
        )
        console.print(f"[green]✓[/green] 已添加: {name}")
    except Exception as e:
        console.print(f"[red]添加失败: {e}[/red]")
        raise typer.Exit(1)


@app.command("install")
def install_server(
    package: str = typer.Argument(..., help="包名 (如 @modelcontextprotocol/server-filesystem)"),
):
    """从 MCP 市场安装服务器
    
    Examples:
        auto mcp install @modelcontextprotocol/server-filesystem
    """
    console.print(f"[dim]安装 {package}...[/dim]")
    console.print("[yellow]MCP 市场功能开发中...[/yellow]")


@app.command("remove")
def remove_server(
    name: str = typer.Argument(..., help="服务器名称"),
):
    """移除 MCP 服务器"""
    from auto.integration.mcp.client import MCPClient
    
    client = MCPClient()
    
    try:
        client.remove_server(name)
        console.print(f"[green]✓[/green] 已移除: {name}")
    except Exception as e:
        console.print(f"[red]移除失败: {e}[/red]")
        raise typer.Exit(1)


@app.command("enable")
def enable_server(
    name: str = typer.Argument(..., help="服务器名称"),
):
    """启用 MCP 服务器"""
    from auto.integration.mcp.client import MCPClient
    
    client = MCPClient()
    client.set_enabled(name, True)
    console.print(f"[green]✓[/green] 已启用: {name}")


@app.command("disable")
def disable_server(
    name: str = typer.Argument(..., help="服务器名称"),
):
    """禁用 MCP 服务器"""
    from auto.integration.mcp.client import MCPClient
    
    client = MCPClient()
    client.set_enabled(name, False)
    console.print(f"[green]✓[/green] 已禁用: {name}")


@app.command("test")
def test_server(
    name: str = typer.Argument(..., help="服务器名称"),
):
    """测试 MCP 服务器连接"""
    import asyncio
    from auto.integration.mcp.client import MCPClient
    
    console.print(f"[dim]测试连接 {name}...[/dim]")
    
    client = MCPClient()
    
    async def test():
        return await client.test_connection(name)
    
    try:
        success, message = asyncio.run(test())
        if success:
            console.print(f"[green]✓[/green] 连接成功: {message}")
        else:
            console.print(f"[red]✗[/red] 连接失败: {message}")
    except Exception as e:
        console.print(f"[red]测试失败: {e}[/red]")


@app.command("tools")
def list_tools(
    name: str = typer.Argument(..., help="服务器名称"),
):
    """列出服务器提供的工具"""
    import asyncio
    from auto.integration.mcp.client import MCPClient
    
    client = MCPClient()
    
    async def get_tools():
        return await client.get_server_tools(name)
    
    try:
        tools = asyncio.run(get_tools())
        
        if not tools:
            console.print(f"[dim]服务器 {name} 没有提供工具[/dim]")
            return
        
        console.print(f"[bold]服务器 {name} 的工具:[/bold]")
        console.print()
        
        for tool in tools:
            console.print(f"  [cyan]{tool.get('name', '')}[/cyan]")
            console.print(f"    {tool.get('description', '')}")
            
    except Exception as e:
        console.print(f"[red]获取工具失败: {e}[/red]")
        raise typer.Exit(1)
