"""
auto onboard - 向导式安装命令

借鉴 OpenClaw 的 onboard 设计，引导用户完成初始配置
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.markdown import Markdown

console = Console()

app = typer.Typer(help="向导式安装配置")


@app.callback(invoke_without_command=True)
def onboard(
    skip_ai: bool = typer.Option(False, "--skip-ai", help="跳过 AI 配置"),
    skip_channels: bool = typer.Option(False, "--skip-channels", help="跳过渠道配置"),
    install_daemon: bool = typer.Option(False, "--install-daemon", help="安装为后台服务"),
):
    """
    🚀 向导式安装配置
    
    引导你完成 Auto Bot 的初始设置:
    
    \b
    1. AI 提供商配置
    2. 渠道配置 (Telegram/Discord/企业微信)
    3. 工作空间初始化
    4. 后台服务安装 (可选)
    """
    console.print()
    console.print(Panel.fit(
        "[bold blue]🤖 欢迎使用 Auto Bot![/]\n\n"
        "让我们一起完成初始设置吧。\n"
        "这个向导会帮你配置 AI、渠道和工作空间。",
        title="Auto Bot 安装向导",
        border_style="blue"
    ))
    console.print()
    
    # 步骤 1: 检查环境
    _check_environment()
    
    # 步骤 2: 配置 AI 提供商
    if not skip_ai:
        _configure_ai_provider()
    
    # 步骤 3: 配置渠道
    if not skip_channels:
        _configure_channels()
    
    # 步骤 4: 初始化工作空间
    _initialize_workspace()
    
    # 步骤 5: 安装后台服务
    if install_daemon:
        _install_daemon()
    
    # 完成
    _show_completion()


def _check_environment():
    """检查环境"""
    console.print("[bold]步骤 1/5: 检查环境[/]")
    console.print()
    
    checks = []
    
    # Python 版本
    py_version = sys.version_info
    py_ok = py_version >= (3, 10)
    checks.append(("Python 版本", f"{py_version.major}.{py_version.minor}", py_ok))
    
    # 配置目录
    config_dir = Path.home() / ".ai-auto"
    config_exists = config_dir.exists()
    checks.append(("配置目录", str(config_dir), True))
    
    # 必要的库
    try:
        import httpx
        checks.append(("httpx", "已安装", True))
    except ImportError:
        checks.append(("httpx", "未安装", False))
    
    try:
        import fastapi
        checks.append(("FastAPI", "已安装", True))
    except ImportError:
        checks.append(("FastAPI", "未安装", False))
    
    # 显示结果
    table = Table(title="环境检查")
    table.add_column("项目", style="cyan")
    table.add_column("状态", style="white")
    table.add_column("结果", style="green")
    
    all_ok = True
    for name, status, ok in checks:
        result = "✅" if ok else "❌"
        if not ok:
            all_ok = False
        table.add_row(name, status, result)
    
    console.print(table)
    console.print()
    
    if not all_ok:
        console.print("[yellow]⚠️ 部分检查未通过，但可以继续安装。[/]")
        if not Confirm.ask("是否继续？"):
            raise typer.Abort()
    else:
        console.print("[green]✅ 环境检查通过[/]")
    
    console.print()


def _configure_ai_provider():
    """配置 AI 提供商"""
    console.print("[bold]步骤 2/5: 配置 AI 提供商[/]")
    console.print()
    
    console.print("Auto Bot 支持多种 AI 提供商:")
    console.print("  1. OpenAI (GPT-4, GPT-3.5)")
    console.print("  2. Anthropic (Claude)")
    console.print("  3. 中转站 (自定义 API)")
    console.print("  4. 跳过此步骤")
    console.print()
    
    choice = Prompt.ask(
        "请选择 AI 提供商",
        choices=["1", "2", "3", "4"],
        default="1"
    )
    
    if choice == "4":
        console.print("[yellow]已跳过 AI 配置，你可以稍后通过 'auto config provider add' 添加。[/]")
        console.print()
        return
    
    provider_map = {
        "1": ("openai", "https://api.openai.com/v1", "gpt-4"),
        "2": ("anthropic", "https://api.anthropic.com/v1", "claude-3-opus-20240229"),
        "3": ("proxy", "", ""),
    }
    
    provider_name, default_url, default_model = provider_map[choice]
    
    # 获取配置
    if choice == "3":
        base_url = Prompt.ask("请输入中转站 API 地址")
        model = Prompt.ask("请输入默认模型名称", default="gpt-4")
    else:
        base_url = Prompt.ask("API 地址", default=default_url)
        model = Prompt.ask("默认模型", default=default_model)
    
    api_key = Prompt.ask("请输入 API Key", password=True)
    
    if not api_key:
        console.print("[red]❌ API Key 不能为空[/]")
        return
    
    # 保存配置
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("保存配置...", total=None)
        
        # 创建配置目录
        config_dir = Path.home() / ".ai-auto"
        config_dir.mkdir(exist_ok=True)
        
        # 保存到配置文件
        config_file = config_dir / "config.yaml"
        import yaml
        
        config = {}
        if config_file.exists():
            with open(config_file, "r") as f:
                config = yaml.safe_load(f) or {}
        
        if "providers" not in config:
            config["providers"] = []
        
        # 添加新提供商
        config["providers"].append({
            "name": provider_name,
            "base_url": base_url,
            "api_key": api_key,
            "model": model,
            "is_default": len(config["providers"]) == 0,
        })
        
        with open(config_file, "w") as f:
            yaml.dump(config, f, allow_unicode=True)
        
        progress.update(task, completed=True)
    
    console.print(f"[green]✅ AI 提供商 '{provider_name}' 配置成功[/]")
    console.print()


def _configure_channels():
    """配置渠道"""
    console.print("[bold]步骤 3/5: 配置消息渠道[/]")
    console.print()
    
    console.print("Auto Bot 支持多种消息渠道:")
    console.print("  1. Telegram Bot")
    console.print("  2. Discord Bot")
    console.print("  3. 企业微信")
    console.print("  4. 跳过此步骤")
    console.print()
    
    channels_to_configure = []
    
    while True:
        choice = Prompt.ask(
            "请选择要配置的渠道 (输入数字，完成后输入 4)",
            choices=["1", "2", "3", "4"],
            default="4"
        )
        
        if choice == "4":
            break
        
        channel_map = {
            "1": "telegram",
            "2": "discord",
            "3": "wechat_work",
        }
        channels_to_configure.append(channel_map[choice])
    
    if not channels_to_configure:
        console.print("[yellow]已跳过渠道配置，你可以稍后通过 Web 界面配置。[/]")
        console.print()
        return
    
    # 配置每个渠道
    config_dir = Path.home() / ".ai-auto"
    config_file = config_dir / "config.yaml"
    
    import yaml
    config = {}
    if config_file.exists():
        with open(config_file, "r") as f:
            config = yaml.safe_load(f) or {}
    
    if "channels" not in config:
        config["channels"] = {}
    
    for channel in channels_to_configure:
        console.print()
        console.print(f"[bold cyan]配置 {channel.upper()}[/]")
        
        if channel == "telegram":
            token = Prompt.ask("请输入 Telegram Bot Token")
            config["channels"]["telegram"] = {
                "token": token,
                "enabled": True,
            }
            console.print("[green]✅ Telegram 配置成功[/]")
            console.print("[dim]提示: 与 @BotFather 对话获取 Bot Token[/]")
            
        elif channel == "discord":
            token = Prompt.ask("请输入 Discord Bot Token")
            config["channels"]["discord"] = {
                "token": token,
                "enabled": True,
            }
            console.print("[green]✅ Discord 配置成功[/]")
            console.print("[dim]提示: 在 Discord Developer Portal 创建应用获取 Token[/]")
            
        elif channel == "wechat_work":
            corp_id = Prompt.ask("请输入企业 ID (CorpID)")
            agent_id = Prompt.ask("请输入应用 ID (AgentID)")
            secret = Prompt.ask("请输入应用 Secret", password=True)
            config["channels"]["wechat_work"] = {
                "corp_id": corp_id,
                "agent_id": int(agent_id),
                "secret": secret,
                "enabled": True,
            }
            console.print("[green]✅ 企业微信配置成功[/]")
    
    # 保存配置
    with open(config_file, "w") as f:
        yaml.dump(config, f, allow_unicode=True)
    
    console.print()


def _initialize_workspace():
    """初始化工作空间"""
    console.print("[bold]步骤 4/5: 初始化工作空间[/]")
    console.print()
    
    # 默认工作空间目录
    default_workspace = Path.home() / ".ai-auto" / "workspace"
    
    workspace_path = Prompt.ask(
        "工作空间目录",
        default=str(default_workspace)
    )
    
    workspace = Path(workspace_path)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("初始化工作空间...", total=None)
        
        # 创建目录结构
        workspace.mkdir(parents=True, exist_ok=True)
        (workspace / "skills").mkdir(exist_ok=True)
        
        # 创建 AGENTS.md
        agents_file = workspace / "AGENTS.md"
        if not agents_file.exists():
            agents_file.write_text("""# AGENTS.md

