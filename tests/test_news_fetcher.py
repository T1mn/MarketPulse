from unittest.mock import patch

import pytest
from MarketPulse import news_fetcher


@pytest.fixture
def mock_finnhub_response():
    """模拟Finnhub API响应"""
    return [
        {
            "id": "test_news_1",
            "title": "Test News 1",
            "content": "Test Content 1",
            "url": "https://example.com/1",
            "source": "Test Source",
            "datetime": "2024-03-20T10:00:00Z",
            "related": "AAPL,MSFT",
        },
        {
            "id": "test_news_2",
            "title": "Test News 2",
            "content": "Test Content 2",
            "url": "https://example.com/2",
            "source": "Test Source",
            "datetime": "2024-03-20T11:00:00Z",
            "related": "GOOGL",
        },
    ]


def test_fetch_latest_news_success(mock_finnhub_response, use_mock):
    """测试成功获取最新新闻"""
    if not use_mock:
        pytest.skip("跳过实际API调用测试")

    with patch(
        "MarketPulse.news_fetcher.finnhub_client.general_news",
        return_value=mock_finnhub_response,
    ):
        articles = news_fetcher.fetch_latest_news()
        assert isinstance(articles, list)
        assert len(articles) == 2
        assert articles[0]["id"] == "test_news_1"
        assert articles[1]["id"] == "test_news_2"


def test_fetch_latest_news_empty(use_mock):
    """测试获取空新闻列表"""
    if not use_mock:
        pytest.skip("跳过实际API调用测试")

    with patch("MarketPulse.news_fetcher.finnhub_client.general_news", return_value=[]):
        articles = news_fetcher.fetch_latest_news()
        assert isinstance(articles, list)
        assert len(articles) == 0


def test_fetch_latest_news_api_error(use_mock):
    """测试API错误情况"""
    if not use_mock:
        pytest.skip("跳过实际API调用测试")

    with patch(
        "MarketPulse.news_fetcher.finnhub_client.general_news",
        side_effect=Exception("API Error"),
    ):
        articles = news_fetcher.fetch_latest_news()
        assert isinstance(articles, list)
        assert len(articles) == 0
