"""文件管理技能"""

from pathlib import Path
from typing import Optional
import shutil

from auto.core.skill.base import Skill, ToolDefinition
from auto.core.tool.context import ToolContext
from auto.core.tool.result import ToolResult


class FileManagerSkill(Skill):
    """文件管理技能
    
    提供文件和文件夹管理功能。
    """
    
    @property
    def name(self) -> str:
        return "file_manager"
    
    @property
    def display_name(self) -> str:
        return "文件管理"
    
    @property
    def description(self) -> str:
        return "文件和文件夹管理，支持整理桌面、搜索文件、批量操作等"
    
    @property
    def category(self) -> str:
        return "productivity"
    
    @property
    def tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="list_directory",
                description="列出目录内容",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "目录路径",
                            "default": ".",
                        },
                        "recursive": {
                            "type": "boolean",
                            "description": "是否递归列出",
                            "default": False,
                        },
                        "pattern": {
                            "type": "string",
                            "description": "文件名匹配模式 (如 *.txt)",
                        },
                    },
                },
                handler=self.list_directory,
            ),
            ToolDefinition(
                name="organize_files",
                description="按规则整理文件",
                parameters={
                    "type": "object",
                    "properties": {
                        "source_path": {
                            "type": "string",
                            "description": "源目录路径",
                        },
                        "rules": {
                            "type": "object",
                            "description": "整理规则 (文件类型 -> 目标目录)",
                        },
                        "dry_run": {
                            "type": "boolean",
                            "description": "仅预览，不实际移动",
                            "default": True,
                        },
                    },
                    "required": ["source_path"],
                },
                dangerous=True,
                requires_confirmation=True,
                handler=self.organize_files,
            ),
            ToolDefinition(
                name="move_files",
                description="批量移动文件",
                parameters={
                    "type": "object",
                    "properties": {
                        "files": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "文件路径列表",
                        },
                        "destination": {
                            "type": "string",
                            "description": "目标目录",
                        },
                    },
                    "required": ["files", "destination"],
                },
                dangerous=True,
                requires_confirmation=True,
                handler=self.move_files,
            ),
            ToolDefinition(
                name="search_files",
                description="搜索文件",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "搜索目录",
                            "default": ".",
                        },
                        "pattern": {
                            "type": "string",
                            "description": "文件名模式",
                        },
                        "content": {
                            "type": "string",
                            "description": "文件内容搜索",
                        },
                    },
                },
                handler=self.search_files,
            ),
        ]
    
    @property
    def system_prompt(self) -> str:
        return """你是一个文件管理助手，可以帮助用户：
- 列出和浏览文件目录
- 整理和归档文件
- 搜索文件
- 批量操作文件

安全规则：
- 只能操作用户允许的目录
- 危险操作（移动、删除）需要确认
- 不能操作系统目录"""
    
    async def list_directory(
        self,
        ctx: ToolContext,
        path: str = ".",
        recursive: bool = False,
        pattern: Optional[str] = None,
    ) -> ToolResult:
        """列出目录内容"""
        target_path = Path(path).expanduser().resolve()
        
        # 安全检查
        if not ctx.security.is_allowed_path(target_path):
            return ToolResult.error_result(f"路径不允许: {path}")
        
        if not target_path.exists():
            return ToolResult.error_result(f"路径不存在: {path}")
        
        if not target_path.is_dir():
            return ToolResult.error_result(f"不是目录: {path}")
        
        try:
            files = []
            
            if recursive:
                iterator = target_path.rglob(pattern or "*")
            else:
                iterator = target_path.glob(pattern or "*")
            
            for item in iterator:
                try:
                    stat = item.stat()
                    files.append({
                        "name": item.name,
                        "path": str(item),
                        "type": "dir" if item.is_dir() else "file",
                        "size": stat.st_size if item.is_file() else 0,
                        "modified": stat.st_mtime,
                    })
                except (PermissionError, OSError):
                    continue
            
            # 按类型和名称排序
            files.sort(key=lambda x: (x["type"] != "dir", x["name"].lower()))
            
            return ToolResult.table(
                data=files,
                message=f"找到 {len(files)} 个文件/文件夹",
            )
        except Exception as e:
            return ToolResult.error_result(f"列出目录失败: {str(e)}")
    
    async def organize_files(
        self,
        ctx: ToolContext,
        source_path: str,
        rules: Optional[dict] = None,
        dry_run: bool = True,
    ) -> ToolResult:
        """按规则整理文件"""
        source = Path(source_path).expanduser().resolve()
        
        # 安全检查
        if not ctx.security.is_allowed_path(source):
            return ToolResult.error_result(f"路径不允许: {source_path}")
        
        if not source.exists():
            return ToolResult.error_result(f"路径不存在: {source_path}")
        
        # 默认整理规则
        if rules is None:
            rules = {
                "images": ["*.png", "*.jpg", "*.jpeg", "*.gif", "*.webp", "*.svg"],
                "documents": ["*.pdf", "*.doc", "*.docx", "*.xls", "*.xlsx", "*.ppt", "*.pptx"],
                "code": ["*.py", "*.js", "*.ts", "*.java", "*.go", "*.rs"],
                "archives": ["*.zip", "*.rar", "*.7z", "*.tar", "*.gz"],
                "videos": ["*.mp4", "*.mov", "*.avi", "*.mkv"],
                "audio": ["*.mp3", "*.wav", "*.flac", "*.m4a"],
            }
        
        try:
            # 分析文件
            actions = []
            
            for item in source.iterdir():
                if item.is_file():
                    for category, patterns in rules.items():
                        for pattern in patterns:
                            if item.match(pattern):
                                dest_dir = source / category
                                actions.append({
                                    "file": item.name,
                                    "from": str(item),
                                    "to": str(dest_dir / item.name),
                                    "category": category,
                                })
                                break
            
            if dry_run:
                return ToolResult.success_result(
                    data={
                        "mode": "dry_run",
                        "actions": actions,
                        "summary": {
                            category: len([a for a in actions if a["category"] == category])
                            for category in rules.keys()
                        },
                    },
                    message=f"预览: 将移动 {len(actions)} 个文件",
                )
            
            # 执行移动
            moved = []
            errors = []
            
            for action in actions:
                try:
                    dest_dir = Path(action["to"]).parent
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    shutil.move(action["from"], action["to"])
                    moved.append(action)
                except Exception as e:
                    errors.append({"file": action["file"], "error": str(e)})
            
            return ToolResult.success_result(
                data={
                    "moved": moved,
                    "errors": errors,
                },
                message=f"已移动 {len(moved)} 个文件，{len(errors)} 个失败",
            )
        except Exception as e:
            return ToolResult.error_result(f"整理文件失败: {str(e)}")
    
    async def move_files(
        self,
        ctx: ToolContext,
        files: list[str],
        destination: str,
    ) -> ToolResult:
        """批量移动文件"""
        dest_path = Path(destination).expanduser().resolve()
        
        # 安全检查
        if not ctx.security.is_allowed_path(dest_path):
            return ToolResult.error_result(f"目标路径不允许: {destination}")
        
        try:
            dest_path.mkdir(parents=True, exist_ok=True)
            
            moved = []
            errors = []
            
            for file_path in files:
                src = Path(file_path).expanduser().resolve()
                
                if not ctx.security.is_allowed_path(src):
                    errors.append({"file": file_path, "error": "路径不允许"})
                    continue
                
                if not src.exists():
                    errors.append({"file": file_path, "error": "文件不存在"})
                    continue
                
                try:
                    dest_file = dest_path / src.name
                    shutil.move(str(src), str(dest_file))
                    moved.append({
                        "from": str(src),
                        "to": str(dest_file),
                    })
                except Exception as e:
                    errors.append({"file": file_path, "error": str(e)})
            
            return ToolResult.success_result(
                data={
                    "moved": moved,
                    "errors": errors,
                },
                message=f"成功移动 {len(moved)} 个文件，{len(errors)} 个失败",
            )
        except Exception as e:
            return ToolResult.error_result(f"移动文件失败: {str(e)}")
    
    async def search_files(
        self,
        ctx: ToolContext,
        path: str = ".",
        pattern: Optional[str] = None,
        content: Optional[str] = None,
    ) -> ToolResult:
        """搜索文件"""
        search_path = Path(path).expanduser().resolve()
        
        # 安全检查
        if not ctx.security.is_allowed_path(search_path):
            return ToolResult.error_result(f"路径不允许: {path}")
        
        if not search_path.exists():
            return ToolResult.error_result(f"路径不存在: {path}")
        
        try:
            results = []
            
            # 文件名搜索
            if pattern:
                for item in search_path.rglob(pattern):
                    if item.is_file():
                        results.append({
                            "name": item.name,
                            "path": str(item),
                            "match_type": "filename",
                        })
            
            # 内容搜索
            if content:
                for item in search_path.rglob("*"):
                    if item.is_file() and item.suffix in [".txt", ".md", ".py", ".js", ".json", ".yaml", ".yml"]:
                        try:
                            text = item.read_text(encoding="utf-8", errors="ignore")
                            if content.lower() in text.lower():
                                # 找到匹配的行
                                lines = text.split("\n")
                                matches = []
                                for i, line in enumerate(lines, 1):
                                    if content.lower() in line.lower():
                                        matches.append({"line": i, "text": line.strip()[:100]})
                                
                                results.append({
                                    "name": item.name,
                                    "path": str(item),
                                    "match_type": "content",
                                    "matches": matches[:5],  # 限制匹配数
                                })
                        except Exception:
                            continue
            
            return ToolResult.table(
                data=results[:50],  # 限制结果数量
                message=f"找到 {len(results)} 个匹配",
            )
        except Exception as e:
            return ToolResult.error_result(f"搜索失败: {str(e)}")
