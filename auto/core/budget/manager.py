"""预算管理器

实现 Token 使用预算控制和告警。
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"           # 50%
    WARNING = "warning"     # 80%
    CRITICAL = "critical"   # 100%


@dataclass
class BudgetConfig:
    """预算配置"""
    # 每日预算 (美元)
    daily_budget: float = 10.0
    
    # 每月预算 (美元)
    monthly_budget: float = 100.0
    
    # 每用户每日限制 (美元)
    user_daily_limit: float = 5.0
    
    # 告警阈值
    alert_thresholds: list[float] = field(default_factory=lambda: [0.5, 0.8, 1.0])
    
    # 超预算时是否阻止请求
    block_on_exceed: bool = False
    
    # 告警回调
    alert_callback: Optional[Callable] = None


@dataclass
class BudgetAlert:
    """预算告警"""
    level: AlertLevel
    budget_type: str  # daily, monthly, user
    current_usage: float
    budget_limit: float
    usage_percent: float
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    user_id: Optional[str] = None
    workspace_id: Optional[str] = None


class BudgetManager:
    """预算管理器
    
    功能:
    - 跟踪日/月使用量
    - 阈值告警 (50%/80%/100%)
    - 超预算拦截 (可选)
    """
    
    def __init__(self, config: Optional[BudgetConfig] = None):
        self.config = config or BudgetConfig()
        
        # 使用记录
        self._daily_usage: dict[str, float] = {}  # date -> cost
        self._monthly_usage: dict[str, float] = {}  # month -> cost
        self._user_daily_usage: dict[str, dict[str, float]] = {}  # user_id -> date -> cost
        
        # 已触发的告警
        self._triggered_alerts: set[str] = set()
        
        # 告警历史
        self._alert_history: list[BudgetAlert] = []
    
    def _get_today(self) -> str:
        """获取今日日期字符串"""
        return datetime.now().strftime("%Y-%m-%d")
    
    def _get_month(self) -> str:
        """获取当月字符串"""
        return datetime.now().strftime("%Y-%m")
    
    def record_usage(
        self,
        cost: float,
        user_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ) -> list[BudgetAlert]:
        """记录使用量并检查预算
        
        Args:
            cost: 本次使用成本 (美元)
            user_id: 用户 ID
            workspace_id: 工作空间 ID
        
        Returns:
            list[BudgetAlert]: 触发的告警列表
        """
        today = self._get_today()
        month = self._get_month()
        
        # 更新使用量
        self._daily_usage[today] = self._daily_usage.get(today, 0) + cost
        self._monthly_usage[month] = self._monthly_usage.get(month, 0) + cost
        
        if user_id:
            if user_id not in self._user_daily_usage:
                self._user_daily_usage[user_id] = {}
            self._user_daily_usage[user_id][today] = (
                self._user_daily_usage[user_id].get(today, 0) + cost
            )
        
        # 检查预算
        alerts = []
        
        # 日预算检查
        daily_alert = self._check_budget(
            budget_type="daily",
            current=self._daily_usage[today],
            limit=self.config.daily_budget,
            user_id=user_id,
            workspace_id=workspace_id,
        )
        if daily_alert:
            alerts.append(daily_alert)
        
        # 月预算检查
        monthly_alert = self._check_budget(
            budget_type="monthly",
            current=self._monthly_usage[month],
            limit=self.config.monthly_budget,
            user_id=user_id,
            workspace_id=workspace_id,
        )
        if monthly_alert:
            alerts.append(monthly_alert)
        
        # 用户日限制检查
        if user_id:
            user_usage = self._user_daily_usage[user_id].get(today, 0)
            user_alert = self._check_budget(
                budget_type="user_daily",
                current=user_usage,
                limit=self.config.user_daily_limit,
                user_id=user_id,
                workspace_id=workspace_id,
            )
            if user_alert:
                alerts.append(user_alert)
        
        # 触发告警回调
        for alert in alerts:
            self._alert_history.append(alert)
            if self.config.alert_callback:
                try:
                    self.config.alert_callback(alert)
                except Exception as e:
                    logger.error(f"告警回调失败: {e}")
        
        return alerts
    
    def _check_budget(
        self,
        budget_type: str,
        current: float,
        limit: float,
        user_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ) -> Optional[BudgetAlert]:
        """检查单项预算"""
        if limit <= 0:
            return None
        
        percent = current / limit
        
        for threshold in sorted(self.config.alert_thresholds):
            if percent >= threshold:
                # 生成告警 ID，避免重复告警
                alert_key = f"{budget_type}:{self._get_today()}:{threshold}"
                if user_id:
                    alert_key += f":{user_id}"
                
                if alert_key in self._triggered_alerts:
                    continue
                
                self._triggered_alerts.add(alert_key)
                
                # 确定告警级别
                if threshold >= 1.0:
                    level = AlertLevel.CRITICAL
                elif threshold >= 0.8:
                    level = AlertLevel.WARNING
                else:
                    level = AlertLevel.INFO
                
                # 生成消息
                if budget_type == "daily":
                    msg = f"日预算已使用 {percent*100:.1f}% (${current:.2f}/${limit:.2f})"
                elif budget_type == "monthly":
                    msg = f"月预算已使用 {percent*100:.1f}% (${current:.2f}/${limit:.2f})"
                else:
                    msg = f"用户日限额已使用 {percent*100:.1f}% (${current:.2f}/${limit:.2f})"
                
                return BudgetAlert(
                    level=level,
                    budget_type=budget_type,
                    current_usage=current,
                    budget_limit=limit,
                    usage_percent=percent,
                    message=msg,
                    user_id=user_id,
                    workspace_id=workspace_id,
                )
        
        return None
    
    def check_can_proceed(
        self,
        estimated_cost: float = 0.01,
        user_id: Optional[str] = None,
    ) -> tuple[bool, Optional[str]]:
        """检查是否可以继续请求
        
        Args:
            estimated_cost: 预估成本
            user_id: 用户 ID
        
        Returns:
            tuple[bool, Optional[str]]: (是否可以继续, 拒绝原因)
        """
        if not self.config.block_on_exceed:
            return True, None
        
        today = self._get_today()
        month = self._get_month()
        
        # 检查日预算
        daily = self._daily_usage.get(today, 0) + estimated_cost
        if daily > self.config.daily_budget:
            return False, f"已超出日预算 (${daily:.2f}/${self.config.daily_budget:.2f})"
        
        # 检查月预算
        monthly = self._monthly_usage.get(month, 0) + estimated_cost
        if monthly > self.config.monthly_budget:
            return False, f"已超出月预算 (${monthly:.2f}/${self.config.monthly_budget:.2f})"
        
        # 检查用户日限制
        if user_id:
            if user_id not in self._user_daily_usage:
                self._user_daily_usage[user_id] = {}
            user_daily = self._user_daily_usage[user_id].get(today, 0) + estimated_cost
            if user_daily > self.config.user_daily_limit:
                return False, f"已超出个人日限额 (${user_daily:.2f}/${self.config.user_daily_limit:.2f})"
        
        return True, None
    
    def get_usage_summary(self) -> dict:
        """获取使用量摘要"""
        today = self._get_today()
        month = self._get_month()
        
        daily_usage = self._daily_usage.get(today, 0)
        monthly_usage = self._monthly_usage.get(month, 0)
        
        return {
            "today": {
                "usage": daily_usage,
                "budget": self.config.daily_budget,
                "percent": daily_usage / self.config.daily_budget * 100 if self.config.daily_budget > 0 else 0,
                "remaining": max(0, self.config.daily_budget - daily_usage),
            },
            "month": {
                "usage": monthly_usage,
                "budget": self.config.monthly_budget,
                "percent": monthly_usage / self.config.monthly_budget * 100 if self.config.monthly_budget > 0 else 0,
                "remaining": max(0, self.config.monthly_budget - monthly_usage),
            },
            "alert_count": len(self._alert_history),
        }
    
    def get_user_usage(self, user_id: str) -> dict:
        """获取用户使用量"""
        today = self._get_today()
        
        if user_id not in self._user_daily_usage:
            return {"today": 0, "limit": self.config.user_daily_limit}
        
        usage = self._user_daily_usage[user_id].get(today, 0)
        
        return {
            "today": usage,
            "limit": self.config.user_daily_limit,
            "percent": usage / self.config.user_daily_limit * 100 if self.config.user_daily_limit > 0 else 0,
            "remaining": max(0, self.config.user_daily_limit - usage),
        }
    
    def get_alerts(
        self,
        limit: int = 50,
        level: Optional[AlertLevel] = None,
    ) -> list[BudgetAlert]:
        """获取告警历史"""
        alerts = self._alert_history
        
        if level:
            alerts = [a for a in alerts if a.level == level]
        
        return alerts[-limit:]
    
    def reset_daily(self) -> None:
        """重置每日计数 (每日凌晨调用)"""
        today = self._get_today()
        
        # 清理旧数据 (保留 7 天)
        cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        self._daily_usage = {k: v for k, v in self._daily_usage.items() if k >= cutoff}
        
        for user_id in self._user_daily_usage:
            self._user_daily_usage[user_id] = {
                k: v for k, v in self._user_daily_usage[user_id].items() if k >= cutoff
            }
        
        # 清理告警标记
        self._triggered_alerts = {k for k in self._triggered_alerts if today not in k}
    
    def update_config(
        self,
        daily_budget: Optional[float] = None,
        monthly_budget: Optional[float] = None,
        user_daily_limit: Optional[float] = None,
        block_on_exceed: Optional[bool] = None,
    ) -> None:
        """更新预算配置"""
        if daily_budget is not None:
            self.config.daily_budget = daily_budget
        if monthly_budget is not None:
            self.config.monthly_budget = monthly_budget
        if user_daily_limit is not None:
            self.config.user_daily_limit = user_daily_limit
        if block_on_exceed is not None:
            self.config.block_on_exceed = block_on_exceed


# 全局预算管理器
_budget_manager: Optional[BudgetManager] = None


def get_budget_manager() -> BudgetManager:
    """获取全局预算管理器"""
    global _budget_manager
    if _budget_manager is None:
        _budget_manager = BudgetManager()
    return _budget_manager