## 角色定义

你是一个智能助手，可以帮助用户完成各种任务。

## 行为准则

1. 始终保持礼貌和专业
2. 如果不确定，请先确认
3. 注重效率和准确性
4. 保护用户隐私

## 能力范围

- 代码开发与调试
- 文档编写
- 数据分析
- 任务规划
""", encoding="utf-8")
        
        # 创建 SOUL.md
        soul_file = workspace / "SOUL.md"
        if not soul_file.exists():
            soul_file.write_text("""# SOUL.md

## 人格设定

我是 Auto Bot，一个友好、高效的 AI 助手。

## 沟通风格

- 简洁明了
- 适度幽默
- 专业可靠
- 有耐心

## 价值观

- 帮助用户解决问题是第一优先级
- 诚实面对自己的局限性
- 持续学习和改进
""", encoding="utf-8")
        
        progress.update(task, completed=True)
    
    console.print(f"[green]✅ 工作空间已初始化: {workspace}[/]")
    console.print(f"[dim]   - AGENTS.md: Agent 行为定义[/]")
    console.print(f"[dim]   - SOUL.md: AI 人格设定[/]")
    console.print(f"[dim]   - skills/: 自定义技能目录[/]")
    console.print()


def _install_daemon():
    """安装后台服务"""
    console.print("[bold]步骤 5/5: 安装后台服务[/]")
    console.print()
    
    import platform
    system = platform.system()
    
    if system == "Darwin":
        # macOS: 使用 launchd
        _install_launchd_service()
    elif system == "Linux":
        # Linux: 使用 systemd
        _install_systemd_service()
    else:
        console.print(f"[yellow]⚠️ 暂不支持 {system} 系统的后台服务安装[/]")
        console.print("[dim]你可以手动运行: auto gateway --port 8000[/]")


def _install_launchd_service():
    """安装 macOS launchd 服务"""
    plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.autobot.gateway</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python}</string>
        <string>-m</string>
        <string>uvicorn</string>
        <string>auto.gateway.api.app:app</string>
        <string>--port</string>
        <string>8000</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{log_dir}/autobot.log</string>
    <key>StandardErrorPath</key>
    <string>{log_dir}/autobot.error.log</string>
</dict>
</plist>
"""
    
    python_path = sys.executable
    log_dir = Path.home() / ".ai-auto" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    plist_path = Path.home() / "Library" / "LaunchAgents" / "com.autobot.gateway.plist"
    plist_path.parent.mkdir(parents=True, exist_ok=True)
    
    plist_path.write_text(
        plist_content.format(python=python_path, log_dir=str(log_dir))
    )
    
    # 加载服务
    os.system(f"launchctl load {plist_path}")
    
    console.print("[green]✅ 后台服务已安装[/]")
    console.print(f"[dim]   配置文件: {plist_path}[/]")
    console.print(f"[dim]   日志目录: {log_dir}[/]")
    console.print()
    console.print("[dim]管理命令:[/]")
    console.print(f"[dim]   启动: launchctl start com.autobot.gateway[/]")
    console.print(f"[dim]   停止: launchctl stop com.autobot.gateway[/]")
    console.print(f"[dim]   卸载: launchctl unload {plist_path}[/]")


