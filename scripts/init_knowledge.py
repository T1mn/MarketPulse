"""知识库初始化脚本"""
import asyncio
import logging
from pathlib import Path

from core.rag.document_loader import DocumentLoader
from core.rag.retriever import retriever

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_knowledge_base():
    """初始化知识库"""

    logger.info("🚀 Starting knowledge base initialization...")

    # 知识库目录
    kb_dir = Path(__file__).parent.parent / "data" / "knowledge_base"

    # 加载所有知识
    logger.info(f"📚 Loading knowledge from: {kb_dir}")

    documents = DocumentLoader.load_directory(
        directory=str(kb_dir),
        file_types=['.json', '.md'],
        recursive=True
    )

    if not documents:
        logger.warning("⚠️  No documents found!")
        return

    logger.info(f"📄 Found {len(documents)} documents")

    # 批量添加到向量数据库
    count = await retriever.batch_add_knowledge(documents)

    logger.info(f"✅ Successfully added {count} documents to knowledge base")

    # 测试检索
    logger.info("🔍 Testing retrieval...")

    test_queries = [
        "如何充值？",
        "交易手续费是多少？",
        "怎么设置止损？",
    ]

    for query in test_queries:
        results = await retriever.retrieve(query, top_k=3)
        logger.info(f"Query: {query}")
        logger.info(f"Results: {len(results)} documents found")
        if results:
            logger.info(f"Top result score: {results[0].score:.3f}")
        logger.info("---")

    logger.info("🎉 Knowledge base initialization completed!")


if __name__ == "__main__":
    asyncio.run(init_knowledge_base())
