"""Webhook 路由"""

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel

from auto.gateway.webhook.handlers import get_webhook_router

router = APIRouter()


class WebhookResponse(BaseModel):
    """Webhook 响应"""
    code: int = 0
    message: str = "success"
    data: dict = {}


@router.post("/webhook/{source}")
async def handle_webhook(
    source: str,
    request: Request,
    background_tasks: BackgroundTasks,
):
    """处理 Webhook 请求
    
    支持的来源:
    - wechat_work: 企业微信
    - dingtalk: 钉钉
    - feishu: 飞书
    - custom: 自定义
    """
    webhook_router = get_webhook_router()
    
    # 获取处理器
    handler = webhook_router.get_handler(source)
    if not handler:
        raise HTTPException(status_code=404, detail=f"未知的 Webhook 来源: {source}")
    
    # 解析请求
    try:
        # 获取请求体
        content_type = request.headers.get("content-type", "")
        
        if "application/json" in content_type:
            request_data = await request.json()
        elif "application/xml" in content_type or "text/xml" in content_type:
            # 解析 XML
            body = await request.body()
            request_data = _parse_xml(body.decode())
        else:
            request_data = dict(request.query_params)
        
        headers = dict(request.headers)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"解析请求失败: {str(e)}")
    
    # 处理飞书 URL 验证
    if source == "feishu" and request_data.get("type") == "url_verification":
        return {"challenge": request_data.get("challenge", "")}
    
    # 处理企业微信 URL 验证
    if source == "wechat_work" and request.query_params.get("echostr"):
        return request.query_params.get("echostr")
    
    # 异步处理 Webhook
    background_tasks.add_task(
        _process_webhook,
        handler,
        request_data,
        headers,
    )
    
    # 立即返回成功
    return WebhookResponse(message="已接收")


async def _process_webhook(handler, request_data: dict, headers: dict):
    """异步处理 Webhook"""
    try:
        await handler.handle(request_data, headers)
    except Exception as e:
        # 记录错误日志
        import logging
        logging.error(f"Webhook 处理失败: {str(e)}")


def _parse_xml(xml_string: str) -> dict:
    """解析 XML 字符串"""
    try:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml_string)
        
        result = {}
        for child in root:
            if child.text:
                result[child.tag] = child.text
        
        return result
    except Exception:
        return {}


@router.get("/webhook/status")
async def webhook_status():
    """获取 Webhook 状态"""
    webhook_router = get_webhook_router()
    handlers = webhook_router.list_handlers()
    
    return WebhookResponse(
        data={
            "handlers": handlers,
            "count": len(handlers),
        }
    )
