"""笔记助手技能"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from auto.core.skill.base import Skill, ToolDefinition
from auto.core.tool.context import ToolContext
from auto.core.tool.result import ToolResult


class NotesSkill(Skill):
    """笔记助手技能
    
    提供快速记录、笔记管理、搜索等功能。
    """
    
    @property
    def name(self) -> str:
        return "notes"
    
    @property
    def display_name(self) -> str:
        return "笔记助手"
    
    @property
    def description(self) -> str:
        return "快速记录、笔记管理、标签分类、全文搜索"
    
    @property
    def category(self) -> str:
        return "productivity"
    
    @property
    def tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="create_note",
                description="创建新笔记",
                parameters={
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "笔记标题",
                        },
                        "content": {
                            "type": "string",
                            "description": "笔记内容 (Markdown)",
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "标签列表",
                        },
                        "folder": {
                            "type": "string",
                            "description": "存放文件夹",
                            "default": "notes",
                        },
                    },
                    "required": ["title", "content"],
                },
                handler=self.create_note,
            ),
            ToolDefinition(
                name="quick_note",
                description="快速记录 (自动生成标题和时间戳)",
                parameters={
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "笔记内容",
                        },
                        "category": {
                            "type": "string",
                            "enum": ["idea", "todo", "memo", "meeting", "daily"],
                            "description": "分类",
                            "default": "memo",
                        },
                    },
                    "required": ["content"],
                },
                handler=self.quick_note,
            ),
            ToolDefinition(
                name="list_notes",
                description="列出笔记",
                parameters={
                    "type": "object",
                    "properties": {
                        "folder": {
                            "type": "string",
                            "description": "文件夹路径",
                            "default": "notes",
                        },
                        "tag": {
                            "type": "string",
                            "description": "按标签筛选",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "返回数量",
                            "default": 20,
                        },
                    },
                },
                handler=self.list_notes,
            ),
            ToolDefinition(
                name="search_notes",
                description="搜索笔记内容",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索关键词",
                        },
                        "folder": {
                            "type": "string",
                            "description": "搜索范围 (文件夹)",
                            "default": "notes",
                        },
                    },
                    "required": ["query"],
                },
                handler=self.search_notes,
            ),
            ToolDefinition(
                name="read_note",
                description="读取笔记内容",
                parameters={
                    "type": "object",
                    "properties": {
                        "note_path": {
                            "type": "string",
                            "description": "笔记文件路径",
                        },
                    },
                    "required": ["note_path"],
                },
                handler=self.read_note,
            ),
            ToolDefinition(
                name="update_note",
                description="更新笔记",
                parameters={
                    "type": "object",
                    "properties": {
                        "note_path": {
                            "type": "string",
                            "description": "笔记文件路径",
                        },
                        "content": {
                            "type": "string",
                            "description": "新内容",
                        },
                        "append": {
                            "type": "boolean",
                            "description": "是否追加内容",
                            "default": False,
                        },
                    },
                    "required": ["note_path", "content"],
                },
                handler=self.update_note,
            ),
            ToolDefinition(
                name="daily_note",
                description="创建或更新每日笔记",
                parameters={
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "今日记录",
                        },
                        "date": {
                            "type": "string",
                            "description": "日期 (YYYY-MM-DD)，默认今天",
                        },
                    },
                    "required": ["content"],
                },
                handler=self.daily_note,
            ),
            ToolDefinition(
                name="get_note_stats",
                description="获取笔记统计",
                parameters={
                    "type": "object",
                    "properties": {
                        "folder": {
                            "type": "string",
                            "description": "文件夹路径",
                            "default": "notes",
                        },
                    },
                },
                handler=self.get_note_stats,
            ),
        ]
    
    @property
    def system_prompt(self) -> str:
        return """你是一个笔记助手，帮助用户快速记录和管理笔记。

功能：
- 快速记录想法和备忘
- 按标签和文件夹分类
- 搜索历史笔记
- 每日笔记管理

笔记格式：
- 使用 Markdown 格式
- 自动添加时间戳
- 支持标签分类"""
    
    def _get_notes_dir(self, ctx: ToolContext, folder: str = "notes") -> Path:
        """获取笔记目录"""
        if ctx.workspace_id:
            # 工作空间内的笔记目录
            from auto.shared.config import DEFAULT_CONFIG_DIR
            base = DEFAULT_CONFIG_DIR / "workspaces" / ctx.workspace_id
        else:
            base = Path.home() / ".ai-auto"
        
        return base / folder
    
    async def create_note(
        self,
        ctx: ToolContext,
        title: str,
        content: str,
        tags: Optional[list[str]] = None,
        folder: str = "notes",
    ) -> ToolResult:
        """创建笔记"""
        notes_dir = self._get_notes_dir(ctx, folder)
        
        if not ctx.security.is_allowed_path(notes_dir):
            return ToolResult.error_result(f"路径不允许: {notes_dir}")
        
        notes_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c if c.isalnum() or c in "- _" else "_" for c in title)
        filename = f"{timestamp}_{safe_title[:50]}.md"
        
        # 构建笔记内容
        tags_str = ", ".join(tags) if tags else ""
        note_content = f"""---
