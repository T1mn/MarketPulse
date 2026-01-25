"""LLM 缓存管理"""
import hashlib
import json
import time
from typing import Optional, Dict, Any
from collections import OrderedDict

from .base import LLMMessage, LLMResponse


class LLMCache:
    """
    LLM 响应缓存

    功能：
    1. 基于内容的缓存 key 生成
    2. TTL（Time To Live）过期管理
    3. LRU（Least Recently Used）淘汰策略
    4. 缓存统计
    """

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()

        # 统计信息
        self.hits = 0
        self.misses = 0

    def generate_key(
        self,
        messages: list[LLMMessage],
        temperature: float,
        max_tokens: int
    ) -> str:
        """
        生成缓存 key

        基于以下因素：
        - 消息内容
        - 温度参数
        - 最大 token 数
        """
        content = {
            "messages": [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        content_str = json.dumps(content, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(content_str.encode()).hexdigest()

    def get(self, key: str) -> Optional[LLMResponse]:
        """获取缓存"""
        if key in self.cache:
            entry = self.cache[key]

            # 检查是否过期
            if time.time() < entry["expire_at"]:
                # 命中，移到最后（LRU）
                self.cache.move_to_end(key)
                self.hits += 1
                return entry["response"]
            else:
                # 过期，删除
                del self.cache[key]

        self.misses += 1
        return None

    def set(self, key: str, response: LLMResponse, ttl: int = 3600):
        """设置缓存"""
        # 检查大小限制
        if len(self.cache) >= self.max_size:
            # LRU: 删除最早的项
            self.cache.popitem(last=False)

        self.cache[key] = {
            "response": response,
            "expire_at": time.time() + ttl,
            "created_at": time.time(),
        }

    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

    def get_stats(self) -> Dict:
        """获取缓存统计"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.2f}%",
        }
