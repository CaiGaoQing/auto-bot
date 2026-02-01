"""开发助手技能"""

from auto.core.skill.base import Skill, ToolDefinition
from auto.core.tool.context import ToolContext
from auto.core.tool.result import ToolResult


class DeveloperSkill(Skill):
    """开发助手技能
    
    提供代码生成、审查、调试等功能。
    """
    
    @property
    def name(self) -> str:
        return "developer"
    
    @property
    def display_name(self) -> str:
        return "开发助手"
    
    @property
    def description(self) -> str:
        return "代码生成、审查、调试、重构等开发辅助功能"
    
    @property
    def category(self) -> str:
        return "developer"
    
    @property
    def tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="write_code",
                description="生成代码文件",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "文件路径",
                        },
                        "content": {
                            "type": "string",
                            "description": "代码内容",
                        },
                        "language": {
                            "type": "string",
                            "description": "编程语言",
                            "default": "python",
                        },
                    },
                    "required": ["file_path", "content"],
                },
                handler=self.write_code,
            ),
            ToolDefinition(
                name="read_code",
                description="读取代码文件",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "文件路径",
                        },
                    },
                    "required": ["file_path"],
                },
                handler=self.read_code,
            ),
            ToolDefinition(
                name="run_command",
                description="运行 shell 命令",
                parameters={
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "要执行的命令",
                        },
                        "cwd": {
                            "type": "string",
                            "description": "工作目录",
                        },
                    },
                    "required": ["command"],
                },
                dangerous=True,
                requires_confirmation=True,
                handler=self.run_command,
            ),
        ]
    
    @property
    def system_prompt(self) -> str:
        return """你是一个专业的软件开发助手，擅长：
- 代码生成和优化
- 代码审查和问题诊断
- 技术方案设计
- 调试和问题排查

请确保：
1. 代码质量高，遵循最佳实践
2. 添加必要的注释和文档
3. 考虑错误处理和边界情况
4. 推荐现代化的解决方案"""
    
    async def write_code(
        self,
        ctx: ToolContext,
        file_path: str,
        content: str,
        language: str = "python",
    ) -> ToolResult:
        """生成代码文件"""
        from pathlib import Path
        
        # 安全检查
        if not ctx.security.is_allowed_path(file_path):
            return ToolResult.error_result(f"路径不允许: {file_path}")
        
        try:
            path = Path(file_path).expanduser()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            
            return ToolResult.success_result(
                data={"path": str(path), "size": len(content)},
                message=f"代码已写入: {path}",
            )
        except Exception as e:
            return ToolResult.error_result(f"写入失败: {str(e)}")
    
    async def read_code(
        self,
        ctx: ToolContext,
        file_path: str,
    ) -> ToolResult:
        """读取代码文件"""
        from pathlib import Path
        
        # 安全检查
        if not ctx.security.is_allowed_path(file_path):
            return ToolResult.error_result(f"路径不允许: {file_path}")
        
        try:
            path = Path(file_path).expanduser()
            
            if not path.exists():
                return ToolResult.error_result(f"文件不存在: {file_path}")
            
            content = path.read_text(encoding="utf-8")
            
            # 检测语言
            suffix = path.suffix.lower()
            language_map = {
                ".py": "python",
                ".js": "javascript",
                ".ts": "typescript",
                ".java": "java",
                ".go": "go",
                ".rs": "rust",
                ".c": "c",
                ".cpp": "cpp",
                ".h": "c",
                ".rb": "ruby",
                ".php": "php",
                ".swift": "swift",
                ".kt": "kotlin",
                ".scala": "scala",
                ".sh": "bash",
                ".sql": "sql",
                ".html": "html",
                ".css": "css",
                ".json": "json",
                ".yaml": "yaml",
                ".yml": "yaml",
                ".md": "markdown",
            }
            language = language_map.get(suffix, "text")
            
            return ToolResult.code(
                content=content,
                language=language,
                message=f"读取文件: {path}",
            )
        except Exception as e:
            return ToolResult.error_result(f"读取失败: {str(e)}")
    
    async def run_command(
        self,
        ctx: ToolContext,
        command: str,
        cwd: str = None,
    ) -> ToolResult:
        """运行 shell 命令"""
        import asyncio
        from pathlib import Path
        
        # 安全检查
        if ctx.security.is_dangerous_operation(command):
            return ToolResult.error_result(f"检测到危险命令: {command}")
        
        try:
            work_dir = Path(cwd).expanduser() if cwd else ctx.workspace_path
            
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=work_dir,
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=60,
            )
            
            output = stdout.decode("utf-8", errors="replace")
            error = stderr.decode("utf-8", errors="replace")
            
            return ToolResult.success_result(
                data={
                    "exit_code": process.returncode,
                    "stdout": output,
                    "stderr": error,
                },
                message=f"命令执行完成，退出码: {process.returncode}",
            )
        except asyncio.TimeoutError:
            return ToolResult.error_result("命令执行超时")
        except Exception as e:
            return ToolResult.error_result(f"命令执行失败: {str(e)}")
