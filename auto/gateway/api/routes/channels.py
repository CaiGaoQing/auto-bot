"""
渠道管理 API 路由

管理多渠道消息配置
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from auto.channels import ChannelManager, ChannelType, get_channel_manager

router = APIRouter(prefix="/channels", tags=["渠道管理"])


# ============ 请求/响应模型 ============

class ChannelConfig(BaseModel):
    """渠道配置"""
    name: str
    channel_type: str  # telegram, discord, wechat_work
    enabled: bool = True
    config: Dict[str, Any] = {}


class ChannelStatus(BaseModel):
    """渠道状态"""
    name: str
    channel_type: str
    connected: bool
    enabled: bool


class ChannelTestResult(BaseModel):
    """渠道测试结果"""
    success: bool
    message: str


# ============ 路由 ============

@router.get("", response_model=Dict[str, Any])
async def list_channels():
    """
    列出所有渠道
    
    返回所有配置的渠道及其状态
    """
    manager = get_channel_manager()
    status = manager.get_status()
    
    return {
        "success": True,
        "data": status,
    }


@router.post("")
async def add_channel(config: ChannelConfig):
    """
    添加渠道
    
    配置新的消息渠道
    """
    manager = get_channel_manager()
    
    try:
        channel_type = ChannelType(config.channel_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的渠道类型: {config.channel_type}"
        )
    
    try:
        await manager.add_channel(
            name=config.name,
            channel_type=channel_type,
            config=config.config,
        )
        
        return {
            "success": True,
            "message": f"渠道 {config.name} 添加成功",
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{name}")
async def remove_channel(name: str):
    """
    移除渠道
    """
    manager = get_channel_manager()
    manager.remove_channel(name)
    
    return {
        "success": True,
        "message": f"渠道 {name} 已移除",
    }


@router.post("/{name}/connect")
async def connect_channel(name: str):
    """
    连接渠道
    """
    manager = get_channel_manager()
    
    try:
        success = await manager.connect_channel(name)
        
        if success:
            return {
                "success": True,
                "message": f"渠道 {name} 连接成功",
            }
        else:
            return {
                "success": False,
                "message": f"渠道 {name} 连接失败",
            }
            
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{name}/disconnect")
async def disconnect_channel(name: str):
    """
    断开渠道
    """
    manager = get_channel_manager()
    await manager.disconnect_channel(name)
    
    return {
        "success": True,
        "message": f"渠道 {name} 已断开",
    }


@router.post("/{name}/test")
async def test_channel(name: str):
    """
    测试渠道连接
    """
    manager = get_channel_manager()
    channel = manager.channels.get(name)
    
    if not channel:
        raise HTTPException(status_code=404, detail=f"渠道不存在: {name}")
    
    # 验证配置
    valid, message = channel.validate_config()
    
    if not valid:
        return {
            "success": False,
            "message": f"配置验证失败: {message}",
        }
    
    # 尝试连接
    try:
        if not channel.is_connected:
            await channel.connect()
        
        return {
            "success": True,
            "message": "渠道测试成功",
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"连接失败: {str(e)}",
        }


@router.get("/types")
async def list_channel_types():
    """
    列出支持的渠道类型
    """
    types = [
        {
            "type": ChannelType.TELEGRAM.value,
            "name": "Telegram",
            "description": "Telegram Bot",
            "config_fields": [
                {"name": "token", "type": "string", "required": True, "description": "Bot Token"},
                {"name": "allowed_users", "type": "array", "required": False, "description": "允许的用户 ID"},
                {"name": "allowed_groups", "type": "array", "required": False, "description": "允许的群组 ID"},
            ]
        },
        {
            "type": ChannelType.DISCORD.value,
            "name": "Discord",
            "description": "Discord Bot",
            "config_fields": [
                {"name": "token", "type": "string", "required": True, "description": "Bot Token"},
                {"name": "allowed_guilds", "type": "array", "required": False, "description": "允许的服务器 ID"},
                {"name": "dm_enabled", "type": "boolean", "required": False, "description": "允许私信"},
            ]
        },
        {
            "type": ChannelType.WECHAT_WORK.value,
            "name": "企业微信",
            "description": "企业微信应用",
            "config_fields": [
                {"name": "corp_id", "type": "string", "required": True, "description": "企业 ID"},
                {"name": "agent_id", "type": "integer", "required": True, "description": "应用 ID"},
                {"name": "secret", "type": "string", "required": True, "description": "应用 Secret"},
                {"name": "token", "type": "string", "required": False, "description": "回调 Token"},
                {"name": "encoding_aes_key", "type": "string", "required": False, "description": "消息加密密钥"},
            ]
        },
    ]
    
    return {
        "success": True,
        "data": types,
    }
