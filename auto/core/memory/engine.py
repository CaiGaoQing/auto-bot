"""记忆引擎"""

import logging
from datetime import datetime
from typing import Any, Optional
from pathlib import Path

from auto.shared.models import Memory
from auto.shared.utils import generate_id

logger = logging.getLogger(__name__)


class MemoryEngine:
    """记忆引擎
    
    负责:
    - 管理工作空间记忆
    - 记忆存储和检索
    - 记忆生命周期管理
    - 语义搜索 (可选)
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        self._memories: dict[str, list[Memory]] = {}  # workspace_id -> memories
        self._storage_path = storage_path
        self._vector_store = None
        self._embeddings_cache: dict[str, list[float]] = {}
        self._use_vector_search = False
        
        # 尝试初始化向量存储
        self._init_vector_store()
    
    def _init_vector_store(self) -> None:
        """初始化向量存储"""
        try:
            from auto.core.knowledge.vector_store import ChromaVectorStore
            from auto.shared.config import DEFAULT_CONFIG_DIR
            
            self._vector_store = ChromaVectorStore(
                persist_directory=str(DEFAULT_CONFIG_DIR / "memory_vectors"),
                collection_name="memories",
            )
            self._use_vector_search = True
            logger.info("记忆向量存储初始化成功")
        except ImportError:
            logger.warning("ChromaDB 未安装，使用关键词检索")
        except Exception as e:
            logger.warning(f"向量存储初始化失败: {e}")
    
    async def _get_embedding(self, text: str) -> Optional[list[float]]:
        """获取文本的向量嵌入"""
        # 检查缓存
        if text in self._embeddings_cache:
            return self._embeddings_cache[text]
        
        try:
            import openai
            from auto.shared.config import get_config_manager
            
            config = get_config_manager()
            api_key = None
            
            # 获取 OpenAI API Key
            for provider in config.config.providers:
                if provider.name == "openai" and provider.api_key:
                    api_key = provider.api_key
                    break
            
            if not api_key:
                return None
            
            client = openai.OpenAI(api_key=api_key)
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=text,
            )
            
            embedding = response.data[0].embedding
            self._embeddings_cache[text] = embedding
            return embedding
            
        except Exception as e:
            logger.warning(f"获取嵌入失败: {e}")
            return None
    
    def add_memory(
        self,
        workspace_id: str,
        content: str,
        memory_type: str = "preference",
        source_type: str = "user",
        importance: int = 50,
        is_pinned: bool = False,
    ) -> Memory:
        """添加记忆
        
        Args:
            workspace_id: 工作空间 ID
            content: 记忆内容
            memory_type: 记忆类型 (preference, rule, knowledge, context, summary)
            source_type: 来源类型 (user, auto, conversation)
            importance: 重要性 (0-100)
            is_pinned: 是否置顶
        
        Returns:
            Memory: 创建的记忆
        """
        memory = Memory(
            id=generate_id("mem"),
            workspace_id=workspace_id,
            content=content,
            memory_type=memory_type,
            source_type=source_type,
            importance=importance,
            is_pinned=is_pinned,
        )
        
        if workspace_id not in self._memories:
            self._memories[workspace_id] = []
        
        self._memories[workspace_id].append(memory)
        
        return memory
    
    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """获取记忆"""
        for memories in self._memories.values():
            for memory in memories:
                if memory.id == memory_id:
                    return memory
        return None
    
    def list_memories(
        self,
        workspace_id: str,
        memory_type: Optional[str] = None,
        is_pinned: Optional[bool] = None,
        limit: int = 100,
    ) -> list[Memory]:
        """列出记忆
        
        Args:
            workspace_id: 工作空间 ID
            memory_type: 按类型筛选
            is_pinned: 按置顶筛选
            limit: 返回数量限制
        
        Returns:
            list[Memory]: 记忆列表
        """
        memories = self._memories.get(workspace_id, [])
        
        if memory_type:
            memories = [m for m in memories if m.memory_type == memory_type]
        
        if is_pinned is not None:
            memories = [m for m in memories if m.is_pinned == is_pinned]
        
        # 排序：置顶优先，然后按重要性和访问次数
        memories.sort(
            key=lambda m: (
                not m.is_pinned,
                -m.importance,
                -m.access_count,
            )
        )
        
        return memories[:limit]
    
    def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        importance: Optional[int] = None,
        is_pinned: Optional[bool] = None,
    ) -> Optional[Memory]:
        """更新记忆"""
        memory = self.get_memory(memory_id)
        if not memory:
            return None
        
        if content is not None:
            memory.content = content
        if importance is not None:
            memory.importance = importance
        if is_pinned is not None:
            memory.is_pinned = is_pinned
        
        memory.updated_at = datetime.now()
        
        return memory
    
    def delete_memory(self, memory_id: str) -> bool:
        """删除记忆"""
        for workspace_id, memories in self._memories.items():
            for i, memory in enumerate(memories):
                if memory.id == memory_id:
                    del memories[i]
                    return True
        return False
    
    def access_memory(self, memory_id: str) -> None:
        """访问记忆 (增加访问计数)"""
        memory = self.get_memory(memory_id)
        if memory:
            memory.access_count += 1
    
    def search_memories(
        self,
        workspace_id: str,
        query: str,
        limit: int = 5,
        use_vector: bool = True,
    ) -> list[tuple[Memory, float]]:
        """搜索记忆 (支持语义检索)
        
        Args:
            workspace_id: 工作空间 ID
            query: 搜索查询
            limit: 返回数量
            use_vector: 是否使用向量检索
        
        Returns:
            list[tuple[Memory, float]]: (记忆, 相关度分数) 列表
        """
        memories = self._memories.get(workspace_id, [])
        
        if not memories:
            return []
        
        # 尝试使用向量检索
        if use_vector and self._use_vector_search and self._vector_store:
            try:
                vector_results = self._vector_search(workspace_id, query, limit)
                if vector_results:
                    return vector_results
            except Exception as e:
                logger.warning(f"向量检索失败，回退到关键词检索: {e}")
        
        # 回退到关键词匹配
        return self._keyword_search(memories, query, limit)
    
    def _keyword_search(
        self,
        memories: list[Memory],
        query: str,
        limit: int,
    ) -> list[tuple[Memory, float]]:
        """关键词搜索"""
        query_lower = query.lower()
        results = []
        
        for memory in memories:
            content_lower = memory.content.lower()
            
            # 计算简单相关度
            if query_lower in content_lower:
                score = 0.9
            else:
                query_words = set(query_lower.split())
                content_words = set(content_lower.split())
                common = query_words & content_words
                if common:
                    score = len(common) / len(query_words) * 0.8
                else:
                    score = 0
            
            if score > 0:
                results.append((memory, score))
        
        results.sort(key=lambda x: -x[1])
        return results[:limit]
    
    def _vector_search(
        self,
        workspace_id: str,
        query: str,
        limit: int,
    ) -> list[tuple[Memory, float]]:
        """向量语义检索"""
        if not self._vector_store:
            return []
        
        # 使用向量存储检索
        results = self._vector_store.search(
            query=query,
            top_k=limit,
            filter_metadata={"workspace_id": workspace_id},
        )
        
        # 映射回 Memory 对象
        memory_results = []
        memories = self._memories.get(workspace_id, [])
        memory_map = {m.id: m for m in memories}
        
        for doc_id, score in results:
            if doc_id in memory_map:
                memory_results.append((memory_map[doc_id], score))
        
        return memory_results
    
    async def index_memory(self, memory: Memory) -> bool:
        """将记忆索引到向量存储"""
        if not self._use_vector_search or not self._vector_store:
            return False
        
        try:
            self._vector_store.add_documents(
                documents=[memory.content],
                metadatas=[{
                    "memory_id": memory.id,
                    "workspace_id": memory.workspace_id,
                    "memory_type": memory.memory_type,
                }],
                ids=[memory.id],
            )
            return True
        except Exception as e:
            logger.warning(f"索引记忆失败: {e}")
            return False
    
    def get_context_memories(
        self,
        workspace_id: str,
        current_message: str,
        limit: int = 5,
    ) -> list[Memory]:
        """获取上下文相关的记忆
        
        用于注入到对话上下文中。
        
        Args:
            workspace_id: 工作空间 ID
            current_message: 当前消息
            limit: 返回数量
        
        Returns:
            list[Memory]: 相关记忆列表
        """
        # 1. 获取置顶记忆
        pinned = self.list_memories(workspace_id, is_pinned=True, limit=3)
        
        # 2. 搜索相关记忆
        search_results = self.search_memories(workspace_id, current_message, limit=limit)
        relevant = [m for m, _ in search_results if m not in pinned]
        
        # 3. 合并并限制数量
        result = pinned + relevant[:limit - len(pinned)]
        
        # 增加访问计数
        for memory in result:
            self.access_memory(memory.id)
        
        return result
    
    def format_memories_for_prompt(self, memories: list[Memory]) -> str:
        """格式化记忆为提示词"""
        if not memories:
            return ""
        
        lines = ["## 工作空间记忆\n"]
        
        for memory in memories:
            prefix = "📌 " if memory.is_pinned else "• "
            lines.append(f"{prefix}{memory.content}")
        
        return "\n".join(lines)
    
    async def extract_memories_from_conversation(
        self,
        workspace_id: str,
        messages: list[Any],
    ) -> list[Memory]:
        """从对话中自动提取记忆
        
        使用 AI 提取关键信息，如用户偏好、重要决策等。
        """
        if not messages or len(messages) < 2:
            return []
        
        # 构建对话文本
        conversation_text = ""
        for msg in messages[-10:]:  # 只看最近 10 条
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if isinstance(content, str) and content:
                conversation_text += f"{role}: {content}\n"
        
        if len(conversation_text) < 50:
            return []
        
        # 使用 AI 提取记忆
        try:
            from auto.core.ai.router import get_router
            
            ai_router = get_router()
            
            extraction_prompt = f"""分析以下对话，提取值得记住的关键信息。

