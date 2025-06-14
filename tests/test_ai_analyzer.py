from unittest.mock import patch

import pytest
from MarketPulse import ai_analyzer


def test_analyze_news_article_success(
    mock_article, mock_analysis_result, mock_genai_client, use_mock
):
    """测试新闻分析成功的情况"""
    if not use_mock:
        pytest.skip("跳过实际API调用测试")

    with patch("MarketPulse.ai_analyzer.genai.Client", return_value=mock_genai_client):
        result = ai_analyzer.analyze_news_article(mock_article)
        assert result is not None
        assert isinstance(result, dict)
        assert "summary" in result


def test_analyze_news_article_failure(mock_article, use_mock):
    """测试新闻分析失败的情况"""
    if not use_mock:
        pytest.skip("跳过实际API调用测试")

    with patch(
        "MarketPulse.ai_analyzer.genai.Client", side_effect=Exception("API Error")
    ):
        result = ai_analyzer.analyze_news_article(mock_article)
        assert result is None


def test_analyze_news_article_empty_input():
    """测试空输入的情况"""
    result = ai_analyzer.analyze_news_article({})
    assert result is None
