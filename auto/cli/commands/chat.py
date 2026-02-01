"""对话命令"""

import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

app = typer.Typer(help="对话命令")
console = Console()


async def single_chat(
    message: str,
    model: Optional[str] = None,
    role: Optional[str] = None,
    skill: Optional[str] = None,
) -> None:
    """单次对话"""
    from auto.core.ai.router import AIRouter
    from auto.shared.config import get_config
    from auto.shared.models import Message, MessageRole
    
    config = get_config()
    router = AIRouter()
    
    # 使用配置的模型
    model = model or config.default_model
    
    console.print(f"[dim]使用模型: {model}[/dim]")
    console.print()
    
    # 构建消息
    messages = [Message(role=MessageRole.USER, content=message)]
    
    try:
        # 调用 AI
        response = await router.chat(messages, model=model)
        
        # 显示响应
        console.print(Markdown(response.message.content))
        console.print()
        console.print(
            f"[dim]Tokens: {response.usage.total_tokens} "
            f"(输入: {response.usage.prompt_tokens}, 输出: {response.usage.completion_tokens})[/dim]"
        )
    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")
        raise typer.Exit(1)


async def interactive_chat(
    model: Optional[str] = None,
    role: Optional[str] = None,
    skill: Optional[str] = None,
) -> None:
    """交互式对话"""
    from auto.core.ai.router import AIRouter
    from auto.shared.config import get_config
    from auto.shared.models import Message, MessageRole
    
    config = get_config()
    router = AIRouter()
    
    model = model or config.default_model
    role = role or "general"
    
    # 显示欢迎信息
    console.print()
    console.print(Panel.fit(
        f"[bold blue]AI 个人助手[/bold blue]\n\n"
        f"模型: {model}\n"
        f"角色: {role}\n\n"
        f"[dim]输入 /help 查看命令, /exit 退出[/dim]",
        title="欢迎",
        border_style="blue",
    ))
    console.print()
    
    # 对话历史
    messages: list[Message] = []
    
    while True:
        try:
            # 获取用户输入
            user_input = Prompt.ask("[bold green]You[/bold green]")
            
            if not user_input.strip():
                continue
            
            # 处理命令
            if user_input.startswith("/"):
                cmd = user_input[1:].lower().split()
                if not cmd:
                    continue
                    
                if cmd[0] in ("exit", "quit", "q"):
                    console.print("[dim]再见！[/dim]")
                    break
                elif cmd[0] == "help":
                    show_chat_help()
                    continue
                elif cmd[0] == "clear":
                    messages.clear()
                    console.print("[dim]对话已清空[/dim]")
                    continue
                elif cmd[0] == "model":
                    if len(cmd) > 1:
                        model = cmd[1]
                        console.print(f"[dim]已切换模型: {model}[/dim]")
                    else:
                        console.print(f"[dim]当前模型: {model}[/dim]")
                    continue
                elif cmd[0] == "role":
                    if len(cmd) > 1:
                        role = cmd[1]
                        console.print(f"[dim]已切换角色: {role}[/dim]")
                    else:
                        console.print(f"[dim]当前角色: {role}[/dim]")
                    continue
                elif cmd[0] == "history":
                    if not messages:
                        console.print("[dim]暂无对话历史[/dim]")
                    else:
                        for msg in messages[-10:]:
                            role_label = "You" if msg.role == MessageRole.USER else "AI"
                            console.print(f"[dim]{role_label}: {msg.content[:50]}...[/dim]")
                    continue
                else:
                    console.print(f"[yellow]未知命令: {cmd[0]}[/yellow]")
                    continue
            
            # 添加用户消息
            messages.append(Message(role=MessageRole.USER, content=user_input))
            
            # 调用 AI
            console.print()
            try:
                response = await router.chat(messages, model=model)
                
                # 添加助手消息
                messages.append(response.message)
                
                # 显示响应
                console.print("[bold blue]AI[/bold blue]")
                console.print(Markdown(response.message.content))
                console.print()
                console.print(
                    f"[dim]Tokens: {response.usage.total_tokens}[/dim]"
                )
            except Exception as e:
                console.print(f"[red]错误: {e}[/red]")
                # 移除失败的用户消息
                messages.pop()
            
            console.print()
            
        except KeyboardInterrupt:
            console.print("\n[dim]使用 /exit 退出[/dim]")
            continue
        except EOFError:
            console.print("\n[dim]再见！[/dim]")
            break


def show_chat_help():
    """显示对话帮助"""
    console.print()
    console.print("[bold]可用命令:[/bold]")
    commands = [
        ("/help", "显示帮助"),
        ("/exit", "退出对话"),
        ("/clear", "清空对话历史"),
        ("/model <name>", "切换模型"),
        ("/role <name>", "切换角色"),
        ("/history", "查看对话历史"),
    ]
    for cmd, desc in commands:
        console.print(f"  [cyan]{cmd:20}[/cyan] {desc}")
    console.print()


@app.callback(invoke_without_command=True)
def chat(
    ctx: typer.Context,
    message: Optional[str] = typer.Argument(None, help="消息内容"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="指定模型"),
    role: Optional[str] = typer.Option(None, "--role", "-r", help="指定角色"),
    skill: Optional[str] = typer.Option(None, "--skill", "-s", help="使用技能"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="交互模式"),
):
    """对话命令
    
    不带参数进入交互式对话，带消息参数进行单次对话。
    
    Examples:
        auto chat                    # 交互式对话
        auto chat "你好"             # 单次对话
        auto chat -m gpt-4o "问题"   # 指定模型
    """
    if ctx.invoked_subcommand is not None:
        return
    
    if message:
        # 单次对话
        asyncio.run(single_chat(message, model=model, role=role, skill=skill))
    else:
        # 交互式对话
        asyncio.run(interactive_chat(model=model, role=role, skill=skill))
