"""Webhook 提供商处理器"""

import hashlib
import hmac
import time
from typing import Optional

import httpx

from auto.gateway.webhook.handlers import WebhookEvent, WebhookHandler, WebhookResponse


class WeChatWorkHandler(WebhookHandler):
    """企业微信 Webhook 处理器"""
    
    def __init__(
        self,
        corp_id: str = "",
        agent_id: str = "",
        secret: str = "",
        token: str = "",
        encoding_aes_key: str = "",
    ):
        self.corp_id = corp_id
        self.agent_id = agent_id
        self.secret = secret
        self.token = token
        self.encoding_aes_key = encoding_aes_key
        self._access_token: Optional[str] = None
        self._token_expires: float = 0
    
    @property
    def source(self) -> str:
        return "wechat_work"
    
    async def verify(self, request_data: dict, headers: dict) -> bool:
        """验证企业微信请求签名"""
        msg_signature = request_data.get("msg_signature", "")
        timestamp = request_data.get("timestamp", "")
        nonce = request_data.get("nonce", "")
        
        if not all([msg_signature, timestamp, nonce]):
            return False
        
        # 计算签名
        sort_list = sorted([self.token, timestamp, nonce])
        signature = hashlib.sha1("".join(sort_list).encode()).hexdigest()
        
        return signature == msg_signature
    
    async def parse(self, request_data: dict, headers: dict) -> Optional[WebhookEvent]:
        """解析企业微信消息"""
        try:
            # 解析 XML 消息
            msg_type = request_data.get("MsgType", "")
            
            if msg_type == "text":
                return WebhookEvent(
                    source=self.source,
                    event_type="message",
                    user_id=request_data.get("FromUserName", ""),
                    content=request_data.get("Content", ""),
                    raw_data=request_data,
                    conversation_id=request_data.get("AgentID", ""),
                )
            elif msg_type == "event":
                return WebhookEvent(
                    source=self.source,
                    event_type=request_data.get("Event", ""),
                    user_id=request_data.get("FromUserName", ""),
                    content="",
                    raw_data=request_data,
                )
            
            return None
        except Exception:
            return None
    
    async def reply(self, event: WebhookEvent, content: str) -> WebhookResponse:
        """发送企业微信回复"""
        try:
            # 获取 access_token
            access_token = await self._get_access_token()
            
            if not access_token:
                return WebhookResponse(success=False, message="获取 access_token 失败")
            
            # 发送消息
            url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
            
            payload = {
                "touser": event.user_id,
                "msgtype": "text",
                "agentid": self.agent_id,
                "text": {"content": content},
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)
                data = response.json()
            
            if data.get("errcode") == 0:
                return WebhookResponse(success=True, message="发送成功")
            else:
                return WebhookResponse(
                    success=False,
                    message=f"发送失败: {data.get('errmsg', '')}",
                )
        except Exception as e:
            return WebhookResponse(success=False, message=f"发送失败: {str(e)}")
    
    async def _get_access_token(self) -> Optional[str]:
        """获取 access_token"""
        if self._access_token and time.time() < self._token_expires:
            return self._access_token
        
        try:
            url = (
                f"https://qyapi.weixin.qq.com/cgi-bin/gettoken"
                f"?corpid={self.corp_id}&corpsecret={self.secret}"
            )
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                data = response.json()
            
            if data.get("errcode") == 0:
                self._access_token = data["access_token"]
                self._token_expires = time.time() + data.get("expires_in", 7200) - 300
                return self._access_token
            
            return None
        except Exception:
            return None