def _install_systemd_service():
    """安装 Linux systemd 服务"""
    service_content = """[Unit]
Description=Auto Bot Gateway Service
After=network.target

[Service]
Type=simple
User={user}
ExecStart={python} -m uvicorn auto.gateway.api.app:app --port 8000
Restart=always
RestartSec=10
StandardOutput=append:{log_dir}/autobot.log
StandardError=append:{log_dir}/autobot.error.log

[Install]
WantedBy=multi-user.target
"""
    
    import getpass
    user = getpass.getuser()
    python_path = sys.executable
    log_dir = Path.home() / ".ai-auto" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    service_path = Path.home() / ".config" / "systemd" / "user" / "autobot.service"
    service_path.parent.mkdir(parents=True, exist_ok=True)
    
    service_path.write_text(
        service_content.format(user=user, python=python_path, log_dir=str(log_dir))
    )
    
    # 重新加载并启动
    os.system("systemctl --user daemon-reload")
    os.system("systemctl --user enable autobot")
    os.system("systemctl --user start autobot")
    
    console.print("[green]✅ 后台服务已安装[/]")
    console.print(f"[dim]   配置文件: {service_path}[/]")
    console.print(f"[dim]   日志目录: {log_dir}[/]")
    console.print()
    console.print("[dim]管理命令:[/]")
    console.print("[dim]   启动: systemctl --user start autobot[/]")
    console.print("[dim]   停止: systemctl --user stop autobot[/]")
    console.print("[dim]   状态: systemctl --user status autobot[/]")


def _show_completion():
    """显示完成信息"""
    console.print()
    console.print(Panel.fit(
        "[bold green]🎉 安装完成！[/]\n\n"
        "现在你可以:\n\n"
        "  [cyan]auto chat[/]           - 开始对话\n"
        "  [cyan]auto gateway[/]        - 启动 API 服务\n"
        "  [cyan]auto doctor[/]         - 检查系统状态\n"
        "  [cyan]auto query all[/]      - 查看所有功能\n\n"
        "[dim]Web 界面: cd web && npm run dev[/]\n"
        "[dim]文档: https://github.com/CaiGaoQing/auto-bot[/]",
        title="安装完成",
        border_style="green"
    ))
    console.print()