title: {title}
created: {datetime.now().isoformat()}
tags: [{tags_str}]
---

# {title}

{content}
"""
        
        note_path = notes_dir / filename
        note_path.write_text(note_content, encoding="utf-8")
        
        return ToolResult.file(
            path=str(note_path),
            message=f"笔记已创建: {title}",
        )
    
    async def quick_note(
        self,
        ctx: ToolContext,
        content: str,
        category: str = "memo",
    ) -> ToolResult:
        """快速记录"""
        category_names = {
            "idea": "💡 想法",
            "todo": "✅ 待办",
            "memo": "📝 备忘",
            "meeting": "📅 会议",
            "daily": "📆 日记",
        }
        
        title = category_names.get(category, "📝 备忘")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        title = f"{title} - {timestamp}"
        
        return await self.create_note(
            ctx,
            title=title,
            content=content,
            tags=[category],
            folder=f"notes/{category}",
        )
    
    async def list_notes(
        self,
        ctx: ToolContext,
        folder: str = "notes",
        tag: Optional[str] = None,
        limit: int = 20,
    ) -> ToolResult:
        """列出笔记"""
        notes_dir = self._get_notes_dir(ctx, folder)
        
        if not notes_dir.exists():
            return ToolResult.success_result(
                data={"notes": [], "count": 0},
                message="暂无笔记",
            )
        
        notes = []
        
        # 递归查找 .md 文件
        for note_path in sorted(notes_dir.rglob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
            if len(notes) >= limit:
                break
            
            # 读取元数据
            try:
                content = note_path.read_text(encoding="utf-8")
                
                # 解析 frontmatter
                title = note_path.stem
                note_tags = []
                
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        frontmatter = parts[1]
                        for line in frontmatter.split("\n"):
                            if line.startswith("title:"):
                                title = line.split(":", 1)[1].strip()
                            elif line.startswith("tags:"):
                                tags_str = line.split(":", 1)[1].strip()
                                note_tags = [t.strip() for t in tags_str.strip("[]").split(",") if t.strip()]
                
                # 标签筛选
                if tag and tag not in note_tags:
                    continue
                
                notes.append({
                    "path": str(note_path),
                    "title": title,
                    "tags": note_tags,
                    "modified": datetime.fromtimestamp(note_path.stat().st_mtime).isoformat(),
                    "size": note_path.stat().st_size,
                })
            except Exception:
                continue
        
        return ToolResult.table(
            data=notes,
            message=f"找到 {len(notes)} 条笔记",
        )
    
    async def search_notes(
        self,
        ctx: ToolContext,
        query: str,
        folder: str = "notes",
    ) -> ToolResult:
        """搜索笔记"""
        notes_dir = self._get_notes_dir(ctx, folder)
        
        if not notes_dir.exists():
            return ToolResult.success_result(
                data={"results": []},
                message="暂无笔记",
            )
        
        results = []
        query_lower = query.lower()
        
        for note_path in notes_dir.rglob("*.md"):
            try:
                content = note_path.read_text(encoding="utf-8")
                
                if query_lower in content.lower():
                    # 找到匹配的行
                    matches = []
                    for i, line in enumerate(content.split("\n")):
                        if query_lower in line.lower():
                            matches.append({
                                "line": i + 1,
                                "text": line[:100],
                            })
                    
                    # 提取标题
                    title = note_path.stem
                    if content.startswith("---"):
                        parts = content.split("---", 2)
                        if len(parts) >= 3:
                            for line in parts[1].split("\n"):
                                if line.startswith("title:"):
                                    title = line.split(":", 1)[1].strip()
                                    break
                    
                    results.append({
                        "path": str(note_path),
                        "title": title,
                        "matches": matches[:3],  # 最多显示3处匹配
                        "match_count": len(matches),
                    })
            except Exception:
                continue
        
        return ToolResult.success_result(
            data={"results": results},
            message=f"搜索 '{query}' 找到 {len(results)} 条结果",
        )
    
    async def read_note(
        self,
        ctx: ToolContext,
        note_path: str,
    ) -> ToolResult:
        """读取笔记"""
        path = Path(note_path).expanduser()
        
        if not ctx.security.is_allowed_path(path):
            return ToolResult.error_result(f"路径不允许: {note_path}")
        
        if not path.exists():
            return ToolResult.error_result(f"笔记不存在: {note_path}")
        
        try:
            content = path.read_text(encoding="utf-8")
            
            return ToolResult.success_result(
                data={
                    "path": str(path),
                    "content": content,
                    "size": len(content),
                },
                message=f"读取笔记: {path.name}",
            )
        except Exception as e:
            return ToolResult.error_result(f"读取失败: {str(e)}")
    
    async def update_note(
        self,
        ctx: ToolContext,
        note_path: str,
        content: str,
        append: bool = False,
    ) -> ToolResult:
        """更新笔记"""
        path = Path(note_path).expanduser()
        
        if not ctx.security.is_allowed_path(path):
            return ToolResult.error_result(f"路径不允许: {note_path}")
        
        if not path.exists():
            return ToolResult.error_result(f"笔记不存在: {note_path}")
        
        try:
            if append:
                old_content = path.read_text(encoding="utf-8")
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                new_content = f"{old_content}\n\n---\n\n**更新于 {timestamp}**\n\n{content}"
            else:
                new_content = content
            
            path.write_text(new_content, encoding="utf-8")
            
            return ToolResult.success_result(
                data={"path": str(path)},
                message=f"笔记已{'追加' if append else '更新'}: {path.name}",
            )
        except Exception as e:
            return ToolResult.error_result(f"更新失败: {str(e)}")
    
    async def daily_note(
        self,
        ctx: ToolContext,
        content: str,
        date: Optional[str] = None,
    ) -> ToolResult:
        """每日笔记"""
        if date:
            try:
                note_date = datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                return ToolResult.error_result("日期格式错误，请使用 YYYY-MM-DD")
        else:
            note_date = datetime.now()
        
        notes_dir = self._get_notes_dir(ctx, "daily")
        notes_dir.mkdir(parents=True, exist_ok=True)
        
        filename = note_date.strftime("%Y-%m-%d.md")
        note_path = notes_dir / filename
        
        timestamp = datetime.now().strftime("%H:%M")
        entry = f"\n## {timestamp}\n\n{content}\n"
        
        if note_path.exists():
            # 追加到现有日记
            old_content = note_path.read_text(encoding="utf-8")
            new_content = old_content + entry
            note_path.write_text(new_content, encoding="utf-8")
            message = f"已追加到 {filename}"
        else:
            # 创建新日记
            new_content = f"""---
