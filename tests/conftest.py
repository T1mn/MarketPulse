import os
from unittest.mock import MagicMock

import pytest


def pytest_configure(config):
    """强制在CI环境中使用mock"""
    if os.getenv("CI"):
        os.environ["USE_MOCK"] = "true"


@pytest.fixture
def use_mock():
    """控制是否使用mock的fixture"""
    return os.getenv("USE_MOCK", "true").lower() == "true"


@pytest.fixture
def mock_article():
    """返回一个模拟的新闻文章数据"""
    return {
        "id": "test_article_1",
        "title": "测试新闻标题",
        "content": "这是一条测试新闻内容",
        "url": "https://example.com/test",
        "source": "Test Source",
        "datetime": "2024-03-20T10:00:00Z",
        "related": "AAPL,MSFT",
    }


@pytest.fixture
def mock_analysis_result():
    """返回一个模拟的AI分析结果"""
    return {
        "summary": "测试新闻摘要",
        "market_impact": {"market": "美股科技板块", "impact_level": "中"},
        "actionable_insight": {
            "asset": {"name": "苹果公司", "ticker": "AAPL"},
            "action": "观望",
            "reasoning": "测试原因",
            "confidence": "中",
        },
    }


@pytest.fixture
def mock_genai_client():
    """模拟Gemini API客户端"""
    mock_client = MagicMock()
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"summary": "测试摘要"}'
    mock_model.generate_content.return_value = mock_response
    mock_client.models.return_value = mock_model
    return mock_client
