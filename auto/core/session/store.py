"""
会话存储

支持会话持久化到文件或数据库
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

from .manager import Session, SessionStatus, Message

logger = logging.getLogger(__name__)


class SessionStore:
    """
    会话存储
    
    将会话持久化到 JSON 文件
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        初始化存储
        
        Args:
            storage_path: 存储目录，默认为 ~/.ai-auto/sessions
        """
        if storage_path is None:
            storage_path = Path.home() / ".ai-auto" / "sessions"
        
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def save_session(self, session: Session) -> bool:
        """保存会话"""
        try:
            session_file = self.storage_path / f"{session.id}.json"
            
            data = {
                "id": session.id,
                "channel_type": session.channel_type,
                "channel_id": session.channel_id,
                "status": session.status.value,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "model": session.model,
                "system_prompt": session.system_prompt,
                "thinking_level": session.thinking_level,
                "workspace_id": session.workspace_id,
                "role_id": session.role_id,
                "metadata": session.metadata,
                "total_tokens": session.total_tokens,
                "input_tokens": session.input_tokens,
                "output_tokens": session.output_tokens,
                "messages": [m.to_dict() for m in session.messages],
            }
            
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"保存会话: {session.id}")
            return True
            
        except Exception as e:
            logger.error(f"保存会话失败: {e}")
            return False
    
    def load_session(self, session_id: str) -> Optional[Session]:
        """加载会话"""
        try:
            session_file = self.storage_path / f"{session_id}.json"
            
            if not session_file.exists():
                return None
            
            with open(session_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            session = Session(
                id=data["id"],
                channel_type=data["channel_type"],
                channel_id=data["channel_id"],
                status=SessionStatus(data["status"]),
                created_at=datetime.fromisoformat(data["created_at"]),
                updated_at=datetime.fromisoformat(data["updated_at"]),
                model=data.get("model"),
                system_prompt=data.get("system_prompt"),
                thinking_level=data.get("thinking_level", "medium"),
                workspace_id=data.get("workspace_id"),
                role_id=data.get("role_id"),
                metadata=data.get("metadata", {}),
                total_tokens=data.get("total_tokens", 0),
                input_tokens=data.get("input_tokens", 0),
                output_tokens=data.get("output_tokens", 0),
            )
            
            # 加载消息
            for msg_data in data.get("messages", []):
                session.messages.append(Message(
                    id=msg_data["id"],
                    role=msg_data["role"],
                    content=msg_data["content"],
                    timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                    metadata=msg_data.get("metadata", {}),
                ))
            
            logger.debug(f"加载会话: {session_id}")
            return session
            
        except Exception as e:
            logger.error(f"加载会话失败: {e}")
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        try:
            session_file = self.storage_path / f"{session_id}.json"
            
            if session_file.exists():
                session_file.unlink()
                logger.debug(f"删除会话文件: {session_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"删除会话文件失败: {e}")
            return False
    
    def list_sessions(self) -> List[str]:
        """列出所有保存的会话 ID"""
        sessions = []
        for file in self.storage_path.glob("*.json"):
            sessions.append(file.stem)
        return sessions
    
    def load_all_sessions(self) -> Dict[str, Session]:
        """加载所有会话"""
        sessions = {}
        for session_id in self.list_sessions():
            session = self.load_session(session_id)
            if session:
                sessions[session_id] = session
        return sessions
    
    def get_session_summary(self, session_id: str) -> Optional[dict]:
        """获取会话摘要（不加载完整消息）"""
        try:
            session_file = self.storage_path / f"{session_id}.json"
            
            if not session_file.exists():
                return None
            
            with open(session_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            return {
                "id": data["id"],
                "channel_type": data["channel_type"],
                "channel_id": data["channel_id"],
                "status": data["status"],
                "created_at": data["created_at"],
                "updated_at": data["updated_at"],
                "message_count": len(data.get("messages", [])),
                "total_tokens": data.get("total_tokens", 0),
            }
            
        except Exception as e:
            logger.error(f"获取会话摘要失败: {e}")
            return None
    
    def cleanup_old_sessions(self, days: int = 30) -> int:
        """
        清理旧会话
        
        Args:
            days: 保留天数
        
        Returns:
            删除的会话数量
        """
        deleted = 0
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        for session_id in self.list_sessions():
            session_file = self.storage_path / f"{session_id}.json"
            
            try:
                # 检查文件修改时间
                if session_file.stat().st_mtime < cutoff:
                    session_file.unlink()
                    deleted += 1
                    logger.info(f"清理旧会话: {session_id}")
            except Exception as e:
                logger.warning(f"清理会话失败 {session_id}: {e}")
        
        return deleted
    
    def get_storage_stats(self) -> dict:
        """获取存储统计"""
        sessions = self.list_sessions()
        total_size = 0
        
        for session_id in sessions:
            session_file = self.storage_path / f"{session_id}.json"
            if session_file.exists():
                total_size += session_file.stat().st_size
        
        return {
            "session_count": len(sessions),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "storage_path": str(self.storage_path),
        }
