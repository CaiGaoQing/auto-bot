"""日程管理技能"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict, field

from auto.core.skill.base import Skill, ToolDefinition
from auto.core.tool.context import ToolContext
from auto.core.tool.result import ToolResult


@dataclass
class Event:
    """日程事件"""
    id: str
    title: str
    start: str  # ISO 格式
    end: Optional[str] = None
    description: str = ""
    location: str = ""
    reminder: Optional[int] = None  # 提前提醒分钟数
    recurring: Optional[str] = None  # daily, weekly, monthly
    tags: list = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class CalendarSkill(Skill):
    """日程管理技能
    
    提供日程创建、查询、提醒等功能。
    """
    
    @property
    def name(self) -> str:
        return "calendar"
    
    @property
    def display_name(self) -> str:
        return "日程管理"
    
    @property
    def description(self) -> str:
        return "日程安排、会议管理、提醒设置"
    
    @property
    def category(self) -> str:
        return "productivity"
    
    @property
    def tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="create_event",
                description="创建日程事件",
                parameters={
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "事件标题",
                        },
                        "start": {
                            "type": "string",
                            "description": "开始时间 (YYYY-MM-DD HH:MM 或 YYYY-MM-DD)",
                        },
                        "end": {
                            "type": "string",
                            "description": "结束时间",
                        },
                        "description": {
                            "type": "string",
                            "description": "事件描述",
                        },
                        "location": {
                            "type": "string",
                            "description": "地点",
                        },
                        "reminder": {
                            "type": "integer",
                            "description": "提前提醒分钟数",
                        },
                        "recurring": {
                            "type": "string",
                            "enum": ["daily", "weekly", "monthly"],
                            "description": "重复规则",
                        },
                    },
                    "required": ["title", "start"],
                },
                handler=self.create_event,
            ),
            ToolDefinition(
                name="list_events",
                description="列出日程事件",
                parameters={
                    "type": "object",
                    "properties": {
                        "start_date": {
                            "type": "string",
                            "description": "开始日期 (YYYY-MM-DD)",
                        },
                        "end_date": {
                            "type": "string",
                            "description": "结束日期",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "返回数量",
                            "default": 20,
                        },
                    },
                },
                handler=self.list_events,
            ),
            ToolDefinition(
                name="today_events",
                description="获取今日日程",
                parameters={
                    "type": "object",
                    "properties": {},
                },
                handler=self.today_events,
            ),
            ToolDefinition(
                name="upcoming_events",
                description="获取即将到来的日程",
                parameters={
                    "type": "object",
                    "properties": {
                        "days": {
                            "type": "integer",
                            "description": "未来天数",
                            "default": 7,
                        },
                    },
                },
                handler=self.upcoming_events,
            ),
            ToolDefinition(
                name="delete_event",
                description="删除日程事件",
                parameters={
                    "type": "object",
                    "properties": {
                        "event_id": {
                            "type": "string",
                            "description": "事件 ID",
                        },
                    },
                    "required": ["event_id"],
                },
                handler=self.delete_event,
            ),
            ToolDefinition(
                name="update_event",
                description="更新日程事件",
                parameters={
                    "type": "object",
                    "properties": {
                        "event_id": {
                            "type": "string",
                            "description": "事件 ID",
                        },
                        "title": {
                            "type": "string",
                            "description": "新标题",
                        },
                        "start": {
                            "type": "string",
                            "description": "新开始时间",
                        },
                        "end": {
                            "type": "string",
                            "description": "新结束时间",
                        },
                    },
                    "required": ["event_id"],
                },
                handler=self.update_event,
            ),
            ToolDefinition(
                name="search_events",
                description="搜索日程事件",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索关键词",
                        },
                    },
                    "required": ["query"],
                },
                handler=self.search_events,
            ),
            ToolDefinition(
                name="get_free_time",
                description="查找空闲时间",
                parameters={
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "日期 (YYYY-MM-DD)",
                        },
                        "duration": {
                            "type": "integer",
                            "description": "需要的时长 (分钟)",
                            "default": 60,
                        },
                    },
                    "required": ["date"],
                },
                handler=self.get_free_time,
            ),
        ]
    
    @property
    def system_prompt(self) -> str:
        return """你是一个日程管理助手，帮助用户安排和管理日程。

功能：
- 创建和管理日程事件
- 设置提醒
- 查找空闲时间
- 日程冲突检测

