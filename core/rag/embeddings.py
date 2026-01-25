"""嵌入模型"""
import logging
from typing import List, Optional
from sentence_transformers import SentenceTransformer
import numpy as np

from config import settings

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """
    嵌入模型管理

    支持多种嵌入模型：
    1. Sentence-Transformers（本地）
    2. OpenAI Embeddings（API）
    3. Google Embeddings（API）
    """

    def __init__(
        self,
        model_name: str = "moka-ai/m3e-base",
        use_local: bool = True
    ):
        self.model_name = model_name
        self.use_local = use_local
        self.model = None

        self._init_model()

    def _init_model(self):
        """初始化嵌入模型"""
        if self.use_local:
            try:
                logger.info(f"Loading local embedding model: {self.model_name}")
                self.model = SentenceTransformer(self.model_name)
                logger.info("✅ Embedding model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                # 降级到更小的模型
                try:
                    logger.info("Trying fallback model: all-MiniLM-L6-v2")
                    self.model = SentenceTransformer('all-MiniLM-L6-v2')
                    logger.info("✅ Fallback embedding model loaded")
                except Exception as e2:
                    logger.error(f"Fallback also failed: {e2}")
                    self.model = None

    def embed_text(self, text: str) -> List[float]:
        """
        为单个文本生成嵌入

        Args:
            text: 输入文本

        Returns:
            List[float]: 嵌入向量
        """
        if not self.model:
            raise ValueError("Embedding model not initialized")

        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            raise

    def embed_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        批量生成嵌入

        Args:
            texts: 文本列表
            batch_size: 批处理大小

        Returns:
            List[List[float]]: 嵌入向量列表
        """
        if not self.model:
            raise ValueError("Embedding model not initialized")

        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=len(texts) > 100
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Batch embedding error: {e}")
            raise

    def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        计算两个嵌入的余弦相似度

        Args:
            embedding1: 嵌入向量1
            embedding2: 嵌入向量2

        Returns:
            float: 相似度分数（0-1）
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # 余弦相似度
        cos_sim = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        return float(cos_sim)

    def get_dimension(self) -> int:
        """获取嵌入维度"""
        if self.model:
            return self.model.get_sentence_embedding_dimension()
        return 768  # 默认维度


# 全局嵌入模型实例
embedding_model = EmbeddingModel()
