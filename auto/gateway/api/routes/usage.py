"""用量统计 API 路由"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from auto.core.usage.tracker import get_usage_tracker

router = APIRouter()


class UsageResponse(BaseModel):
    """用量响应"""
    code: int = 0
    message: str = "success"
    data: dict = {}


@router.get("/usage/summary")
async def get_usage_summary(
    user_id: Optional[str] = Query(None, description="用户 ID"),
    workspace_id: Optional[str] = Query(None, description="工作空间 ID"),
    provider: Optional[str] = Query(None, description="提供商"),
    model: Optional[str] = Query(None, description="模型"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
) -> UsageResponse:
    """获取用量汇总"""
    tracker = get_usage_tracker()
    
    # 解析日期
    start = None
    end = None
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            pass
    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            pass
    
    summary = tracker.get_summary(
        start_date=start,
        end_date=end,
        user_id=user_id,
        workspace_id=workspace_id,
        provider=provider,
        model=model,
    )
    
    return UsageResponse(
        data={
            "total_requests": summary.total_requests,
            "total_prompt_tokens": summary.total_prompt_tokens,
            "total_completion_tokens": summary.total_completion_tokens,
            "total_tokens": summary.total_tokens,
            "total_cost": summary.total_cost,
            "by_provider": summary.by_provider,
            "by_model": summary.by_model,
            "by_date": summary.by_date,
        }
    )


@router.get("/usage/today")
async def get_today_usage(
    user_id: Optional[str] = Query(None),
    workspace_id: Optional[str] = Query(None),
) -> UsageResponse:
    """获取今日用量"""
    tracker = get_usage_tracker()
    
    summary = tracker.get_today_summary(
        user_id=user_id,
        workspace_id=workspace_id,
    )
    
    return UsageResponse(
        data={
            "date": datetime.now().strftime("%Y-%m-%d"),
            "total_requests": summary.total_requests,
            "total_tokens": summary.total_tokens,
            "total_cost": summary.total_cost,
            "by_model": summary.by_model,
        }
    )


@router.get("/usage/monthly")
async def get_monthly_usage(
    year: Optional[int] = Query(None, description="年份"),
    month: Optional[int] = Query(None, description="月份"),
    user_id: Optional[str] = Query(None),
    workspace_id: Optional[str] = Query(None),
) -> UsageResponse:
    """获取月度用量"""
    tracker = get_usage_tracker()
    
    now = datetime.now()
    year = year or now.year
    month = month or now.month
    
    summary = tracker.get_monthly_summary(
        year=year,
        month=month,
        user_id=user_id,
        workspace_id=workspace_id,
    )
    
    return UsageResponse(
        data={
            "year": year,
            "month": month,
            "total_requests": summary.total_requests,
            "total_tokens": summary.total_tokens,
            "total_cost": summary.total_cost,
            "by_date": summary.by_date,
            "by_model": summary.by_model,
        }
    )


@router.get("/usage/records")
async def get_usage_records(
    limit: int = Query(100, le=1000),
    user_id: Optional[str] = Query(None),
    workspace_id: Optional[str] = Query(None),
) -> UsageResponse:
    """获取最近的用量记录"""
    tracker = get_usage_tracker()
    
    records = tracker.get_recent_records(
        limit=limit,
        user_id=user_id,
        workspace_id=workspace_id,
    )
    
    items = [
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
    
    return UsageResponse(
        data={
            "items": items,
            "count": len(items),
        }
    )


@router.get("/usage/export")
async def export_usage(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
) -> UsageResponse:
    """导出用量数据"""
    tracker = get_usage_tracker()
    
    start = None
    end = None
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            pass
    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            pass
    
    records = tracker.export_records(start_date=start, end_date=end)
    
    return UsageResponse(
        data={
            "records": records,
            "count": len(records),
            "exported_at": datetime.now().isoformat(),
        }
    )