时间格式：
- 日期: YYYY-MM-DD
- 时间: YYYY-MM-DD HH:MM"""
    
    def _get_calendar_file(self, ctx: ToolContext) -> Path:
        """获取日历数据文件"""
        from auto.shared.config import DEFAULT_CONFIG_DIR
        
        if ctx.workspace_id:
            base = DEFAULT_CONFIG_DIR / "workspaces" / ctx.workspace_id
        else:
            base = DEFAULT_CONFIG_DIR
        
        calendar_dir = base / "calendar"
        calendar_dir.mkdir(parents=True, exist_ok=True)
        
        return calendar_dir / "events.json"
    
    def _load_events(self, ctx: ToolContext) -> list[dict]:
        """加载事件"""
        file_path = self._get_calendar_file(ctx)
        
        if not file_path.exists():
            return []
        
        try:
            return json.loads(file_path.read_text(encoding="utf-8"))
        except Exception:
            return []
    
    def _save_events(self, ctx: ToolContext, events: list[dict]) -> None:
        """保存事件"""
        file_path = self._get_calendar_file(ctx)
        file_path.write_text(json.dumps(events, ensure_ascii=False, indent=2), encoding="utf-8")
    
    def _parse_datetime(self, dt_str: str) -> datetime:
        """解析日期时间字符串"""
        formats = [
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%Y/%m/%d %H:%M",
            "%Y/%m/%d",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(dt_str, fmt)
            except ValueError:
                continue
        
        raise ValueError(f"无法解析日期时间: {dt_str}")
    
    async def create_event(
        self,
        ctx: ToolContext,
        title: str,
        start: str,
        end: Optional[str] = None,
        description: str = "",
        location: str = "",
        reminder: Optional[int] = None,
        recurring: Optional[str] = None,
    ) -> ToolResult:
        """创建日程事件"""
        try:
            start_dt = self._parse_datetime(start)
        except ValueError as e:
            return ToolResult.error_result(str(e))
        
        if end:
            try:
                end_dt = self._parse_datetime(end)
            except ValueError:
                end_dt = start_dt + timedelta(hours=1)
        else:
            end_dt = start_dt + timedelta(hours=1)
        
        # 生成 ID
        from auto.shared.utils import generate_id
        event_id = generate_id("evt")
        
        event = Event(
            id=event_id,
            title=title,
            start=start_dt.isoformat(),
            end=end_dt.isoformat(),
            description=description,
            location=location,
            reminder=reminder,
            recurring=recurring,
        )
        
        # 保存
        events = self._load_events(ctx)
        events.append(asdict(event))
        self._save_events(ctx, events)
        
        return ToolResult.success_result(
            data=asdict(event),
            message=f"日程已创建: {title} ({start_dt.strftime('%m-%d %H:%M')})",
        )
    
    async def list_events(
        self,
        ctx: ToolContext,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 20,
    ) -> ToolResult:
        """列出日程事件"""
        events = self._load_events(ctx)
        
        # 过滤
        if start_date:
            try:
                start_dt = self._parse_datetime(start_date)
                events = [e for e in events if datetime.fromisoformat(e["start"]) >= start_dt]
            except Exception:
                pass
        
        if end_date:
            try:
                end_dt = self._parse_datetime(end_date)
                events = [e for e in events if datetime.fromisoformat(e["start"]) <= end_dt]
            except Exception:
                pass
        
        # 排序
        events = sorted(events, key=lambda e: e["start"])[:limit]
        
        # 格式化输出
        formatted = []
        for e in events:
            start_dt = datetime.fromisoformat(e["start"])
            formatted.append({
                "id": e["id"][:8],
                "title": e["title"],
                "start": start_dt.strftime("%m-%d %H:%M"),
                "location": e.get("location", ""),
            })
        
        return ToolResult.table(
            data=formatted,
            message=f"共 {len(events)} 个日程",
        )
    
    async def today_events(self, ctx: ToolContext) -> ToolResult:
        """获取今日日程"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        
        return await self.list_events(
            ctx,
            start_date=today.strftime("%Y-%m-%d"),
            end_date=tomorrow.strftime("%Y-%m-%d"),
        )
    
    async def upcoming_events(
        self,
        ctx: ToolContext,
        days: int = 7,
    ) -> ToolResult:
        """获取即将到来的日程"""
        now = datetime.now()
        end = now + timedelta(days=days)
        
        return await self.list_events(
            ctx,
            start_date=now.strftime("%Y-%m-%d"),
            end_date=end.strftime("%Y-%m-%d"),
        )
    
    async def delete_event(
        self,
        ctx: ToolContext,
        event_id: str,
    ) -> ToolResult:
        """删除日程事件"""
        events = self._load_events(ctx)
        
        # 查找事件
        found = None
        for i, e in enumerate(events):
            if e["id"] == event_id or e["id"].startswith(event_id):
                found = events.pop(i)
                break
        
        if not found:
            return ToolResult.error_result(f"事件不存在: {event_id}")
        
        self._save_events(ctx, events)
        
        return ToolResult.success_result(
            data={"deleted": found},
            message=f"已删除: {found['title']}",
        )
    
    async def update_event(
        self,
        ctx: ToolContext,
        event_id: str,
        title: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> ToolResult:
        """更新日程事件"""
        events = self._load_events(ctx)
        
        # 查找事件
        found_idx = None
        for i, e in enumerate(events):
            if e["id"] == event_id or e["id"].startswith(event_id):
                found_idx = i
                break
        
        if found_idx is None:
            return ToolResult.error_result(f"事件不存在: {event_id}")
        
        event = events[found_idx]
        
        if title:
            event["title"] = title
        if start:
            try:
                event["start"] = self._parse_datetime(start).isoformat()
            except ValueError as e:
                return ToolResult.error_result(str(e))
        if end:
            try:
                event["end"] = self._parse_datetime(end).isoformat()
            except ValueError as e:
                return ToolResult.error_result(str(e))
        
        events[found_idx] = event
        self._save_events(ctx, events)
        
        return ToolResult.success_result(
            data=event,
            message=f"已更新: {event['title']}",
        )
    
    async def search_events(
        self,
        ctx: ToolContext,
        query: str,
    ) -> ToolResult:
        """搜索日程事件"""
        events = self._load_events(ctx)
        query_lower = query.lower()
        
        results = []
        for e in events:
            if (query_lower in e["title"].lower() or
                query_lower in e.get("description", "").lower() or
                query_lower in e.get("location", "").lower()):
                results.append(e)
        
        # 格式化
        formatted = []
        for e in results:
            start_dt = datetime.fromisoformat(e["start"])
            formatted.append({
                "id": e["id"][:8],
                "title": e["title"],
                "start": start_dt.strftime("%Y-%m-%d %H:%M"),
            })
        
        return ToolResult.table(
            data=formatted,
            message=f"搜索 '{query}' 找到 {len(results)} 个结果",
        )
    
    async def get_free_time(
        self,
        ctx: ToolContext,
        date: str,
        duration: int = 60,
    ) -> ToolResult:
        """查找空闲时间"""
        try:
            target_date = self._parse_datetime(date)
        except ValueError as e:
            return ToolResult.error_result(str(e))
        
        # 工作时间 9:00 - 18:00
        work_start = target_date.replace(hour=9, minute=0)
        work_end = target_date.replace(hour=18, minute=0)
        
        # 获取当天事件
        events = self._load_events(ctx)
        day_events = []
        
        for e in events:
            event_start = datetime.fromisoformat(e["start"])
            if event_start.date() == target_date.date():
                event_end = datetime.fromisoformat(e["end"]) if e.get("end") else event_start + timedelta(hours=1)
                day_events.append((event_start, event_end, e["title"]))
        
        # 按开始时间排序
        day_events.sort(key=lambda x: x[0])
        
        # 查找空闲时段
        free_slots = []
        current = work_start
        
        for event_start, event_end, _ in day_events:
            if current < event_start:
                gap = (event_start - current).total_seconds() / 60
                if gap >= duration:
                    free_slots.append({
                        "start": current.strftime("%H:%M"),
                        "end": event_start.strftime("%H:%M"),
                        "duration": int(gap),
                    })
            current = max(current, event_end)
        
        # 检查最后一段
        if current < work_end:
            gap = (work_end - current).total_seconds() / 60
            if gap >= duration:
                free_slots.append({
                    "start": current.strftime("%H:%M"),
                    "end": work_end.strftime("%H:%M"),
                    "duration": int(gap),
                })
        
        return ToolResult.table(
            data=free_slots,
            message=f"{date} 有 {len(free_slots)} 个空闲时段 (>={duration}分钟)",
        )
