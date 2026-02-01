"""邮件助手技能"""

import asyncio
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Optional

from auto.core.skill.base import Skill, ToolDefinition
from auto.core.tool.context import ToolContext
from auto.core.tool.result import ToolResult


class EmailSkill(Skill):
    """邮件助手技能
    
    提供邮件读取、发送、搜索等功能。
    """
    
    @property
    def name(self) -> str:
        return "email"
    
    @property
    def display_name(self) -> str:
        return "邮件助手"
    
    @property
    def description(self) -> str:
        return "邮件读取、发送、搜索、总结"
    
    @property
    def category(self) -> str:
        return "productivity"
    
    @property
    def tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="read_inbox",
                description="读取收件箱邮件",
                parameters={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "读取数量",
                            "default": 10,
                        },
                        "unread_only": {
                            "type": "boolean",
                            "description": "仅未读邮件",
                            "default": False,
                        },
                    },
                },
                handler=self.read_inbox,
            ),
            ToolDefinition(
                name="read_email",
                description="读取单封邮件详情",
                parameters={
                    "type": "object",
                    "properties": {
                        "email_id": {
                            "type": "string",
                            "description": "邮件 ID",
                        },
                    },
                    "required": ["email_id"],
                },
                handler=self.read_email,
            ),
            ToolDefinition(
                name="send_email",
                description="发送邮件",
                parameters={
                    "type": "object",
                    "properties": {
                        "to": {
                            "type": "string",
                            "description": "收件人邮箱 (多个用逗号分隔)",
                        },
                        "subject": {
                            "type": "string",
                            "description": "邮件主题",
                        },
                        "body": {
                            "type": "string",
                            "description": "邮件正文",
                        },
                        "html": {
                            "type": "boolean",
                            "description": "是否为 HTML 格式",
                            "default": False,
                        },
                        "cc": {
                            "type": "string",
                            "description": "抄送",
                        },
                        "attachments": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "附件路径列表",
                        },
                    },
                    "required": ["to", "subject", "body"],
                },
                dangerous=True,
                requires_confirmation=True,
                handler=self.send_email,
            ),
            ToolDefinition(
                name="search_emails",
                description="搜索邮件",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索关键词",
                        },
                        "folder": {
                            "type": "string",
                            "description": "邮件文件夹",
                            "default": "INBOX",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "返回数量",
                            "default": 20,
                        },
                    },
                    "required": ["query"],
                },
                handler=self.search_emails,
            ),
            ToolDefinition(
                name="reply_email",
                description="回复邮件",
                parameters={
                    "type": "object",
                    "properties": {
                        "email_id": {
                            "type": "string",
                            "description": "原邮件 ID",
                        },
                        "body": {
                            "type": "string",
                            "description": "回复内容",
                        },
                        "reply_all": {
                            "type": "boolean",
                            "description": "是否回复所有人",
                            "default": False,
                        },
                    },
                    "required": ["email_id", "body"],
                },
                dangerous=True,
                requires_confirmation=True,
                handler=self.reply_email,
            ),
            ToolDefinition(
                name="draft_email",
                description="生成邮件草稿 (不发送)",
                parameters={
                    "type": "object",
                    "properties": {
                        "to": {
                            "type": "string",
                            "description": "收件人",
                        },
                        "subject": {
                            "type": "string",
                            "description": "主题",
                        },
                        "body": {
                            "type": "string",
                            "description": "正文",
                        },
                        "context": {
                            "type": "string",
                            "description": "背景信息 (用于 AI 优化)",
                        },
                    },
                    "required": ["to", "subject", "body"],
                },
                handler=self.draft_email,
            ),
            ToolDefinition(
                name="get_email_config",
                description="获取邮件配置状态",
                parameters={
                    "type": "object",
                    "properties": {},
                },
                handler=self.get_email_config,
            ),
        ]
    
    @property
    def system_prompt(self) -> str:
        return """你是一个专业的邮件助手，可以帮助用户：
- 阅读和搜索邮件
- 撰写专业的邮件回复
- 管理邮件和日程
- 提取邮件中的重要信息

写邮件原则：
1. 专业、礼貌、简洁
2. 结构清晰，重点突出
3. 根据收件人调整语气
4. 检查附件和链接"""
    
    def _get_email_config(self, ctx: ToolContext) -> dict:
        """获取邮件配置"""
        return {
            "imap_host": ctx.config.get("email_imap_host", ""),
            "imap_port": ctx.config.get("email_imap_port", 993),
            "smtp_host": ctx.config.get("email_smtp_host", ""),
            "smtp_port": ctx.config.get("email_smtp_port", 587),
            "username": ctx.config.get("email_username", ""),
            "password": ctx.config.get("email_password", ""),
        }
    
    async def read_inbox(
        self,
        ctx: ToolContext,
        limit: int = 10,
        unread_only: bool = False,
    ) -> ToolResult:
        """读取收件箱"""
        config = self._get_email_config(ctx)
        
        if not config["imap_host"] or not config["username"]:
            return ToolResult.error_result(
                "邮件未配置，请设置: email_imap_host, email_username, email_password"
            )
        
        try:
            import imaplib
            import email
            from email.header import decode_header
        except ImportError:
            return ToolResult.error_result("需要 Python 标准库 imaplib")
        
        try:
            # 连接 IMAP 服务器
            mail = imaplib.IMAP4_SSL(config["imap_host"], config["imap_port"])
            mail.login(config["username"], config["password"])
            mail.select("INBOX")
            
            # 搜索邮件
            if unread_only:
                status, messages = mail.search(None, "UNSEEN")
            else:
                status, messages = mail.search(None, "ALL")
            
            email_ids = messages[0].split()
            
            # 获取最新的邮件
            email_ids = email_ids[-limit:][::-1]
            
            emails = []
            for eid in email_ids:
                status, msg_data = mail.fetch(eid, "(RFC822)")
                
                for response in msg_data:
                    if isinstance(response, tuple):
                        msg = email.message_from_bytes(response[1])
                        
                        # 解码主题
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding or "utf-8", errors="ignore")
                        
                        # 解码发件人
                        from_header, encoding = decode_header(msg["From"])[0]
                        if isinstance(from_header, bytes):
                            from_header = from_header.decode(encoding or "utf-8", errors="ignore")
                        
                        emails.append({
                            "id": eid.decode(),
                            "subject": subject,
                            "from": from_header,
                            "date": msg["Date"],
                            "has_attachment": msg.is_multipart(),
                        })
            
            mail.logout()
            
            return ToolResult.table(
                data=emails,
                message=f"读取到 {len(emails)} 封邮件",
            )
        except Exception as e:
            return ToolResult.error_result(f"读取邮件失败: {str(e)}")
    
    async def read_email(
        self,
        ctx: ToolContext,
        email_id: str,
    ) -> ToolResult:
        """读取单封邮件"""
        config = self._get_email_config(ctx)
        
        if not config["imap_host"]:
            return ToolResult.error_result("邮件未配置")
        
        try:
            import imaplib
            import email
            from email.header import decode_header
        except ImportError:
            return ToolResult.error_result("需要 Python 标准库 imaplib")
        
        try:
            mail = imaplib.IMAP4_SSL(config["imap_host"], config["imap_port"])
            mail.login(config["username"], config["password"])
            mail.select("INBOX")
            
            status, msg_data = mail.fetch(email_id.encode(), "(RFC822)")
            
            if status != "OK":
                return ToolResult.error_result(f"邮件不存在: {email_id}")
            
            msg = email.message_from_bytes(msg_data[0][1])
            
            # 解码主题
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8", errors="ignore")
            
            # 解码发件人
            from_header, encoding = decode_header(msg["From"])[0]
            if isinstance(from_header, bytes):
                from_header = from_header.decode(encoding or "utf-8", errors="ignore")
            
            # 获取正文
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain":
                        payload = part.get_payload(decode=True)
                        charset = part.get_content_charset() or "utf-8"
                        body = payload.decode(charset, errors="ignore")
                        break
            else:
                payload = msg.get_payload(decode=True)
                charset = msg.get_content_charset() or "utf-8"
                body = payload.decode(charset, errors="ignore")
            
            mail.logout()
            
            return ToolResult.success_result(
                data={
                    "id": email_id,
                    "subject": subject,
                    "from": from_header,
                    "to": msg["To"],
                    "date": msg["Date"],
                    "body": body[:5000],  # 限制长度
                },
                message=f"邮件: {subject}",
            )
        except Exception as e:
            return ToolResult.error_result(f"读取邮件失败: {str(e)}")
    
    async def send_email(
        self,
        ctx: ToolContext,
        to: str,
        subject: str,
        body: str,
        html: bool = False,
        cc: Optional[str] = None,
        attachments: Optional[list[str]] = None,
    ) -> ToolResult:
        """发送邮件"""
        config = self._get_email_config(ctx)
        
        if not config["smtp_host"] or not config["username"]:
            return ToolResult.error_result(
                "邮件未配置，请设置: email_smtp_host, email_username, email_password"
            )
        
        try:
            import smtplib
        except ImportError:
            return ToolResult.error_result("需要 Python 标准库 smtplib")
        
        try:
            # 创建邮件
            if attachments:
                msg = MIMEMultipart()
                msg.attach(MIMEText(body, "html" if html else "plain", "utf-8"))
                
                # 添加附件
                for att_path in attachments:
                    path = Path(att_path).expanduser()
                    if path.exists():
                        with open(path, "rb") as f:
                            part = MIMEBase("application", "octet-stream")
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                "Content-Disposition",
                                f"attachment; filename={path.name}",
                            )
                            msg.attach(part)
            else:
                msg = MIMEText(body, "html" if html else "plain", "utf-8")
            
            msg["Subject"] = subject
            msg["From"] = config["username"]
            msg["To"] = to
            if cc:
                msg["Cc"] = cc
            
            # 发送邮件
            with smtplib.SMTP(config["smtp_host"], config["smtp_port"]) as server:
                server.starttls()
                server.login(config["username"], config["password"])
                
                recipients = to.split(",")
                if cc:
                    recipients.extend(cc.split(","))
                
                server.sendmail(config["username"], recipients, msg.as_string())
            
            return ToolResult.success_result(
                data={
                    "to": to,
                    "subject": subject,
                    "sent_at": datetime.now().isoformat(),
                },
                message=f"邮件已发送至: {to}",
            )
        except Exception as e:
            return ToolResult.error_result(f"发送邮件失败: {str(e)}")
    
    async def search_emails(
        self,
        ctx: ToolContext,
        query: str,
        folder: str = "INBOX",
        limit: int = 20,
    ) -> ToolResult:
        """搜索邮件"""
        config = self._get_email_config(ctx)
        
        if not config["imap_host"]:
            return ToolResult.error_result("邮件未配置")
        
        try:
            import imaplib
            import email
            from email.header import decode_header
        except ImportError:
            return ToolResult.error_result("需要 Python 标准库 imaplib")
        
        try:
            mail = imaplib.IMAP4_SSL(config["imap_host"], config["imap_port"])
            mail.login(config["username"], config["password"])
            mail.select(folder)
            
            # 搜索
            status, messages = mail.search(None, f'(OR SUBJECT "{query}" BODY "{query}")')
            
            email_ids = messages[0].split()[-limit:][::-1]
            
            emails = []
            for eid in email_ids:
                status, msg_data = mail.fetch(eid, "(RFC822)")
                
                for response in msg_data:
                    if isinstance(response, tuple):
                        msg = email.message_from_bytes(response[1])
                        
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding or "utf-8", errors="ignore")
                        
                        from_header, encoding = decode_header(msg["From"])[0]
                        if isinstance(from_header, bytes):
                            from_header = from_header.decode(encoding or "utf-8", errors="ignore")
                        
                        emails.append({
                            "id": eid.decode(),
                            "subject": subject,
                            "from": from_header,
                            "date": msg["Date"],
                        })
            
            mail.logout()
            
            return ToolResult.table(
                data=emails,
                message=f"搜索 '{query}' 找到 {len(emails)} 封邮件",
            )
        except Exception as e:
            return ToolResult.error_result(f"搜索邮件失败: {str(e)}")
    
    async def reply_email(
        self,
        ctx: ToolContext,
        email_id: str,
        body: str,
        reply_all: bool = False,
    ) -> ToolResult:
        """回复邮件"""
        # 先读取原邮件
        original = await self.read_email(ctx, email_id)
        if not original.success:
            return original
        
        data = original.data
        
        # 构建回复
        to = data["from"]
        if reply_all and data.get("to"):
            # 添加其他收件人
            pass
        
        subject = data["subject"]
        if not subject.lower().startswith("re:"):
            subject = f"Re: {subject}"
        
        # 添加引用
        quoted = f"\n\n--- Original Message ---\n{data.get('body', '')[:1000]}"
        full_body = body + quoted
        
        return await self.send_email(
            ctx,
            to=to,
            subject=subject,
            body=full_body,
        )
    
    async def draft_email(
        self,
        ctx: ToolContext,
        to: str,
        subject: str,
        body: str,
        context: Optional[str] = None,
    ) -> ToolResult:
        """生成邮件草稿"""
        draft = {
            "to": to,
            "subject": subject,
            "body": body,
            "created_at": datetime.now().isoformat(),
            "status": "draft",
        }
        
        if context:
            draft["context"] = context
        
        return ToolResult.success_result(
            data=draft,
            message="邮件草稿已生成，确认后可发送",
        )
    
    async def get_email_config(self, ctx: ToolContext) -> ToolResult:
        """获取邮件配置状态"""
        config = self._get_email_config(ctx)
        
        has_imap = bool(config["imap_host"])
        has_smtp = bool(config["smtp_host"])
        has_credentials = bool(config["username"] and config["password"])
        
        return ToolResult.success_result(
            data={
                "imap_configured": has_imap,
                "smtp_configured": has_smtp,
                "credentials_set": has_credentials,
                "imap_host": config["imap_host"] or "(未配置)",
                "smtp_host": config["smtp_host"] or "(未配置)",
            },
            message="配置完整" if (has_imap and has_smtp and has_credentials) else "配置不完整",
        )
