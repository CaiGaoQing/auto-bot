"""
企业微信 (WeCom) 渠道实现

使用企业微信开放 API
"""

import asyncio
import hashlib
import logging
import time
import xml.etree.ElementTree as ET
from typing import Optional, List
from datetime import datetime

import httpx

from .base import (
    BaseChannel,
    ChannelType,
    ChannelMessage,
    ChannelResponse,
    ChannelUser,
    MessageType,
    ChannelAuthError,
    ChannelConnectionError,
)

logger = logging.getLogger(__name__)


class WeComChannel(BaseChannel):
    """
    企业微信渠道
    
    配置示例:
    {
        "corp_id": "ww...",
        "agent_id": 1000002,
        "secret": "...",
        "token": "...",  # 用于验证回调
        "encoding_aes_key": "...",  # 用于消息加解密
        "allowed_users": ["userid1", "userid2"],  # 可选：允许的用户
        "allowed_departments": [1, 2],  # 可选：允许的部门
    }
    """
    
    API_BASE = "https://qyapi.weixin.qq.com/cgi-bin"
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.channel_type = ChannelType.WECHAT_WORK
        
        self.corp_id = config.get("corp_id", "")
        self.agent_id = config.get("agent_id", 0)
        self.secret = config.get("secret", "")
        self.token = config.get("token", "")
        self.encoding_aes_key = config.get("encoding_aes_key", "")
        
        self.allowed_users = set(config.get("allowed_users", []))
        self.allowed_departments = set(config.get("allowed_departments", []))
        
        self._access_token = ""
        self._token_expires = 0
        self._http_client: Optional[httpx.AsyncClient] = None
    
    @property
    def name(self) -> str:
        return "企业微信"
    
    def validate_config(self) -> tuple[bool, str]:
        if not self.corp_id:
            return False, "缺少企业 ID (corp_id)"
        if not self.agent_id:
            return False, "缺少应用 ID (agent_id)"
        if not self.secret:
            return False, "缺少应用 Secret"
        return True, "OK"
    
    async def connect(self) -> bool:
        """连接到企业微信"""
        valid, msg = self.validate_config()
        if not valid:
            raise ChannelAuthError("wechat_work", msg)
        
        self._http_client = httpx.AsyncClient(timeout=30)
        
        # 获取 access_token
        try:
            await self._refresh_token()
        except Exception as e:
            raise ChannelConnectionError("wechat_work", f"获取 access_token 失败: {e}")
        
        self._running = True
        logger.info("企业微信已连接")
        return True
    
    async def disconnect(self):
        """断开连接"""
        if self._http_client:
            await self._http_client.aclose()
        self._running = False
        logger.info("企业微信已断开")
    
    async def _refresh_token(self):
        """刷新 access_token"""
        url = f"{self.API_BASE}/gettoken"
        params = {
            "corpid": self.corp_id,
            "corpsecret": self.secret,
        }
        
        resp = await self._http_client.get(url, params=params)
        data = resp.json()
        
        if data.get("errcode", 0) != 0:
            raise ChannelAuthError("wechat_work", data.get("errmsg", "未知错误"))
        
        self._access_token = data["access_token"]
        self._token_expires = time.time() + data["expires_in"] - 300  # 提前 5 分钟刷新
        logger.debug("企业微信 access_token 已刷新")
    
    async def _get_token(self) -> str:
        """获取有效的 access_token"""
        if time.time() >= self._token_expires:
            await self._refresh_token()
        return self._access_token
    
    async def send_message(
        self,
        channel_id: str,
        response: ChannelResponse
    ) -> bool:
        """发送消息"""
        if not self._http_client:
            return False
        
        try:
            token = await self._get_token()
            url = f"{self.API_BASE}/message/send?access_token={token}"
            
            # 基础消息体
            payload = {
                "touser": channel_id,
                "agentid": self.agent_id,
            }
            
            # 根据消息类型发送
            if response.message_type == MessageType.TEXT:
                # 文本消息
                payload["msgtype"] = "text"
                payload["text"] = {"content": response.content}
            
            elif response.message_type == MessageType.IMAGE and response.attachments:
                # 图片消息（需要先上传）
                att = response.attachments[0]
                if att.get("media_id"):
                    payload["msgtype"] = "image"
                    payload["image"] = {"media_id": att["media_id"]}
                else:
                    # 降级为文本
                    payload["msgtype"] = "text"
                    payload["text"] = {"content": response.content}
            
            elif response.message_type == MessageType.FILE and response.attachments:
                # 文件消息
                att = response.attachments[0]
                if att.get("media_id"):
                    payload["msgtype"] = "file"
                    payload["file"] = {"media_id": att["media_id"]}
                else:
                    payload["msgtype"] = "text"
                    payload["text"] = {"content": response.content}
            
            else:
                # 默认文本
                payload["msgtype"] = "text"
                payload["text"] = {"content": response.content}
            
            # 发送
            resp = await self._http_client.post(url, json=payload)
            data = resp.json()
            
            if data.get("errcode", 0) != 0:
                logger.error(f"企业微信发送失败: {data.get('errmsg')}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"企业微信发送消息失败: {e}")
            return False
    
    async def send_typing(self, channel_id: str):
        """企业微信不支持 typing 状态"""
        pass
    
    async def upload_media(
        self,
        file_path: str,
        media_type: str = "file"
    ) -> Optional[str]:
        """
        上传临时素材
        
        Args:
            file_path: 文件路径
            media_type: 媒体类型 (image/voice/video/file)
        
        Returns:
            media_id
        """
        if not self._http_client:
            return None
        
        try:
            token = await self._get_token()
            url = f"{self.API_BASE}/media/upload?access_token={token}&type={media_type}"
            
            with open(file_path, "rb") as f:
                files = {"media": f}
                resp = await self._http_client.post(url, files=files)
            
            data = resp.json()
            if data.get("errcode", 0) != 0:
                logger.error(f"上传媒体失败: {data.get('errmsg')}")
                return None
            
            return data.get("media_id")
            
        except Exception as e:
            logger.error(f"上传媒体失败: {e}")
            return None
    
    async def get_user_info(self, user_id: str) -> Optional[ChannelUser]:
        """获取用户信息"""
        if not self._http_client:
            return None
        
        try:
            token = await self._get_token()
            url = f"{self.API_BASE}/user/get?access_token={token}&userid={user_id}"
            
            resp = await self._http_client.get(url)
            data = resp.json()
            
            if data.get("errcode", 0) != 0:
                return None
            
            return ChannelUser(
                id=data["userid"],
                username=data.get("userid"),
                display_name=data.get("name"),
                avatar_url=data.get("avatar"),
                raw_data=data,
            )
            
        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            return None
    
    def verify_callback(self, msg_signature: str, timestamp: str, nonce: str, echostr: str) -> Optional[str]:
        """
        验证回调 URL
        
        用于企业微信验证服务器配置
        """
        try:
            # 这里需要使用 WXBizMsgCrypt 库进行解密
            # 简化版本仅做签名验证
            sort_list = sorted([self.token, timestamp, nonce, echostr])
            sha1 = hashlib.sha1("".join(sort_list).encode()).hexdigest()
            
            if sha1 == msg_signature:
                # 需要解密 echostr 返回
                # 这里简化处理
                return echostr
            return None
        except Exception as e:
            logger.error(f"验证回调失败: {e}")
            return None
    
    def parse_callback_message(self, xml_data: str) -> Optional[ChannelMessage]:
        """
        解析回调消息
        
        企业微信通过 Webhook 推送消息
        """
        try:
            root = ET.fromstring(xml_data)
            
            msg_type = root.find("MsgType").text
            from_user = root.find("FromUserName").text
            create_time = root.find("CreateTime").text
            msg_id = root.find("MsgId").text if root.find("MsgId") is not None else str(time.time())
            
            # 检查权限
            if self.allowed_users and from_user not in self.allowed_users:
                return None
            
            content = ""
            message_type = MessageType.TEXT
            attachments = []
            
            if msg_type == "text":
                content = root.find("Content").text
            elif msg_type == "image":
                message_type = MessageType.IMAGE
                media_id = root.find("MediaId").text
                pic_url = root.find("PicUrl").text if root.find("PicUrl") is not None else ""
                attachments.append({
                    "type": "image",
                    "media_id": media_id,
                    "url": pic_url,
                })
            elif msg_type == "voice":
                message_type = MessageType.AUDIO
                media_id = root.find("MediaId").text
                attachments.append({
                    "type": "voice",
                    "media_id": media_id,
                })
            elif msg_type == "file":
                message_type = MessageType.FILE
                media_id = root.find("MediaId").text
                attachments.append({
                    "type": "file",
                    "media_id": media_id,
                })
            
            return ChannelMessage(
                id=msg_id,
                channel_type=ChannelType.WECHAT_WORK,
                channel_id=from_user,  # 企业微信用 userid 作为 channel
                sender=ChannelUser(
                    id=from_user,
                    username=from_user,
                ),
                content=content,
                message_type=message_type,
                attachments=attachments,
                timestamp=datetime.fromtimestamp(int(create_time)),
                raw_data={"xml": xml_data},
            )
            
        except Exception as e:
            logger.error(f"解析消息失败: {e}")
            return None
