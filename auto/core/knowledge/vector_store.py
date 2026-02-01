"""向量存储"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
import hashlib


@dataclass
class Document:
    """文档"""
    id: str
    content: str
    metadata: dict
    embedding: Optional[list[float]] = None


@dataclass
class SearchResult:
    """搜索结果"""
    document: Document
    score: float
    distance: float


class VectorStore(ABC):
    """向量存储抽象基类"""
    
    @abstractmethod
    async def add_documents(
        self,
        documents: list[Document],
        collection: str = "default",
    ) -> list[str]:
        """添加文档"""
        pass
    
    @abstractmethod
    async def search(
        self,
        query: str,
        collection: str = "default",
        top_k: int = 5,
        filter: Optional[dict] = None,
    ) -> list[SearchResult]:
        """搜索相似文档"""
        pass
    
    @abstractmethod
    async def delete(
        self,
        ids: list[str],
        collection: str = "default",
    ) -> int:
        """删除文档"""
        pass
    
    @abstractmethod
    async def get(
        self,
        ids: list[str],
        collection: str = "default",
    ) -> list[Document]:
        """获取文档"""
        pass
    
    @abstractmethod
    async def list_collections(self) -> list[str]:
        """列出集合"""
        pass
    
    @abstractmethod
    async def delete_collection(self, collection: str) -> bool:
        """删除集合"""
        pass


class ChromaVectorStore(VectorStore):
    """ChromaDB 向量存储"""
    
    def __init__(
        self,
        persist_directory: Optional[Path] = None,
        embedding_function: Optional[Any] = None,
    ):
        self._persist_directory = persist_directory
        self._embedding_function = embedding_function
        self._client = None
        self._collections: dict[str, Any] = {}
    
    def _ensure_client(self):
        """确保客户端已初始化"""
        if self._client is None:
            try:
                import chromadb
                from chromadb.config import Settings
            except ImportError:
                raise ImportError("需要安装 chromadb: pip install chromadb")
            
            if self._persist_directory:
                self._persist_directory.mkdir(parents=True, exist_ok=True)
                self._client = chromadb.PersistentClient(
                    path=str(self._persist_directory),
                    settings=Settings(anonymized_telemetry=False),
                )
            else:
                self._client = chromadb.Client(
                    settings=Settings(anonymized_telemetry=False),
                )
        
        return self._client
    
    def _get_collection(self, name: str):
        """获取或创建集合"""
        if name not in self._collections:
            client = self._ensure_client()
            
            # 使用默认嵌入函数或自定义
            if self._embedding_function:
                self._collections[name] = client.get_or_create_collection(
                    name=name,
                    embedding_function=self._embedding_function,
                )
            else:
                self._collections[name] = client.get_or_create_collection(name=name)
        
        return self._collections[name]
    
    async def add_documents(
        self,
        documents: list[Document],
        collection: str = "default",
    ) -> list[str]:
        """添加文档"""
        coll = self._get_collection(collection)
        
        ids = []
        contents = []
        metadatas = []
        embeddings = []
        
        for doc in documents:
            doc_id = doc.id or hashlib.md5(doc.content.encode()).hexdigest()
            ids.append(doc_id)
            contents.append(doc.content)
            metadatas.append(doc.metadata or {})
            
            if doc.embedding:
                embeddings.append(doc.embedding)
        
        # 添加到集合
        if embeddings:
            coll.add(
                ids=ids,
                documents=contents,
                metadatas=metadatas,
                embeddings=embeddings,
            )
        else:
            coll.add(
                ids=ids,
                documents=contents,
                metadatas=metadatas,
            )
        
        return ids
    
    async def search(
        self,
        query: str,
        collection: str = "default",
        top_k: int = 5,
        filter: Optional[dict] = None,
    ) -> list[SearchResult]:
        """搜索相似文档"""
        coll = self._get_collection(collection)
        
        results = coll.query(
            query_texts=[query],
            n_results=top_k,
            where=filter,
            include=["documents", "metadatas", "distances"],
        )
        
        search_results = []
        
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                doc = Document(
                    id=doc_id,
                    content=results["documents"][0][i] if results["documents"] else "",
                    metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                )
                
                distance = results["distances"][0][i] if results["distances"] else 0
                # 将距离转换为相似度分数 (0-1)
                score = 1 / (1 + distance)
                
                search_results.append(SearchResult(
                    document=doc,
                    score=score,
                    distance=distance,
                ))
        
        return search_results
    
    async def delete(
        self,
        ids: list[str],
        collection: str = "default",
    ) -> int:
        """删除文档"""
        coll = self._get_collection(collection)
        coll.delete(ids=ids)
        return len(ids)
    
    async def get(
        self,
        ids: list[str],
        collection: str = "default",
    ) -> list[Document]:
        """获取文档"""
        coll = self._get_collection(collection)
        
        results = coll.get(
            ids=ids,
            include=["documents", "metadatas"],
        )
        
        documents = []
        
        if results["ids"]:
            for i, doc_id in enumerate(results["ids"]):
                documents.append(Document(
                    id=doc_id,
                    content=results["documents"][i] if results["documents"] else "",
                    metadata=results["metadatas"][i] if results["metadatas"] else {},
                ))
        
        return documents
    
    async def list_collections(self) -> list[str]:
        """列出集合"""
        client = self._ensure_client()
        collections = client.list_collections()
        return [c.name for c in collections]
    
    async def delete_collection(self, collection: str) -> bool:
        """删除集合"""
        try:
            client = self._ensure_client()
            client.delete_collection(collection)
            
            if collection in self._collections:
                del self._collections[collection]
            
            return True
        except Exception:
            return False
    
    async def count(self, collection: str = "default") -> int:
        """获取文档数量"""
        coll = self._get_collection(collection)
        return coll.count()


# 全局向量存储实例
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """获取全局向量存储"""
    global _vector_store
    if _vector_store is None:
        from auto.shared.config import DEFAULT_CONFIG_DIR
        persist_dir = DEFAULT_CONFIG_DIR / "vector_db"
        _vector_store = ChromaVectorStore(persist_directory=persist_dir)
    return _vector_store
