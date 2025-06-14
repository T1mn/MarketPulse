from unittest.mock import MagicMock, patch

import pytest
import notifier


@pytest.fixture
def mock_bark_response():
    """模拟Bark API响应"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"code": 200, "message": "success"}
    return mock_response


def test_send_bark_notification_success(
    mock_analysis_result, mock_bark_response, use_mock
):
    """测试成功发送Bark通知"""
    if not use_mock:
        pytest.skip("跳过实际API调用测试")

    with patch("MarketPulse.notifier.requests.post", return_value=mock_bark_response):
        result = notifier.send_bark_notification(
            mock_analysis_result,
            "https://example.com/test",
            "Test Source",
            ["AAPL", "MSFT"],
            "2024-03-20T10:00:00Z",
        )
        assert result is True


def test_send_bark_notification_failure(mock_analysis_result, use_mock):
    """测试发送Bark通知失败"""
    if not use_mock:
        pytest.skip("跳过实际API调用测试")

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.json.return_value = {"code": 500, "message": "error"}

    with patch("MarketPulse.notifier.requests.post", return_value=mock_response):
        result = notifier.send_bark_notification(
            mock_analysis_result,
            "https://example.com/test",
            "Test Source",
            ["AAPL"],
            "2024-03-20T10:00:00Z",
        )
        assert result is False


def test_send_bark_notification_network_error(mock_analysis_result, use_mock):
    """测试网络错误情况"""
    if not use_mock:
        pytest.skip("跳过实际API调用测试")

    with patch(
        "MarketPulse.notifier.requests.post", side_effect=Exception("Network Error")
    ):
        result = notifier.send_bark_notification(
            mock_analysis_result,
            "https://example.com/test",
            "Test Source",
            [],
            "2024-03-20T10:00:00Z",
        )
        assert result is False
