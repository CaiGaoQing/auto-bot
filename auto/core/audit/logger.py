"""审计日志系统"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


class EventType(Enum):
    """事件类型"""
    # 认证相关
    LOGIN = "login"
    LOGOUT = "logout"
    AUTH_FAILED = "auth_failed"
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"
    
    # 资源操作
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    
    # AI 操作
    CHAT = "chat"
    TOOL_CALL = "tool_call"
    TOOL_EXECUTE = "tool_execute"
    
    # 危险操作
    DANGEROUS_OPERATION = "dangerous_operation"
    PERMISSION_DENIED = "permission_denied"
    
    # 系统事件
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    CONFIG_CHANGE = "config_change"
    ERROR = "error"


class Severity(Enum):
    """严重级别"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """审计事件"""
    event_type: EventType
    severity: Severity = Severity.INFO
    
    # 主体信息
    user_id: Optional[str] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    
    # 资源信息
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    
    # 操作信息
    action: str = ""
    details: dict = field(default_factory=dict)
    
    # 结果
    success: bool = True
    error_message: Optional[str] = None
    
    # 上下文
    workspace_id: Optional[str] = None
    conversation_id: Optional[str] = None
    request_id: Optional[str] = None
    
    # 时间戳
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = asdict(self)
        data["event_type"] = self.event_type.value
        data["severity"] = self.severity.value
        data["timestamp"] = self.timestamp.isoformat()
        return data
    
    def to_json(self) -> str:
        """转换为 JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False)


