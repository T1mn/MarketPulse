"""NLU 引擎 - 自然语言理解"""
import json
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

from config import chatbot_config
from core.llm.router import llm_router
from core.llm.prompt_manager import prompt_manager

logger = logging.getLogger(__name__)


@dataclass
class Intent:
    """意图识别结果"""
    name: str
    confidence: float
    reasoning: str
    entities: Dict[str, any]


@dataclass
class Entity:
    """实体提取结果"""
    type: str
    value: str
    confidence: float
    start: Optional[int] = None
    end: Optional[int] = None


@dataclass
class NLUResult:
    """NLU 完整结果"""
    intent: Intent
    entities: List[Entity]
    language: str
    confidence: float


class NLUEngine:
    """
    自然语言理解引擎

    功能：
    1. 意图识别（Intent Recognition）
    2. 实体提取（Entity Extraction）
    3. 语言检测（Language Detection）
    4. 情感分析（Sentiment Analysis）
    """

    def __init__(self):
        self.intents = chatbot_config.intents
        self.entity_types = chatbot_config.entity_types
        self.confidence_threshold = chatbot_config.intent_confidence_threshold

    async def understand(
        self,
        user_input: str,
        context: Optional[List[Dict]] = None,
        language: Optional[str] = None
    ) -> NLUResult:
        """
        理解用户输入

        Args:
            user_input: 用户输入文本
            context: 对话上下文
            language: 语言（自动检测如果未提供）

        Returns:
            NLUResult: NLU 结果
        """
        logger.info(f"🔍 NLU analyzing: {user_input[:50]}...")

        # 1. 语言检测
        if not language:
            language = self._detect_language(user_input)

        # 2. 意图识别
        intent = await self._classify_intent(user_input, context or [], language)

        # 3. 实体提取
        entities = await self._extract_entities(user_input, intent.name, language)

        # 4. 综合置信度
        overall_confidence = self._calculate_confidence(intent, entities)

        result = NLUResult(
            intent=intent,
            entities=entities,
            language=language,
            confidence=overall_confidence
        )

        logger.info(
            f"✅ NLU result: intent={intent.name} ({intent.confidence:.2f}), "
            f"entities={len(entities)}, language={language}"
        )

        return result

    async def _classify_intent(
        self,
        user_input: str,
        context: List[Dict],
        language: str
    ) -> Intent:
        """意图分类"""

        # 构建 Prompt
        prompt = prompt_manager.get_nlu_intent_prompt(
            user_input=user_input,
            intents=self.intents,
            context=context,
            language=language
        )

        # 调用 LLM（使用快速模型）
        try:
            response = await llm_router.generate(
                prompt=prompt,
                model_preference="speed",  # 意图识别用快速模型
                temperature=0.1,  # 低温度保证稳定性
                max_tokens=500,
            )

            # 解析响应
            result = self._parse_json_response(response.content)

            return Intent(
                name=result.get("intent", "unknown"),
                confidence=result.get("confidence", 0.0),
                reasoning=result.get("reasoning", ""),
                entities=result.get("entities", {})
            )

        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            # 降级：返回默认意图
            return Intent(
                name="customer_service",
                confidence=0.5,
                reasoning="Fallback to default intent due to error",
                entities={}
            )

    async def _extract_entities(
        self,
        text: str,
        intent: str,
        language: str
    ) -> List[Entity]:
        """实体提取"""

        # 获取该意图需要的实体类型
        intent_config = self.intents.get(intent)
        if not intent_config or not intent_config.required_entities:
            return []

        # 构建 Prompt
        prompt = prompt_manager.get_entity_extraction_prompt(
            text=text,
            entity_types=self.entity_types,
            language=language
        )

        try:
            response = await llm_router.generate(
                prompt=prompt,
                model_preference="speed",
                temperature=0.1,
                max_tokens=500,
            )

            # 解析响应
            result = self._parse_json_response(response.content)
            entities_data = result.get("entities", [])

            entities = []
            for entity_data in entities_data:
                entity = Entity(
                    type=entity_data.get("type", "unknown"),
                    value=entity_data.get("value", ""),
                    confidence=entity_data.get("confidence", 0.0),
                )
                entities.append(entity)

            return entities

        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return []

    def _detect_language(self, text: str) -> str:
        """
        语言检测

        简单启发式规则：
        - 包含中文字符 → zh-CN
        - 否则 → en
        """
        # 检查是否包含中文字符
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        total_chars = len(text)

        if chinese_chars / max(total_chars, 1) > 0.3:
            return "zh-CN"
        else:
            return "en"

    def _calculate_confidence(self, intent: Intent, entities: List[Entity]) -> float:
        """计算综合置信度"""
        # 基础置信度来自意图
        base_confidence = intent.confidence

        # 如果找到了所需的实体，提升置信度
        intent_config = self.intents.get(intent.name)
        if intent_config and intent_config.required_entities:
            required_count = len(intent_config.required_entities)
            found_count = len(entities)
            entity_bonus = min(found_count / max(required_count, 1), 1.0) * 0.1
            base_confidence += entity_bonus

        return min(base_confidence, 1.0)

    def _parse_json_response(self, response: str) -> Dict:
        """解析 LLM 的 JSON 响应"""
        try:
            # 清理可能的 markdown 代码块
            clean_response = response.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]
            if clean_response.startswith("```"):
                clean_response = clean_response[3:]
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]

            return json.loads(clean_response.strip())

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}, response: {response[:200]}")
            return {}