class DingTalkHandler(WebhookHandler):
    """钉钉 Webhook 处理器"""
    
    def __init__(
        self,
        app_key: str = "",
        app_secret: str = "",
        agent_id: str = "",
    ):
        self.app_key = app_key
        self.app_secret = app_secret
        self.agent_id = agent_id
        self._access_token: Optional[str] = None
        self._token_expires: float = 0
    
    @property
    def source(self) -> str:
        return "dingtalk"
    
    async def verify(self, request_data: dict, headers: dict) -> bool:
        """验证钉钉请求签名"""
        timestamp = headers.get("timestamp", "")
        sign = headers.get("sign", "")
        
        if not all([timestamp, sign]):
            return True  # 某些场景没有签名
        
        # 验证签名
        string_to_sign = f"{timestamp}\n{self.app_secret}"
        hmac_code = hmac.new(
            self.app_secret.encode(),
            string_to_sign.encode(),
            hashlib.sha256,
        ).digest()
        
        import base64
        calculated_sign = base64.b64encode(hmac_code).decode()
        
        return calculated_sign == sign
    
    async def parse(self, request_data: dict, headers: dict) -> Optional[WebhookEvent]:
        """解析钉钉消息"""
        try:
            msg_type = request_data.get("msgtype", "")
            
            if msg_type == "text":
                text = request_data.get("text", {})
                sender = request_data.get("senderStaffId", "") or request_data.get("senderId", "")
                
                return WebhookEvent(
                    source=self.source,
                    event_type="message",
                    user_id=sender,
                    content=text.get("content", ""),
                    raw_data=request_data,
                    conversation_id=request_data.get("conversationId", ""),
                )
            
            return None
        except Exception:
            return None
    
    async def reply(self, event: WebhookEvent, content: str) -> WebhookResponse:
        """发送钉钉回复"""
        try:
            access_token = await self._get_access_token()
            
            if not access_token:
                return WebhookResponse(success=False, message="获取 access_token 失败")
            
            # 发送消息
            url = f"https://oapi.dingtalk.com/topapi/message/corpconversation/asyncsend_v2?access_token={access_token}"
            
            payload = {
                "agent_id": self.agent_id,
                "userid_list": event.user_id,
                "msg": {
                    "msgtype": "text",
                    "text": {"content": content},
                },
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)
                data = response.json()
            
            if data.get("errcode") == 0:
                return WebhookResponse(success=True, message="发送成功")
            else:
                return WebhookResponse(
                    success=False,
                    message=f"发送失败: {data.get('errmsg', '')}",
                )
        except Exception as e:
            return WebhookResponse(success=False, message=f"发送失败: {str(e)}")
    
    async def _get_access_token(self) -> Optional[str]:
        """获取 access_token"""
        if self._access_token and time.time() < self._token_expires:
            return self._access_token
        
        try:
            url = (
                f"https://oapi.dingtalk.com/gettoken"
                f"?appkey={self.app_key}&appsecret={self.app_secret}"
            )
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                data = response.json()
            
            if data.get("errcode") == 0:
                self._access_token = data["access_token"]
                self._token_expires = time.time() + data.get("expires_in", 7200) - 300
                return self._access_token
            
            return None
        except Exception:
            return None


class FeishuHandler(WebhookHandler):
    """飞书 Webhook 处理器"""
    
    def __init__(
        self,
        app_id: str = "",
        app_secret: str = "",
        verification_token: str = "",
        encrypt_key: str = "",
    ):
        self.app_id = app_id
        self.app_secret = app_secret
        self.verification_token = verification_token
        self.encrypt_key = encrypt_key
        self._access_token: Optional[str] = None
        self._token_expires: float = 0
    
    @property
    def source(self) -> str:
        return "feishu"
    
    async def verify(self, request_data: dict, headers: dict) -> bool:
        """验证飞书请求"""
        # 验证 token
        token = request_data.get("token", "")
        
        if token and self.verification_token:
            return token == self.verification_token
        
        return True
    
    async def parse(self, request_data: dict, headers: dict) -> Optional[WebhookEvent]:
        """解析飞书消息"""
        try:
            # URL 验证
            if request_data.get("type") == "url_verification":
                return None  # 需要特殊处理
            
            event = request_data.get("event", {})
            message = event.get("message", {})
            
            if not message:
                return None
            
            # 解析消息内容
            msg_type = message.get("message_type", "")
            content = ""
            
            if msg_type == "text":
                content_data = message.get("content", "{}")
                import json
                content_json = json.loads(content_data)
                content = content_json.get("text", "")
            
            sender = event.get("sender", {})
            
            return WebhookEvent(
                source=self.source,
                event_type="message",
                user_id=sender.get("sender_id", {}).get("user_id", ""),
                content=content,
                raw_data=request_data,
                conversation_id=message.get("chat_id", ""),
            )
        except Exception:
            return None
    
    async def reply(self, event: WebhookEvent, content: str) -> WebhookResponse:
        """发送飞书回复"""
        try:
            access_token = await self._get_access_token()
            
            if not access_token:
                return WebhookResponse(success=False, message="获取 access_token 失败")
            
            # 发送消息
            url = "https://open.feishu.cn/open-apis/im/v1/messages"
            
            import json
            payload = {
                "receive_id": event.user_id,
                "msg_type": "text",
                "content": json.dumps({"text": content}),
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    params={"receive_id_type": "user_id"},
                    headers={"Authorization": f"Bearer {access_token}"},
                    json=payload,
                )
                data = response.json()
            
            if data.get("code") == 0:
                return WebhookResponse(success=True, message="发送成功")
            else:
                return WebhookResponse(
                    success=False,
                    message=f"发送失败: {data.get('msg', '')}",
                )
        except Exception as e:
            return WebhookResponse(success=False, message=f"发送失败: {str(e)}")
    
    async def _get_access_token(self) -> Optional[str]:
        """获取 tenant_access_token"""
        if self._access_token and time.time() < self._token_expires:
            return self._access_token
        
        try:
            url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
            
            payload = {
                "app_id": self.app_id,
                "app_secret": self.app_secret,
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)
                data = response.json()
            
            if data.get("code") == 0:
                self._access_token = data["tenant_access_token"]
                self._token_expires = time.time() + data.get("expire", 7200) - 300
                return self._access_token
            
            return None
        except Exception:
            return None