class AuditLogger:
    """审计日志记录器
    
    记录系统中的重要操作和事件，用于安全审计和问题追踪。
    """
    
    def __init__(
        self,
        log_dir: Optional[Path] = None,
        retention_days: int = 90,
    ):
        from auto.shared.config import DEFAULT_CONFIG_DIR
        
        self.log_dir = log_dir or DEFAULT_CONFIG_DIR / "audit_logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.retention_days = retention_days
        self._events: list[AuditEvent] = []
    
    def log(self, event: AuditEvent) -> None:
        """记录审计事件"""
        self._events.append(event)
        
        # 写入日志文件
        self._write_to_file(event)
        
        # 输出到标准日志
        log_message = (
            f"[AUDIT] {event.event_type.value} | "
            f"user={event.user_id or 'anonymous'} | "
            f"action={event.action} | "
            f"success={event.success}"
        )
        
        if event.severity == Severity.ERROR or event.severity == Severity.CRITICAL:
            logger.error(log_message)
        elif event.severity == Severity.WARNING:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def _write_to_file(self, event: AuditEvent) -> None:
        """写入日志文件"""
        date_str = event.timestamp.strftime("%Y-%m-%d")
        log_file = self.log_dir / f"audit_{date_str}.jsonl"
        
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(event.to_json() + "\n")
        except Exception as e:
            logger.error(f"写入审计日志失败: {e}")
    
    def log_login(
        self,
        user_id: str,
        username: str,
        ip_address: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> None:
        """记录登录事件"""
        self.log(AuditEvent(
            event_type=EventType.LOGIN if success else EventType.AUTH_FAILED,
            severity=Severity.INFO if success else Severity.WARNING,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            action="login",
            success=success,
            error_message=error_message,
        ))
    
    def log_api_call(
        self,
        user_id: Optional[str],
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[dict] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """记录 API 调用"""
        self.log(AuditEvent(
            event_type=EventType.READ,
            severity=Severity.INFO if success else Severity.ERROR,
            user_id=user_id,
            ip_address=ip_address,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            details=details or {},
            success=success,
            error_message=error_message,
        ))
    
    def log_tool_execution(
        self,
        user_id: Optional[str],
        tool_name: str,
        arguments: dict,
        success: bool,
        result: Optional[str] = None,
        error_message: Optional[str] = None,
        workspace_id: Optional[str] = None,
        dangerous: bool = False,
    ) -> None:
        """记录工具执行"""
        self.log(AuditEvent(
            event_type=EventType.DANGEROUS_OPERATION if dangerous else EventType.TOOL_EXECUTE,
            severity=Severity.WARNING if dangerous else (Severity.INFO if success else Severity.ERROR),
            user_id=user_id,
            resource_type="tool",
            resource_id=tool_name,
            action=f"execute:{tool_name}",
            details={
                "arguments": arguments,
                "result_preview": result[:200] if result else None,
                "dangerous": dangerous,
            },
            success=success,
            error_message=error_message,
            workspace_id=workspace_id,
        ))
    
    def log_chat(
        self,
        user_id: Optional[str],
        model: str,
        message_preview: str,
        tokens_used: int = 0,
        workspace_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> None:
        """记录聊天"""
        self.log(AuditEvent(
            event_type=EventType.CHAT,
            severity=Severity.INFO,
            user_id=user_id,
            action="chat",
            details={
                "model": model,
                "message_preview": message_preview[:100],
                "tokens_used": tokens_used,
            },
            workspace_id=workspace_id,
            conversation_id=conversation_id,
        ))
    
    def log_config_change(
        self,
        user_id: Optional[str],
        config_key: str,
        old_value: Any = None,
        new_value: Any = None,
    ) -> None:
        """记录配置变更"""
        self.log(AuditEvent(
            event_type=EventType.CONFIG_CHANGE,
            severity=Severity.WARNING,
            user_id=user_id,
            resource_type="config",
            resource_id=config_key,
            action="config_change",
            details={
                "key": config_key,
                "old_value": str(old_value)[:100] if old_value else None,
                "new_value": str(new_value)[:100] if new_value else None,
            },
        ))
    
    def log_error(
        self,
        error: Exception,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> None:
        """记录错误"""
        self.log(AuditEvent(
            event_type=EventType.ERROR,
            severity=Severity.ERROR,
            user_id=user_id,
            action=action or "error",
            details={
                **(details or {}),
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
            success=False,
            error_message=str(error),
        ))
    
    def query(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
        event_type: Optional[EventType] = None,
        limit: int = 100,
    ) -> list[dict]:
        """查询审计日志"""
        results = []
        
        # 确定要查询的日志文件
        if start_date and end_date:
            from datetime import timedelta
            current = start_date
            files = []
            while current <= end_date:
                date_str = current.strftime("%Y-%m-%d")
                log_file = self.log_dir / f"audit_{date_str}.jsonl"
                if log_file.exists():
                    files.append(log_file)
                current += timedelta(days=1)
        else:
            # 获取所有日志文件
            files = sorted(self.log_dir.glob("audit_*.jsonl"), reverse=True)
        
        for log_file in files:
            if len(results) >= limit:
                break
            
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if len(results) >= limit:
                            break
                        
                        try:
                            event = json.loads(line)
                            
                            # 过滤
                            if user_id and event.get("user_id") != user_id:
                                continue
                            if event_type and event.get("event_type") != event_type.value:
                                continue
                            
                            results.append(event)
                        except json.JSONDecodeError:
                            continue
            except Exception:
                continue
        
        return results
    
    def get_stats(
        self,
        days: int = 7,
    ) -> dict:
        """获取统计信息"""
        from datetime import timedelta
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        events = self.query(start_date=start_date, end_date=end_date, limit=10000)
        
        by_type = {}
        by_user = {}
        by_severity = {}
        errors = 0
        
        for event in events:
            # 按类型统计
            event_type = event.get("event_type", "unknown")
            by_type[event_type] = by_type.get(event_type, 0) + 1
            
            # 按用户统计
            user_id = event.get("user_id", "anonymous")
            by_user[user_id] = by_user.get(user_id, 0) + 1
            
            # 按严重级别统计
            severity = event.get("severity", "info")
            by_severity[severity] = by_severity.get(severity, 0) + 1
            
            # 错误统计
            if not event.get("success", True):
                errors += 1
        
        return {
            "total_events": len(events),
            "period_days": days,
            "errors": errors,
            "by_type": by_type,
            "by_user": dict(sorted(by_user.items(), key=lambda x: x[1], reverse=True)[:10]),
            "by_severity": by_severity,
        }
    
    def cleanup(self) -> int:
        """清理过期日志"""
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        deleted = 0
        
        for log_file in self.log_dir.glob("audit_*.jsonl"):
            try:
                # 从文件名解析日期
                date_str = log_file.stem.replace("audit_", "")
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                
                if file_date < cutoff_date:
                    log_file.unlink()
                    deleted += 1
            except Exception:
                continue
        
        return deleted


# 全局审计日志记录器
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """获取全局审计日志记录器"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
