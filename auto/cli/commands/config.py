"""配置命令"""

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from auto.shared.config import AIProviderConfig, get_config_manager
from auto.shared.utils import mask_api_key

app = typer.Typer(help="配置管理")
console = Console()

# provider 子命令组
provider_app = typer.Typer(help="AI 提供商管理")
app.add_typer(provider_app, name="provider")


@app.command("list")
def list_config():
    """列出所有配置"""
    config = get_config_manager()
    cfg = config.config
    
    console.print("[bold]当前配置:[/bold]")
    console.print()
    console.print(f"  模式: {cfg.mode}")
    console.print(f"  调试: {cfg.debug}")
    console.print(f"  默认提供商: {cfg.default_provider}")
    console.print(f"  默认模型: {cfg.default_model}")
    console.print()
    console.print("[bold]存储:[/bold]")
    console.print(f"  类型: {cfg.storage.type}")
    console.print(f"  路径: {cfg.storage.path}")
    console.print()
    console.print("[bold]工作空间:[/bold]")
    console.print(f"  默认路径: {cfg.workspace.default_path}")
    console.print(f"  当前: {cfg.workspace.current or '-'}")
    console.print()
    console.print("[bold]日志:[/bold]")
    console.print(f"  级别: {cfg.logging.level}")
    console.print(f"  文件: {cfg.logging.file}")
    console.print()
    console.print(f"[dim]配置文件: {config.config_path}[/dim]")


@app.command("get")
def get_config(
    key: str = typer.Argument(..., help="配置键名 (如 default_model)"),
):
    """获取配置项"""
    config = get_config_manager()
    value = config.get(key)
    
    if value is None:
        console.print(f"[yellow]配置项不存在: {key}[/yellow]")
    else:
        console.print(f"{key} = {value}")


@app.command("set")
def set_config(
    key: str = typer.Argument(..., help="配置键名"),
    value: str = typer.Argument(..., help="配置值"),
):
    """设置配置项"""
    config = get_config_manager()
    
    # 尝试转换类型
    parsed_value: any = value
    if value.lower() == "true":
        parsed_value = True
    elif value.lower() == "false":
        parsed_value = False
    elif value.isdigit():
        parsed_value = int(value)
    
    config.set(key, parsed_value)
    console.print(f"[green]✓[/green] {key} = {parsed_value}")


# Provider 子命令
@provider_app.command("list")
def list_providers():
    """列出 AI 提供商"""
    config = get_config_manager()
    providers = config.config.providers
    
    if not providers:
        console.print("[dim]暂无配置的提供商[/dim]")
        console.print("[dim]使用 auto config provider add 添加[/dim]")
        return
    
    table = Table(title="AI 提供商")
    table.add_column("名称", style="cyan")
    table.add_column("类型")
    table.add_column("Base URL")
    table.add_column("API Key")
    table.add_column("状态")
    
    for p in providers:
        status = "默认" if p.is_default else ("启用" if p.is_enabled else "禁用")
        api_key = mask_api_key(p.api_key) if p.api_key else "-"
        
        table.add_row(
            p.name,
            p.provider_type,
            p.base_url,
            api_key,
            status,
        )
    
    console.print(table)


@provider_app.command("add")
def add_provider(
    name: str = typer.Option(..., "--name", "-n", help="提供商名称"),
    api_key: str = typer.Option(..., "--api-key", "-k", help="API Key"),
    base_url: str = typer.Option(
        "https://api.openai.com/v1",
        "--base-url", "-u",
        help="API Base URL",
    ),
    provider_type: str = typer.Option(
        "official",
        "--type", "-t",
        help="类型 (official/proxy/custom)",
    ),
    set_default: bool = typer.Option(False, "--default", "-d", help="设为默认"),
):
    """添加 AI 提供商
    
    Examples:
        auto config provider add --name openai --api-key sk-xxx
        auto config provider add --name proxy --api-key sk-xxx --base-url https://proxy.com/v1 --type proxy
    """
    config = get_config_manager()
    
    provider = AIProviderConfig(
        name=name,
        provider_type=provider_type,
        base_url=base_url,
        api_key=api_key,
        is_enabled=True,
        is_default=set_default,
    )
    
    config.add_provider(provider)
    
    console.print(f"[green]✓[/green] 已添加提供商: {name}")
    if set_default:
        console.print(f"[green]✓[/green] 已设为默认")


@provider_app.command("delete")
def delete_provider(
    name: str = typer.Argument(..., help="提供商名称"),
):
    """删除 AI 提供商"""
    config = get_config_manager()
    
    providers = [p for p in config.config.providers if p.name != name]
    
    if len(providers) == len(config.config.providers):
        console.print(f"[red]提供商不存在: {name}[/red]")
        raise typer.Exit(1)
    
    config._config.providers = providers
    config.save()
    
    console.print(f"[green]✓[/green] 已删除: {name}")


@provider_app.command("set-default")
def set_default_provider(
    name: str = typer.Argument(..., help="提供商名称"),
):
    """设为默认提供商"""
    config = get_config_manager()
    
    found = False
    for p in config.config.providers:
        if p.name == name:
            p.is_default = True
            found = True
        else:
            p.is_default = False
    
    if not found:
        console.print(f"[red]提供商不存在: {name}[/red]")
        raise typer.Exit(1)
    
    config.save()
    console.print(f"[green]✓[/green] 已设为默认: {name}")


@provider_app.command("test")
def test_provider(
    name: str = typer.Argument(..., help="提供商名称"),
):
    """测试 AI 提供商"""
    import asyncio
    from auto.core.ai.router import AIRouter
    
    config = get_config_manager()
    provider = config.get_provider(name)
    
    if not provider:
        console.print(f"[red]提供商不存在: {name}[/red]")
        raise typer.Exit(1)
    
    console.print(f"[dim]测试连接 {name}...[/dim]")
    
    async def test():
        router = AIRouter()
        try:
            # 简单测试
            from auto.shared.models import Message, MessageRole
            messages = [Message(role=MessageRole.USER, content="Hi")]
            response = await router.chat(messages, provider_name=name)
            return True, response.usage.total_tokens
        except Exception as e:
            return False, str(e)
    
    success, result = asyncio.run(test())
    
    if success:
        console.print(f"[green]✓[/green] 连接成功 (tokens: {result})")
    else:
        console.print(f"[red]✗[/red] 连接失败: {result}")
