"""预算管理 API 路由"""

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from auto.core.budget import get_budget_manager, AlertLevel

router = APIRouter()


class BudgetResponse(BaseModel):
    """预算响应"""
    code: int = 0
    message: str = "success"
    data: dict = {}


class BudgetConfigUpdate(BaseModel):
    """更新预算配置请求"""
    daily_budget: Optional[float] = None
    monthly_budget: Optional[float] = None
    user_daily_limit: Optional[float] = None
    block_on_exceed: Optional[bool] = None


@router.get("/budget/summary")
async def get_budget_summary() -> BudgetResponse:
    """获取预算摘要"""
    manager = get_budget_manager()
    summary = manager.get_usage_summary()
    
    return BudgetResponse(data=summary)


@router.get("/budget/user/{user_id}")
async def get_user_budget(user_id: str) -> BudgetResponse:
    """获取用户预算使用量"""
    manager = get_budget_manager()
    usage = manager.get_user_usage(user_id)
    
    return BudgetResponse(data=usage)


@router.get("/budget/alerts")
async def get_budget_alerts(
    limit: int = 50,
    level: Optional[str] = None,
) -> BudgetResponse:
    """获取预算告警"""
    manager = get_budget_manager()
    
    alert_level = None
    if level:
        try:
            alert_level = AlertLevel(level)
        except ValueError:
            pass
    
    alerts = manager.get_alerts(limit=limit, level=alert_level)
    
    items = [
        {
            "level": a.level.value,
            "budget_type": a.budget_type,
            "current_usage": a.current_usage,
            "budget_limit": a.budget_limit,
            "usage_percent": a.usage_percent,
            "message": a.message,
            "timestamp": a.timestamp.isoformat(),
            "user_id": a.user_id,
        }
        for a in alerts
    ]
    
    return BudgetResponse(
        data={
            "items": items,
            "count": len(items),
        }
    )


@router.patch("/budget/config")
async def update_budget_config(request: BudgetConfigUpdate) -> BudgetResponse:
    """更新预算配置"""
    manager = get_budget_manager()
    
    manager.update_config(
        daily_budget=request.daily_budget,
        monthly_budget=request.monthly_budget,
        user_daily_limit=request.user_daily_limit,
        block_on_exceed=request.block_on_exceed,
    )
    
    return BudgetResponse(
        message="配置已更新",
        data={
            "daily_budget": manager.config.daily_budget,
            "monthly_budget": manager.config.monthly_budget,
            "user_daily_limit": manager.config.user_daily_limit,
            "block_on_exceed": manager.config.block_on_exceed,
        }
    )


@router.get("/budget/config")
async def get_budget_config() -> BudgetResponse:
    """获取预算配置"""
    manager = get_budget_manager()
    
    return BudgetResponse(
        data={
            "daily_budget": manager.config.daily_budget,
            "monthly_budget": manager.config.monthly_budget,
            "user_daily_limit": manager.config.user_daily_limit,
            "block_on_exceed": manager.config.block_on_exceed,
            "alert_thresholds": manager.config.alert_thresholds,
        }
    )


@router.post("/budget/check")
async def check_budget(
    estimated_cost: float = 0.01,
    user_id: Optional[str] = None,
) -> BudgetResponse:
    """检查是否可以继续请求"""
    manager = get_budget_manager()
    
    can_proceed, reason = manager.check_can_proceed(
        estimated_cost=estimated_cost,
        user_id=user_id,
    )
    
    return BudgetResponse(
        data={
            "can_proceed": can_proceed,
            "reason": reason,
        }
    )
