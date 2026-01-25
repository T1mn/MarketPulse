"""NLU 引擎测试"""
import pytest
from core.dialogue.nlu import NLUEngine


@pytest.mark.asyncio
async def test_nlu_intent_recognition():
    """测试意图识别"""
    nlu = NLUEngine()

    # 测试市场查询意图
    result = await nlu.understand("特斯拉现在多少钱？")

    assert result.intent.name == "market_query"
    assert result.confidence > 0.5
    assert result.language in ["zh-CN", "en"]


@pytest.mark.asyncio
async def test_nlu_entity_extraction():
    """测试实体提取"""
    nlu = NLUEngine()

    result = await nlu.understand("帮我买入100股苹果")

    # 应该识别到资产实体
    assert len(result.entities) > 0

    # 验证实体类型
    entity_types = [e.type for e in result.entities]
    assert "asset" in entity_types or "action" in entity_types


@pytest.mark.asyncio
async def test_nlu_language_detection():
    """测试语言检测"""
    nlu = NLUEngine()

    # 中文
    result_zh = await nlu.understand("你好")
    assert result_zh.language == "zh-CN"

    # 英文
    result_en = await nlu.understand("Hello")
    assert result_en.language == "en"
