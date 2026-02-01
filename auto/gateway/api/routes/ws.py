"""WebSocket 路由"""

from datetime import datetime
from typing import Optional
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from auto.gateway.websocket.manager import get_connection_manager
from auto.gateway.websocket.handlers import WebSocketHandler

router = APIRouter()


@router.websocket("/ws")
async def websocket_chat(
    websocket: WebSocket,
    user_id: Optional[str] = Query(None),
    workspace_id: Optional[str] = Query(None),
    token: Optional[str] = Query(None),
):
    """WebSocket 聊天端点
    
    连接参数:
    - user_id: 用户 ID
    - workspace_id: 工作空间 ID (可选)
    - token: 认证 token (可选)
    
    消息格式:
    ```json
    {
        "type": "chat|ping|execute_tool|subscribe",
        "data": {...}
    }
    ```
    
    响应格式:
    ```json
    {
        "type": "chat_chunk|chat_response|pong|tool_result|error",
        "data": {...},
        "timestamp": "..."
    }
    ```
    """
    # 生成连接 ID
    connection_id = str(uuid.uuid4())
    
    # 如果没有提供 user_id，使用匿名 ID
    if not user_id:
        user_id = f"anonymous_{connection_id[:8]}"
    
    # TODO: 验证 token
    
    manager = get_connection_manager()
    handler = WebSocketHandler(manager)
    
    connection = await manager.connect(
        websocket=websocket,
        connection_id=connection_id,
        user_id=user_id,
        workspace_id=workspace_id,
    )
    
    try:
        # 发送连接成功消息
        await connection.send_json({
            "type": "connected",
            "connection_id": connection_id,
            "user_id": user_id,
            "workspace_id": workspace_id,
            "timestamp": datetime.now().isoformat(),
        })
        
        # 消息循环
        while True:
            data = await websocket.receive_text()
            
            response = await handler.handle(
                connection_id=connection_id,
                raw_message=data,
                user_id=user_id,
                workspace_id=workspace_id,
            )
            
            if response:
                await connection.send_json(response)
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        # 尝试发送错误消息
        try:
            await connection.send_json({
                "type": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            })
        except Exception:
            pass
    finally:
        await manager.disconnect(connection_id)


@router.get("/ws/stats")
async def websocket_stats():
    """获取 WebSocket 统计"""
    manager = get_connection_manager()
    stats = manager.get_stats()
    
    return {
        "code": 0,
        "data": stats,
    }
