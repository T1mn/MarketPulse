"""向量数据库"""
import logging
from typing import List, Dict, Optional, Any
import chromadb
from chromadb.config import Settings
from dataclasses import dataclass

from config import settings as app_settings
from .embeddings import embedding_model

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """文档数据结构"""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


class VectorStore:
    """
    向量数据库管理

    使用 ChromaDB 存储和检索文档
    """

    def __init__(
        self,
        collection_name: str = "market_pulse_knowledge",
        persist_directory: Optional[str] = None
    ):
        self.collection_name = collection_name
        self.persist_directory = persist_directory or str(app_settings.VECTOR_DB_PATH)

        self.client = None
        self.collection = None

        self._init_db()

    def _init_db(self):
        """初始化数据库"""
        try:
            # 创建 ChromaDB 客户端
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

            # 获取或创建集合
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "MarketPulse knowledge base"}
            )

            logger.info(f"✅ Vector store initialized: {self.collection_name}")
            logger.info(f"📊 Document count: {self.collection.count()}")

        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise

    def add_documents(
        self,
        documents: List[Document],
        batch_size: int = 100
    ) -> bool:
        """
        添加文档到向量数据库

        Args:
            documents: 文档列表
            batch_size: 批处理大小

        Returns:
            bool: 是否成功
        """
        try:
            # 分批处理
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]

                # 提取数据
                ids = [doc.id for doc in batch]
                contents = [doc.content for doc in batch]
                # 确保 metadata 非空（ChromaDB 要求）
                metadatas = [doc.metadata if doc.metadata else {"source": "unknown"} for doc in batch]

                # 生成嵌入（如果文档没有预生成）
                embeddings = []
                for doc in batch:
                    if doc.embedding:
                        embeddings.append(doc.embedding)
                    else:
                        embeddings.append(embedding_model.embed_text(doc.content))

                # 添加到集合
                self.collection.add(
                    ids=ids,
                    documents=contents,
                    metadatas=metadatas,
                    embeddings=embeddings
                )

            logger.info(f"✅ Added {len(documents)} documents to vector store")
            return True

        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            return False

    def search(
        self,
        query: str,
        top_k: int = 5,
        filter: Optional[Dict] = None
    ) -> List[Dict]:
        """
        搜索相似文档

        Args:
            query: 查询文本
            top_k: 返回结果数量
            filter: 元数据过滤条件

        Returns:
            List[Dict]: 搜索结果
        """
        try:
            # 生成查询嵌入
            query_embedding = embedding_model.embed_text(query)

            # 执行搜索
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter if filter else None
            )

            # 格式化结果
            documents = []
            if results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    doc = {
                        'id': results['ids'][0][i],
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else None,
                    }
                    documents.append(doc)

            logger.info(f"🔍 Search completed: {len(documents)} results found")
            return documents

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def delete_documents(self, ids: List[str]) -> bool:
        """删除文档"""
        try:
            self.collection.delete(ids=ids)
            logger.info(f"🗑️ Deleted {len(ids)} documents")
            return True
        except Exception as e:
            logger.error(f"Delete error: {e}")
            return False

    def update_document(self, document: Document) -> bool:
        """更新文档"""
        try:
            # ChromaDB 的 update 实际是 upsert
            embedding = document.embedding or embedding_model.embed_text(document.content)

            self.collection.update(
                ids=[document.id],
                documents=[document.content],
                metadatas=[document.metadata],
                embeddings=[embedding]
            )

            logger.info(f"✏️ Updated document: {document.id}")
            return True

        except Exception as e:
            logger.error(f"Update error: {e}")
            return False

    def get_document(self, doc_id: str) -> Optional[Dict]:
        """获取单个文档"""
        try:
            result = self.collection.get(ids=[doc_id])

            if result['ids']:
                return {
                    'id': result['ids'][0],
                    'content': result['documents'][0],
                    'metadata': result['metadatas'][0],
                }

            return None

        except Exception as e:
            logger.error(f"Get document error: {e}")
            return None

    def count(self) -> int:
        """获取文档总数"""
        return self.collection.count()

    def reset(self):
        """重置集合（清空所有数据）"""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "MarketPulse knowledge base"}
            )
            logger.warning(f"⚠️ Collection reset: {self.collection_name}")
        except Exception as e:
            logger.error(f"Reset error: {e}")


# 全局向量存储实例
vector_store = VectorStore()
