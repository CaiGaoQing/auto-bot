"""审计日志 API 路由"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from auto.core.audit import get_audit_logger, EventType

router = APIRouter()


class AuditResponse(BaseModel):
    """审计响应"""
    code: int = 0
    message: str = "success"
    data: dict = {}


@router.get("/audit/logs")
async def get_audit_logs(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    user_id: Optional[str] = Query(None, description="用户 ID"),
    event_type: Optional[str] = Query(None, description="事件类型"),
    limit: int = Query(100, le=1000),
) -> AuditResponse:
    """查询审计日志"""
    audit_logger = get_audit_logger()
    
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
    
    # 解析事件类型
    evt_type = None
    if event_type:
        try:
            evt_type = EventType(event_type)
        except ValueError:
            pass
    
    logs = audit_logger.query(
        start_date=start,
        end_date=end,
        user_id=user_id,
        event_type=evt_type,
        limit=limit,
    )
    
    return AuditResponse(
        data={
            "items": logs,
            "count": len(logs),
        }
    )


@router.get("/audit/stats")
async def get_audit_stats(
    days: int = Query(7, le=90),
) -> AuditResponse:
    """获取审计统计"""
    audit_logger = get_audit_logger()
    stats = audit_logger.get_stats(days=days)
    
    return AuditResponse(data=stats)


@router.get("/audit/event-types")
async def get_event_types() -> AuditResponse:
    """获取事件类型列表"""
    types = [
        {"value": e.value, "name": e.name}
        for e in EventType
    ]
    
    return AuditResponse(
        data={
            "types": types,
            "count": len(types),
        }
    )


@router.post("/audit/cleanup")
async def cleanup_audit_logs() -> AuditResponse:
    """清理过期审计日志"""
    audit_logger = get_audit_logger()
    deleted = audit_logger.cleanup()
    
    return AuditResponse(
        message=f"已清理 {deleted} 个过期日志文件",
        data={"deleted": deleted},
    )