title: 每日笔记 - {note_date.strftime("%Y-%m-%d")}
created: {datetime.now().isoformat()}
tags: [daily]
---

# 每日笔记 - {note_date.strftime("%Y年%m月%d日")}
{entry}"""
            note_path.write_text(new_content, encoding="utf-8")
            message = f"已创建 {filename}"
        
        return ToolResult.file(
            path=str(note_path),
            message=message,
        )
    
    async def get_note_stats(
        self,
        ctx: ToolContext,
        folder: str = "notes",
    ) -> ToolResult:
        """获取笔记统计"""
        notes_dir = self._get_notes_dir(ctx, folder)
        
        if not notes_dir.exists():
            return ToolResult.success_result(
                data={"total": 0},
                message="暂无笔记",
            )
        
        total_notes = 0
        total_size = 0
        by_tag = {}
        by_month = {}
        
        for note_path in notes_dir.rglob("*.md"):
            try:
                total_notes += 1
                total_size += note_path.stat().st_size
                
                # 按月份统计
                mtime = datetime.fromtimestamp(note_path.stat().st_mtime)
                month_key = mtime.strftime("%Y-%m")
                by_month[month_key] = by_month.get(month_key, 0) + 1
                
                # 读取标签
                content = note_path.read_text(encoding="utf-8")
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        for line in parts[1].split("\n"):
                            if line.startswith("tags:"):
                                tags_str = line.split(":", 1)[1].strip()
                                tags = [t.strip() for t in tags_str.strip("[]").split(",") if t.strip()]
                                for tag in tags:
                                    by_tag[tag] = by_tag.get(tag, 0) + 1
            except Exception:
                continue
        
        return ToolResult.success_result(
            data={
                "total_notes": total_notes,
                "total_size": total_size,
                "total_size_human": f"{total_size / 1024:.1f} KB",
                "by_tag": by_tag,
                "by_month": dict(sorted(by_month.items(), reverse=True)[:6]),
            },
            message=f"共 {total_notes} 条笔记",
        )
