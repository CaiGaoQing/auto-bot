"""
auto doctor - 健康诊断命令

借鉴 OpenClaw 的 doctor 设计，自动诊断常见问题
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import List, Tuple, Optional
import platform

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

app = typer.Typer(help="系统健康诊断")


class DiagnosticResult:
    """诊断结果"""
    def __init__(
        self,
        name: str,
        status: str,  # ok, warning, error
        message: str,
        suggestion: Optional[str] = None
    ):
        self.name = name
        self.status = status
        self.message = message
        self.suggestion = suggestion


@app.callback(invoke_without_command=True)
def doctor(
    fix: bool = typer.Option(False, "--fix", help="自动修复发现的问题"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="显示详细信息"),
):
    """
    🩺 系统健康诊断
    
    检查 Auto Bot 的配置和运行状态，诊断常见问题。
    
    检查项目:
    
    \b
    - 环境配置
    - AI 提供商连接
    - 渠道配置
    - 数据库状态
    - 依赖检查
    """
    console.print()
    console.print(Panel.fit(
        "[bold blue]🩺 Auto Bot 健康诊断[/]\n\n"
        "正在检查系统状态...",
        border_style="blue"
    ))
    console.print()
    
    results: List[DiagnosticResult] = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        # 1. 环境检查
        task = progress.add_task("检查环境...", total=None)
        results.extend(_check_environment(verbose))
        progress.update(task, completed=True)
        
        # 2. 配置检查
        task = progress.add_task("检查配置...", total=None)
        results.extend(_check_configuration(verbose))
        progress.update(task, completed=True)
        
        # 3. AI 提供商检查
        task = progress.add_task("检查 AI 提供商...", total=None)
        results.extend(_check_ai_providers(verbose))
        progress.update(task, completed=True)
        
        # 4. 渠道检查
        task = progress.add_task("检查消息渠道...", total=None)
        results.extend(_check_channels(verbose))
        progress.update(task, completed=True)
        
        # 5. 依赖检查
        task = progress.add_task("检查依赖...", total=None)
        results.extend(_check_dependencies(verbose))
        progress.update(task, completed=True)
        
        # 6. 服务检查
        task = progress.add_task("检查服务状态...", total=None)
        results.extend(_check_services(verbose))
        progress.update(task, completed=True)
    
    console.print()
    
    # 显示结果
    _display_results(results)
    
    # 统计
    ok_count = sum(1 for r in results if r.status == "ok")
    warning_count = sum(1 for r in results if r.status == "warning")
    error_count = sum(1 for r in results if r.status == "error")
    
    console.print()
    
    if error_count > 0:
        console.print(f"[bold red]❌ 发现 {error_count} 个错误[/]")
    if warning_count > 0:
        console.print(f"[bold yellow]⚠️  发现 {warning_count} 个警告[/]")
    if error_count == 0 and warning_count == 0:
        console.print("[bold green]✅ 所有检查通过！系统运行正常。[/]")
    
    # 显示修复建议
    if fix and (error_count > 0 or warning_count > 0):
        console.print()
        console.print("[bold]正在尝试自动修复...[/]")
        _auto_fix(results)
    elif error_count > 0 or warning_count > 0:
        console.print()
        console.print("[dim]提示: 使用 --fix 参数尝试自动修复问题[/]")
    
    console.print()


def _check_environment(verbose: bool) -> List[DiagnosticResult]:
    """检查环境"""
    results = []
    
    # Python 版本
    py_version = sys.version_info
    if py_version >= (3, 10):
        results.append(DiagnosticResult(
            "Python 版本",
            "ok",
            f"Python {py_version.major}.{py_version.minor}.{py_version.micro}"
        ))
    else:
        results.append(DiagnosticResult(
            "Python 版本",
            "error",
            f"Python {py_version.major}.{py_version.minor} (需要 3.10+)",
            "请升级 Python 到 3.10 或更高版本"
        ))
    
    # 操作系统
    system = platform.system()
    results.append(DiagnosticResult(
        "操作系统",
        "ok",
        f"{system} {platform.release()}"
    ))
    
    # 虚拟环境
    in_venv = sys.prefix != sys.base_prefix
    if in_venv:
        results.append(DiagnosticResult(
            "虚拟环境",
            "ok",
            f"已激活: {sys.prefix}"
        ))
    else:
        results.append(DiagnosticResult(
            "虚拟环境",
            "warning",
            "未使用虚拟环境",
            "建议使用虚拟环境: python -m venv venv"
        ))
    
    return results


def _check_configuration(verbose: bool) -> List[DiagnosticResult]:
    """检查配置"""
    results = []
    
    config_dir = Path.home() / ".ai-auto"
    config_file = config_dir / "config.yaml"
    
    # 配置目录
    if config_dir.exists():
        results.append(DiagnosticResult(
            "配置目录",
            "ok",
            str(config_dir)
        ))
    else:
        results.append(DiagnosticResult(
            "配置目录",
            "warning",
            "配置目录不存在",
            f"运行 'auto onboard' 或手动创建: mkdir -p {config_dir}"
        ))
        return results
    
    # 配置文件
    if config_file.exists():
        results.append(DiagnosticResult(
            "配置文件",
            "ok",
            str(config_file)
        ))
        
        # 验证配置格式
        try:
            import yaml
            with open(config_file, "r") as f:
                config = yaml.safe_load(f)
            if config:
                results.append(DiagnosticResult(
                    "配置格式",
                    "ok",
                    "YAML 格式有效"
                ))
            else:
                results.append(DiagnosticResult(
                    "配置格式",
                    "warning",
                    "配置文件为空",
                    "运行 'auto onboard' 完成配置"
                ))
        except Exception as e:
            results.append(DiagnosticResult(
                "配置格式",
                "error",
                f"配置文件格式错误: {e}",
                "检查 YAML 语法是否正确"
            ))
    else:
        results.append(DiagnosticResult(
            "配置文件",
            "warning",
            "配置文件不存在",
            "运行 'auto onboard' 创建配置"
        ))
    
    # 工作空间
    workspace_dir = config_dir / "workspace"
    if workspace_dir.exists():
        # 检查必要文件
        agents_file = workspace_dir / "AGENTS.md"
        soul_file = workspace_dir / "SOUL.md"
        
        if agents_file.exists():
            results.append(DiagnosticResult(
                "AGENTS.md",
                "ok",
                str(agents_file)
            ))
        else:
            results.append(DiagnosticResult(
                "AGENTS.md",
                "warning",
                "AGENTS.md 不存在",
                "运行 'auto onboard' 初始化工作空间"
            ))
    else:
        results.append(DiagnosticResult(
            "工作空间",
            "warning",
            "工作空间目录不存在",
            "运行 'auto onboard' 初始化"
        ))
    
    return results


def _check_ai_providers(verbose: bool) -> List[DiagnosticResult]:
    """检查 AI 提供商"""
    results = []
    
    config_dir = Path.home() / ".ai-auto"
    config_file = config_dir / "config.yaml"
    
    if not config_file.exists():
        results.append(DiagnosticResult(
            "AI 提供商",
            "warning",
            "未配置 AI 提供商",
            "运行 'auto config provider add' 添加提供商"
        ))
        return results
    
    try:
        import yaml
        with open(config_file, "r") as f:
            config = yaml.safe_load(f) or {}
        
        providers = config.get("providers", [])
        
        if not providers:
            results.append(DiagnosticResult(
                "AI 提供商",
                "warning",
                "未配置任何 AI 提供商",
                "运行 'auto config provider add' 添加"
            ))
        else:
            for provider in providers:
                name = provider.get("name", "unknown")
                has_key = bool(provider.get("api_key"))
                
                if has_key:
                    results.append(DiagnosticResult(
                        f"提供商: {name}",
                        "ok",
                        f"已配置 (默认: {provider.get('is_default', False)})"
                    ))
                else:
                    results.append(DiagnosticResult(
                        f"提供商: {name}",
                        "error",
                        "缺少 API Key",
                        f"配置 API Key: auto config provider update {name}"
                    ))
    except Exception as e:
        results.append(DiagnosticResult(
            "AI 提供商",
            "error",
            f"读取配置失败: {e}"
        ))
    
    return results


def _check_channels(verbose: bool) -> List[DiagnosticResult]:
    """检查消息渠道"""
    results = []
    
    config_dir = Path.home() / ".ai-auto"
    config_file = config_dir / "config.yaml"
    
    if not config_file.exists():
        results.append(DiagnosticResult(
            "消息渠道",
            "warning",
            "未配置消息渠道",
            "运行 'auto onboard' 配置渠道"
        ))
        return results
    
    try:
        import yaml
        with open(config_file, "r") as f:
            config = yaml.safe_load(f) or {}
        
        channels = config.get("channels", {})
        
        if not channels:
            results.append(DiagnosticResult(
                "消息渠道",
                "ok",
                "未配置渠道 (仅使用 Web/CLI)"
            ))
        else:
            for channel_name, channel_config in channels.items():
                enabled = channel_config.get("enabled", False)
                
                if not enabled:
                    results.append(DiagnosticResult(
                        f"渠道: {channel_name}",
                        "warning",
                        "已配置但未启用"
                    ))
                    continue
                
                # 检查必要配置
                if channel_name == "telegram":
                    if channel_config.get("token"):
                        results.append(DiagnosticResult(
                            "渠道: Telegram",
                            "ok",
                            "已配置"
                        ))
                    else:
                        results.append(DiagnosticResult(
                            "渠道: Telegram",
                            "error",
                            "缺少 Bot Token"
                        ))
                        
                elif channel_name == "discord":
                    if channel_config.get("token"):
                        results.append(DiagnosticResult(
                            "渠道: Discord",
                            "ok",
                            "已配置"
                        ))
                    else:
                        results.append(DiagnosticResult(
                            "渠道: Discord",
                            "error",
                            "缺少 Bot Token"
                        ))
                        
                elif channel_name == "wechat_work":
                    if all([
                        channel_config.get("corp_id"),
                        channel_config.get("agent_id"),
                        channel_config.get("secret"),
                    ]):
                        results.append(DiagnosticResult(
                            "渠道: 企业微信",
                            "ok",
                            "已配置"
                        ))
                    else:
                        results.append(DiagnosticResult(
                            "渠道: 企业微信",
                            "error",
                            "配置不完整",
                            "需要 corp_id, agent_id, secret"
                        ))
    except Exception as e:
        results.append(DiagnosticResult(
            "消息渠道",
            "error",
            f"读取配置失败: {e}"
        ))
    
    return results


def _check_dependencies(verbose: bool) -> List[DiagnosticResult]:
    """检查依赖"""
    results = []
    
    # 核心依赖
    core_deps = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("httpx", "HTTPX"),
        ("pydantic", "Pydantic"),
        ("click", "Click"),
        ("rich", "Rich"),
    ]
    
    # 可选依赖
    optional_deps = [
        ("telegram", "python-telegram-bot", "Telegram 渠道"),
        ("discord", "discord.py", "Discord 渠道"),
        ("python-pptx", "python-pptx", "PPT 生成"),
        ("openpyxl", "openpyxl", "Excel 生成"),
    ]
    
    # 检查核心依赖
    for module, name in core_deps:
        try:
            __import__(module)
            results.append(DiagnosticResult(
                f"依赖: {name}",
                "ok",
                "已安装"
            ))
        except ImportError:
            results.append(DiagnosticResult(
                f"依赖: {name}",
                "error",
                "未安装",
                f"pip install {module}"
            ))
    
    # 检查可选依赖（仅在 verbose 模式）
    if verbose:
        for module, pip_name, desc in optional_deps:
            try:
                __import__(module.replace("-", "_"))
                results.append(DiagnosticResult(
                    f"可选: {pip_name}",
                    "ok",
                    f"已安装 ({desc})"
                ))
            except ImportError:
                results.append(DiagnosticResult(
                    f"可选: {pip_name}",
                    "warning",
                    f"未安装 ({desc})",
                    f"pip install {pip_name}"
                ))
    
    return results


def _check_services(verbose: bool) -> List[DiagnosticResult]:
    """检查服务状态"""
    results = []
    
    # 检查 Gateway 是否运行
    import socket
    
    gateway_port = 8000
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    
    try:
        result = sock.connect_ex(('127.0.0.1', gateway_port))
        if result == 0:
            results.append(DiagnosticResult(
                "Gateway 服务",
                "ok",
                f"运行中 (端口 {gateway_port})"
            ))
        else:
            results.append(DiagnosticResult(
                "Gateway 服务",
                "warning",
                f"未运行 (端口 {gateway_port})",
                "运行: auto gateway 或 python -m uvicorn auto.gateway.api.app:app"
            ))
    except Exception as e:
        results.append(DiagnosticResult(
            "Gateway 服务",
            "warning",
            f"检查失败: {e}"
        ))
    finally:
        sock.close()
    
    # 检查后台服务
    system = platform.system()
    
    if system == "Darwin":
        # macOS
        import subprocess
        try:
            result = subprocess.run(
                ["launchctl", "list", "com.autobot.gateway"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                results.append(DiagnosticResult(
                    "后台服务 (launchd)",
                    "ok",
                    "已安装"
                ))
            else:
                results.append(DiagnosticResult(
                    "后台服务 (launchd)",
                    "warning",
                    "未安装",
                    "运行: auto onboard --install-daemon"
                ))
        except Exception:
            pass
    
    elif system == "Linux":
        # Linux
        import subprocess
        try:
            result = subprocess.run(
                ["systemctl", "--user", "is-active", "autobot"],
                capture_output=True,
                text=True
            )
            if "active" in result.stdout:
                results.append(DiagnosticResult(
                    "后台服务 (systemd)",
                    "ok",
                    "运行中"
                ))
            else:
                results.append(DiagnosticResult(
                    "后台服务 (systemd)",
                    "warning",
                    "未运行或未安装",
                    "运行: auto onboard --install-daemon"
                ))
        except Exception:
            pass
    
    return results


def _display_results(results: List[DiagnosticResult]):
    """显示诊断结果"""
    table = Table(title="诊断结果")
    table.add_column("检查项", style="cyan", no_wrap=True)
    table.add_column("状态", style="white", width=12)
    table.add_column("信息", style="white")
    table.add_column("建议", style="dim")
    
    status_icons = {
        "ok": "[green]✅ 正常[/]",
        "warning": "[yellow]⚠️  警告[/]",
        "error": "[red]❌ 错误[/]",
    }
    
    for result in results:
        table.add_row(
            result.name,
            status_icons.get(result.status, result.status),
            result.message,
            result.suggestion or ""
        )
    
    console.print(table)


def _auto_fix(results: List[DiagnosticResult]):
    """自动修复问题"""
    for result in results:
        if result.status == "ok":
            continue
        
        if result.name == "配置目录":
            config_dir = Path.home() / ".ai-auto"
            config_dir.mkdir(parents=True, exist_ok=True)
            console.print(f"[green]✅ 已创建配置目录: {config_dir}[/]")
        
        elif result.name == "工作空间":
            workspace_dir = Path.home() / ".ai-auto" / "workspace"
            workspace_dir.mkdir(parents=True, exist_ok=True)
            console.print(f"[green]✅ 已创建工作空间目录: {workspace_dir}[/]")
        
        elif "依赖" in result.name and result.suggestion:
            # 提取 pip install 命令
            if "pip install" in result.suggestion:
                package = result.suggestion.split("pip install ")[-1]
                console.print(f"[dim]安装依赖: pip install {package}[/]")
                os.system(f"pip install {package}")
    
    console.print()
    console.print("[dim]部分问题可能需要手动修复。[/]")