关注以下类型的信息：
1. 用户偏好 (如编程语言偏好、工作习惯)
2. 重要决策 (如技术选型、方案确定)
3. 关键知识 (如项目背景、业务规则)
4. 待办事项 (如下一步计划)

对话内容：
{conversation_text}

请以 JSON 数组格式返回，每条记忆包含 type 和 content 字段：
[{{"type": "preference", "content": "记忆内容"}}]

如果没有值得记住的信息，返回空数组 []"""
            
            response = await ai_router.chat(
                messages=[{"role": "user", "content": extraction_prompt}],
                model="gpt-4o-mini",  # 使用较便宜的模型
            )
            
            # 解析响应
            import json
            import re
            
            response_text = response.get("content", "")
            
            # 提取 JSON 部分
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if not json_match:
                return []
            
            extracted = json.loads(json_match.group())
            
            if not isinstance(extracted, list):
                return []
            
            # 创建记忆
            memories = []
            for item in extracted[:5]:  # 最多 5 条
                if isinstance(item, dict) and "content" in item:
                    memory = self.add_memory(
                        workspace_id=workspace_id,
                        content=item["content"],
                        memory_type=item.get("type", "knowledge"),
                        source_type="auto",
                        importance=60,
                    )
                    memories.append(memory)
                    
                    # 索引到向量存储
                    await self.index_memory(memory)
            
            return memories
            
        except Exception as e:
            logger.warning(f"提取记忆失败: {e}")
            return []
    
    def clear_workspace_memories(self, workspace_id: str) -> int:
        """清空工作空间记忆"""
        if workspace_id in self._memories:
            count = len(self._memories[workspace_id])
            del self._memories[workspace_id]
            return count
        return 0


# 全局引擎实例
_engine: Optional[MemoryEngine] = None


def get_memory_engine() -> MemoryEngine:
    """获取全局记忆引擎"""
    global _engine
    if _engine is None:
        _engine = MemoryEngine()
    return _engine
