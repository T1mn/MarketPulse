"""RAG 检索器"""
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from .vector_store import VectorStore, vector_store, Document
from .embeddings import embedding_model
from config import chatbot_config

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """检索结果"""
    content: str
    metadata: Dict[str, Any]
    score: float  # 相似度分数
    source: str


class RAGRetriever:
    """
    RAG 检索器

    功能：
    1. 向量检索
    2. 关键词检索（TODO）
    3. 混合检索（TODO）
    4. 重排序（TODO）
    """

    def __init__(
        self,
        vector_store: VectorStore = None,
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ):
        self.vector_store = vector_store or globals()['vector_store']
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold

    async def retrieve(
        self,
        query: str,
        filters: Optional[Dict] = None,
        top_k: Optional[int] = None
    ) -> List[RetrievalResult]:
        """
        检索相关文档

        Args:
            query: 查询文本
            filters: 元数据过滤条件
            top_k: 返回结果数量

        Returns:
            List[RetrievalResult]: 检索结果
        """
        k = top_k or self.top_k

        # 1. 向量检索
        docs = self.vector_store.search(
            query=query,
            top_k=k * 2,  # 多检索一些，用于后续过滤
            filter=filters
        )

        # 2. 过滤低相似度结果
        results = []
        for doc in docs:
            # 计算相似度分数（距离转换为相似度）
            # ChromaDB 使用 L2 距离，转换为相似度
            distance = doc.get('distance', 0)
            similarity = 1 / (1 + distance)  # 简单转换

            if similarity >= self.similarity_threshold:
                result = RetrievalResult(
                    content=doc['content'],
                    metadata=doc.get('metadata', {}),
                    score=similarity,
                    source=doc.get('metadata', {}).get('source', 'unknown')
                )
                results.append(result)

        # 3. 按相似度排序并限制数量
        results.sort(key=lambda x: x.score, reverse=True)
        results = results[:k]

        logger.info(f"🔍 Retrieved {len(results)} documents (threshold={self.similarity_threshold})")

        return results

    async def build_context(
        self,
        query: str,
        intent: str,
        max_length: int = 2000
    ) -> str:
        """
        构建 RAG 上下文

        Args:
            query: 用户查询
            intent: 意图
            max_length: 最大上下文长度（字符）

        Returns:
            str: 格式化的上下文
        """
        # 根据意图设置过滤条件
        filters = self._get_filters_by_intent(intent)

        # 检索文档
        results = await self.retrieve(query, filters=filters)

        if not results:
            return ""

        # 构建上下文
        context_parts = []
        current_length = 0

        for i, result in enumerate(results, 1):
            # 格式化单个文档
            doc_text = f"【文档 {i}】\n来源：{result.source}\n内容：{result.content}\n"

            # 检查长度限制
            if current_length + len(doc_text) > max_length:
                break

            context_parts.append(doc_text)
            current_length += len(doc_text)

        context = "\n".join(context_parts)

        logger.info(f"📝 Built context: {len(context)} chars from {len(context_parts)} docs")

        return context

    def _get_filters_by_intent(self, intent: str) -> Optional[Dict]:
        """根据意图获取过滤条件"""
        # 不同意图可能需要不同类型的知识
        intent_filters = {
            "market_query": {"category": "market_data"},
            "news_analysis": {"category": "news"},
            "customer_service": {"category": "faq"},
            "trading": {"category": "trading_rules"},
        }

        return intent_filters.get(intent)

    async def add_knowledge(
        self,
        content: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        添加知识到知识库

        Args:
            content: 文档内容
            metadata: 元数据（category, source, title等）

        Returns:
            bool: 是否成功
        """
        # 生成文档 ID
        import hashlib
        doc_id = hashlib.md5(content.encode()).hexdigest()

        # 创建文档
        doc = Document(
            id=doc_id,
            content=content,
            metadata=metadata
        )

        # 添加到向量数据库
        success = self.vector_store.add_documents([doc])

        if success:
            logger.info(f"✅ Added knowledge: {metadata.get('title', doc_id)}")

        return success

    async def batch_add_knowledge(
        self,
        documents: List[Dict[str, Any]]
    ) -> int:
        """
        批量添加知识

        Args:
            documents: 文档列表，每个包含 content 和 metadata

        Returns:
            int: 成功添加的数量
        """
        docs = []
        for doc_data in documents:
            import hashlib
            content = doc_data['content']
            metadata = doc_data.get('metadata', {})

            doc_id = hashlib.md5(content.encode()).hexdigest()

            doc = Document(
                id=doc_id,
                content=content,
                metadata=metadata
            )
            docs.append(doc)

        success = self.vector_store.add_documents(docs)

        if success:
            logger.info(f"✅ Batch added {len(docs)} documents")
            return len(docs)

        return 0


# 全局检索器实例
retriever = RAGRetriever()
