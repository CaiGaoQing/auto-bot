"""知识库技能"""

from pathlib import Path
from typing import Optional

from auto.core.skill.base import Skill, ToolDefinition
from auto.core.tool.context import ToolContext
from auto.core.tool.result import ToolResult


class KnowledgeSkill(Skill):
    """知识库技能
    
    提供知识库管理、文档索引、语义检索等功能。
    """
    
    @property
    def name(self) -> str:
        return "knowledge"
    
    @property
    def display_name(self) -> str:
        return "知识库"
    
    @property
    def description(self) -> str:
        return "知识库管理、文档索引、语义检索、RAG 增强"
    
    @property
    def category(self) -> str:
        return "productivity"
    
    @property
    def tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="index_document",
                description="将文档添加到知识库",
                parameters={
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "文档内容",
                        },
                        "source": {
                            "type": "string",
                            "description": "来源标识",
                        },
                        "collection": {
                            "type": "string",
                            "description": "集合名称",
                            "default": "default",
                        },
                    },
                    "required": ["content", "source"],
                },
                handler=self.index_document,
            ),
            ToolDefinition(
                name="index_file",
                description="将文件添加到知识库",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "文件路径 (支持 txt, md, pdf, docx)",
                        },
                        "collection": {
                            "type": "string",
                            "description": "集合名称",
                            "default": "default",
                        },
                    },
                    "required": ["file_path"],
                },
                handler=self.index_file,
            ),
            ToolDefinition(
                name="index_directory",
                description="将目录下的所有文件添加到知识库",
                parameters={
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "目录路径",
                        },
                        "pattern": {
                            "type": "string",
                            "description": "文件匹配模式",
                            "default": "*.md",
                        },
                        "collection": {
                            "type": "string",
                            "description": "集合名称",
                            "default": "default",
                        },
                        "recursive": {
                            "type": "boolean",
                            "description": "是否递归子目录",
                            "default": True,
                        },
                    },
                    "required": ["directory"],
                },
                handler=self.index_directory,
            ),
            ToolDefinition(
                name="search",
                description="在知识库中搜索相关内容",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索查询",
                        },
                        "collection": {
                            "type": "string",
                            "description": "集合名称",
                            "default": "default",
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "返回数量",
                            "default": 5,
                        },
                    },
                    "required": ["query"],
                },
                handler=self.search,
            ),
            ToolDefinition(
                name="list_collections",
                description="列出知识库集合",
                parameters={
                    "type": "object",
                    "properties": {},
                },
                handler=self.list_collections,
            ),
            ToolDefinition(
                name="get_stats",
                description="获取知识库统计信息",
                parameters={
                    "type": "object",
                    "properties": {
                        "collection": {
                            "type": "string",
                            "description": "集合名称",
                            "default": "default",
                        },
                    },
                },
                handler=self.get_stats,
            ),
            ToolDefinition(
                name="delete_source",
                description="删除指定来源的文档",
                parameters={
                    "type": "object",
                    "properties": {
                        "source": {
                            "type": "string",
                            "description": "来源标识",
                        },
                        "collection": {
                            "type": "string",
                            "description": "集合名称",
                            "default": "default",
                        },
                    },
                    "required": ["source"],
                },
                dangerous=True,
                requires_confirmation=True,
                handler=self.delete_source,
            ),
            ToolDefinition(
                name="delete_collection",
                description="删除整个集合",
                parameters={
                    "type": "object",
                    "properties": {
                        "collection": {
                            "type": "string",
                            "description": "集合名称",
                        },
                    },
                    "required": ["collection"],
                },
                dangerous=True,
                requires_confirmation=True,
                handler=self.delete_collection,
            ),
        ]
    
    @property
    def system_prompt(self) -> str:
        return """你是一个知识库管理助手，可以帮助用户：
- 将文档和文件添加到知识库
- 在知识库中搜索相关信息
- 管理知识库集合

使用知识库可以让 AI 具备企业特定知识，提供更准确的回答。"""
    
    async def index_document(
        self,
        ctx: ToolContext,
        content: str,
        source: str,
        collection: str = "default",
    ) -> ToolResult:
        """索引文档"""
        try:
            from auto.core.knowledge.rag import get_rag_engine
            
            engine = get_rag_engine()
            ids = await engine.index_document(
                content=content,
                source=source,
                collection=collection,
            )
            
            return ToolResult.success_result(
                data={
                    "source": source,
                    "collection": collection,
                    "chunks": len(ids),
                    "chunk_ids": ids[:5],  # 只返回前5个 ID
                },
                message=f"已索引文档 '{source}'，生成 {len(ids)} 个文档块",
            )
        except ImportError as e:
            return ToolResult.error_result(str(e))
        except Exception as e:
            return ToolResult.error_result(f"索引失败: {str(e)}")
    
    async def index_file(
        self,
        ctx: ToolContext,
        file_path: str,
        collection: str = "default",
    ) -> ToolResult:
        """索引文件"""
        path = Path(file_path).expanduser()
        
        if not ctx.security.is_allowed_path(path):
            return ToolResult.error_result(f"路径不允许: {file_path}")
        
        if not path.exists():
            return ToolResult.error_result(f"文件不存在: {file_path}")
        
        try:
            from auto.core.knowledge.rag import get_rag_engine
            
            engine = get_rag_engine()
            ids = await engine.index_file(
                file_path=path,
                collection=collection,
            )
            
            return ToolResult.success_result(
                data={
                    "file": str(path),
                    "collection": collection,
                    "chunks": len(ids),
                },
                message=f"已索引文件 '{path.name}'，生成 {len(ids)} 个文档块",
            )
        except ImportError as e:
            return ToolResult.error_result(str(e))
        except Exception as e:
            return ToolResult.error_result(f"索引失败: {str(e)}")
    
    async def index_directory(
        self,
        ctx: ToolContext,
        directory: str,
        pattern: str = "*.md",
        collection: str = "default",
        recursive: bool = True,
    ) -> ToolResult:
        """索引目录"""
        dir_path = Path(directory).expanduser()
        
        if not ctx.security.is_allowed_path(dir_path):
            return ToolResult.error_result(f"路径不允许: {directory}")
        
        if not dir_path.exists():
            return ToolResult.error_result(f"目录不存在: {directory}")
        
        try:
            from auto.core.knowledge.rag import get_rag_engine
            
            engine = get_rag_engine()
            
            # 查找匹配的文件
            if recursive:
                files = list(dir_path.rglob(pattern))
            else:
                files = list(dir_path.glob(pattern))
            
            if not files:
                return ToolResult.success_result(
                    data={"files": 0},
                    message=f"未找到匹配 '{pattern}' 的文件",
                )
            
            # 索引文件
            results = []
            errors = []
            
            for file_path in files:
                try:
                    ids = await engine.index_file(
                        file_path=file_path,
                        collection=collection,
                    )
                    results.append({
                        "file": str(file_path),
                        "chunks": len(ids),
                    })
                except Exception as e:
                    errors.append({
                        "file": str(file_path),
                        "error": str(e),
                    })
            
            total_chunks = sum(r["chunks"] for r in results)
            
            return ToolResult.success_result(
                data={
                    "directory": str(dir_path),
                    "collection": collection,
                    "files_indexed": len(results),
                    "files_failed": len(errors),
                    "total_chunks": total_chunks,
                    "errors": errors[:5] if errors else None,
                },
                message=f"已索引 {len(results)} 个文件，共 {total_chunks} 个文档块",
            )
        except ImportError as e:
            return ToolResult.error_result(str(e))
        except Exception as e:
            return ToolResult.error_result(f"索引失败: {str(e)}")
    
    async def search(
        self,
        ctx: ToolContext,
        query: str,
        collection: str = "default",
        top_k: int = 5,
    ) -> ToolResult:
        """搜索知识库"""
        try:
            from auto.core.knowledge.rag import get_rag_engine
            
            engine = get_rag_engine()
            rag_context = await engine.search(
                query=query,
                collection=collection,
                top_k=top_k,
            )
            
            if not rag_context.documents:
                return ToolResult.success_result(
                    data={"results": []},
                    message="未找到相关内容",
                )
            
            results = []
            for doc, score in zip(rag_context.documents, rag_context.scores):
                results.append({
                    "content": doc.content[:500] + ("..." if len(doc.content) > 500 else ""),
                    "source": doc.metadata.get("source", "unknown"),
                    "score": round(score, 4),
                })
            
            return ToolResult.success_result(
                data={
                    "query": query,
                    "collection": collection,
                    "results": results,
                },
                message=f"找到 {len(results)} 条相关结果",
            )
        except ImportError as e:
            return ToolResult.error_result(str(e))
        except Exception as e:
            return ToolResult.error_result(f"搜索失败: {str(e)}")
    
    async def list_collections(self, ctx: ToolContext) -> ToolResult:
        """列出集合"""
        try:
            from auto.core.knowledge.vector_store import get_vector_store
            
            store = get_vector_store()
            collections = await store.list_collections()
            
            return ToolResult.success_result(
                data={"collections": collections},
                message=f"共 {len(collections)} 个集合",
            )
        except ImportError as e:
            return ToolResult.error_result(str(e))
        except Exception as e:
            return ToolResult.error_result(f"获取集合失败: {str(e)}")
    
    async def get_stats(
        self,
        ctx: ToolContext,
        collection: str = "default",
    ) -> ToolResult:
        """获取统计信息"""
        try:
            from auto.core.knowledge.rag import get_rag_engine
            
            engine = get_rag_engine()
            stats = await engine.get_stats(collection)
            
            return ToolResult.success_result(
                data=stats,
                message=f"集合 '{collection}' 共 {stats['document_count']} 个文档块",
            )
        except ImportError as e:
            return ToolResult.error_result(str(e))
        except Exception as e:
            return ToolResult.error_result(f"获取统计失败: {str(e)}")
    
    async def delete_source(
        self,
        ctx: ToolContext,
        source: str,
        collection: str = "default",
    ) -> ToolResult:
        """删除来源"""
        try:
            from auto.core.knowledge.rag import get_rag_engine
            
            engine = get_rag_engine()
            count = await engine.delete_by_source(source, collection)
            
            return ToolResult.success_result(
                data={"source": source, "deleted": count},
                message=f"已删除来源 '{source}' 的 {count} 个文档块",
            )
        except ImportError as e:
            return ToolResult.error_result(str(e))
        except Exception as e:
            return ToolResult.error_result(f"删除失败: {str(e)}")
    
    async def delete_collection(
        self,
        ctx: ToolContext,
        collection: str,
    ) -> ToolResult:
        """删除集合"""
        try:
            from auto.core.knowledge.vector_store import get_vector_store
            
            store = get_vector_store()
            success = await store.delete_collection(collection)
            
            if success:
                return ToolResult.success_result(
                    message=f"已删除集合 '{collection}'",
                )
            else:
                return ToolResult.error_result(f"删除集合 '{collection}' 失败")
        except ImportError as e:
            return ToolResult.error_result(str(e))
        except Exception as e:
            return ToolResult.error_result(f"删除失败: {str(e)}")
