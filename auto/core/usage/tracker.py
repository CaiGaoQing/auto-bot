"""Token 用量追踪器"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from collections import defaultdict


@dataclass
class UsageRecord:
    """用量记录"""
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float = 0.0
    
    user_id: Optional[str] = None
    workspace_id: Optional[str] = None
    conversation_id: Optional[str] = None
    
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def estimated_cost(self) -> float:
        """估算成本 (基于通用定价)"""
        if self.cost > 0:
            return self.cost
        
        # 通用定价表 (美元/1K tokens)
        pricing = {
            "gpt-4": (0.03, 0.06),
            "gpt-4-turbo": (0.01, 0.03),
            "gpt-4o": (0.005, 0.015),
            "gpt-4o-mini": (0.00015, 0.0006),
            "gpt-3.5-turbo": (0.0015, 0.002),
            "claude-3-opus": (0.015, 0.075),
            "claude-3-sonnet": (0.003, 0.015),
            "claude-3-haiku": (0.00025, 0.00125),
            "claude-3.5-sonnet": (0.003, 0.015),
        }
        
        # 匹配模型
        model_lower = self.model.lower()
        input_price, output_price = pricing.get("gpt-4o-mini", (0.001, 0.002))
        
        for model_name, prices in pricing.items():
            if model_name in model_lower:
                input_price, output_price = prices
                break
        
        input_cost = (self.prompt_tokens / 1000) * input_price
        output_cost = (self.completion_tokens / 1000) * output_price
        
        return round(input_cost + output_cost, 6)


@dataclass
class UsageSummary:
    """用量汇总"""
    total_requests: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    
    by_provider: dict = field(default_factory=dict)
    by_model: dict = field(default_factory=dict)
    by_user: dict = field(default_factory=dict)
    by_workspace: dict = field(default_factory=dict)
    by_date: dict = field(default_factory=dict)


class UsageTracker:
    """Token 用量追踪器
    
    追踪和统计 AI 调用的 Token 用量。
    """
    
    def __init__(self):
        self._records: list[UsageRecord] = []
        self._by_provider: dict[str, list[UsageRecord]] = defaultdict(list)
        self._by_model: dict[str, list[UsageRecord]] = defaultdict(list)
        self._by_user: dict[str, list[UsageRecord]] = defaultdict(list)
        self._by_workspace: dict[str, list[UsageRecord]] = defaultdict(list)
        self._by_date: dict[str, list[UsageRecord]] = defaultdict(list)
    
    def record(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost: float = 0.0,
        user_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> UsageRecord:
        """记录用量"""
        record = UsageRecord(
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cost=cost,
            user_id=user_id,
            workspace_id=workspace_id,
            conversation_id=conversation_id,
        )
        
        # 索引存储
        self._records.append(record)
        self._by_provider[provider].append(record)
        self._by_model[model].append(record)
        
        if user_id:
            self._by_user[user_id].append(record)
        
        if workspace_id:
            self._by_workspace[workspace_id].append(record)
        
        date_key = record.timestamp.strftime("%Y-%m-%d")
        self._by_date[date_key].append(record)
        
        return record
    
    def get_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> UsageSummary:
        """获取用量汇总"""
        # 过滤记录
        records = self._filter_records(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            workspace_id=workspace_id,
            provider=provider,
            model=model,
        )
        
        summary = UsageSummary()
        summary.total_requests = len(records)
        
        provider_stats = defaultdict(lambda: {"requests": 0, "tokens": 0, "cost": 0.0})
        model_stats = defaultdict(lambda: {"requests": 0, "tokens": 0, "cost": 0.0})
        user_stats = defaultdict(lambda: {"requests": 0, "tokens": 0, "cost": 0.0})
        workspace_stats = defaultdict(lambda: {"requests": 0, "tokens": 0, "cost": 0.0})
        date_stats = defaultdict(lambda: {"requests": 0, "tokens": 0, "cost": 0.0})
        
        for record in records:
            summary.total_prompt_tokens += record.prompt_tokens
            summary.total_completion_tokens += record.completion_tokens
            summary.total_tokens += record.total_tokens
            
            cost = record.estimated_cost
            summary.total_cost += cost
            
            # 按提供商统计
            provider_stats[record.provider]["requests"] += 1
            provider_stats[record.provider]["tokens"] += record.total_tokens
            provider_stats[record.provider]["cost"] += cost
            
            # 按模型统计
            model_stats[record.model]["requests"] += 1
            model_stats[record.model]["tokens"] += record.total_tokens
            model_stats[record.model]["cost"] += cost
            
            # 按用户统计
            if record.user_id:
                user_stats[record.user_id]["requests"] += 1
                user_stats[record.user_id]["tokens"] += record.total_tokens
                user_stats[record.user_id]["cost"] += cost
            
            # 按工作空间统计
            if record.workspace_id:
                workspace_stats[record.workspace_id]["requests"] += 1
                workspace_stats[record.workspace_id]["tokens"] += record.total_tokens
                workspace_stats[record.workspace_id]["cost"] += cost
            
            # 按日期统计
            date_key = record.timestamp.strftime("%Y-%m-%d")
            date_stats[date_key]["requests"] += 1
            date_stats[date_key]["tokens"] += record.total_tokens
            date_stats[date_key]["cost"] += cost
        
        summary.by_provider = dict(provider_stats)
        summary.by_model = dict(model_stats)
        summary.by_user = dict(user_stats)
        summary.by_workspace = dict(workspace_stats)
        summary.by_date = dict(date_stats)
        summary.total_cost = round(summary.total_cost, 4)
        
        return summary
    
    def _filter_records(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> list[UsageRecord]:
        """过滤记录"""
        # 从最小范围开始
        if user_id:
            records = self._by_user.get(user_id, [])
        elif workspace_id:
            records = self._by_workspace.get(workspace_id, [])
        elif provider:
            records = self._by_provider.get(provider, [])
        elif model:
            records = self._by_model.get(model, [])
        else:
            records = self._records
        
        # 时间过滤
        if start_date or end_date:
            filtered = []
            for r in records:
                if start_date and r.timestamp < start_date:
                    continue
                if end_date and r.timestamp > end_date:
                    continue
                filtered.append(r)
            records = filtered
        
        # 其他过滤
        if provider and not (user_id or workspace_id):
            records = [r for r in records if r.provider == provider]
        if model and not (user_id or workspace_id or provider):
            records = [r for r in records if r.model == model]
        
        return records
    
    def get_today_summary(
        self,
        user_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ) -> UsageSummary:
        """获取今日用量"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        
        return self.get_summary(
            start_date=today,
            end_date=tomorrow,
            user_id=user_id,
            workspace_id=workspace_id,
        )
    
    def get_monthly_summary(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None,
        user_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ) -> UsageSummary:
        """获取月度用量"""
        now = datetime.now()
        year = year or now.year
        month = month or now.month
        
        start_date = datetime(year, month, 1)
        
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        return self.get_summary(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            workspace_id=workspace_id,
        )
    
    def get_recent_records(
        self,
        limit: int = 100,
        user_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ) -> list[UsageRecord]:
        """获取最近的记录"""
        if user_id:
            records = self._by_user.get(user_id, [])
        elif workspace_id:
            records = self._by_workspace.get(workspace_id, [])
        else:
            records = self._records
        
        return sorted(records, key=lambda r: r.timestamp, reverse=True)[:limit]
    
    def export_records(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[dict]:
        """导出记录为字典列表"""
        records = self._filter_records(start_date=start_date, end_date=end_date)
        
        return [
            {
                "provider": r.provider,
                "model": r.model,
                "prompt_tokens": r.prompt_tokens,
                "completion_tokens": r.completion_tokens,
                "total_tokens": r.total_tokens,
                "cost": r.estimated_cost,
                "user_id": r.user_id,
                "workspace_id": r.workspace_id,
                "timestamp": r.timestamp.isoformat(),
            }
            for r in records
        ]
    
    def clear(self) -> None:
        """清空记录"""
        self._records.clear()
        self._by_provider.clear()
        self._by_model.clear()
        self._by_user.clear()
        self._by_workspace.clear()
        self._by_date.clear()


# 全局追踪器
_tracker: Optional[UsageTracker] = None


def get_usage_tracker() -> UsageTracker:
    """获取全局追踪器"""
    global _tracker
    if _tracker is None:
        _tracker = UsageTracker()
    return _tracker
