import json
from unittest.mock import mock_open, patch

import pytest

from MarketPulse import state_manager


def test_load_processed_ids_empty_file():
    """测试加载空的已处理ID文件"""
    with patch("os.path.exists", return_value=False):
        result = state_manager.load_processed_ids()
        assert isinstance(result, set)
        assert len(result) == 0


def test_load_processed_ids_success():
    """测试成功加载已处理ID"""
    test_ids = ["id1", "id2", "id3"]
    mock_file = mock_open(read_data=json.dumps(test_ids))
    with patch("os.path.exists", return_value=True), patch("builtins.open", mock_file):
        result = state_manager.load_processed_ids()
        assert isinstance(result, set)
        assert len(result) == 3
        assert "id1" in result
        assert "id2" in result
        assert "id3" in result


def test_save_processed_ids():
    """测试保存已处理ID"""
    test_ids = {"id1", "id2", "id3"}
    mock_file = mock_open()
    with patch("builtins.open", mock_file):
        state_manager.save_processed_ids(test_ids)
        mock_file.assert_called_once()
        # 验证写入的内容是列表格式
        written_data = json.loads(mock_file().write.call_args[0][0])
        assert isinstance(written_data, list)
        assert len(written_data) == 3
        assert "id1" in written_data


def test_save_processed_ids_empty():
    """测试保存空已处理ID"""
    test_ids = set()
    mock_file = mock_open()
    with patch("builtins.open", mock_file):
        state_manager.save_processed_ids(test_ids)
        mock_file.assert_called_once()
        # 验证写入的内容是空列表
        written_data = json.loads(mock_file().write.call_args[0][0])
        assert isinstance(written_data, list)
        assert len(written_data) == 0


def test_save_processed_ids_invalid_type():
    """测试保存已处理ID，类型无效"""
    test_ids = "not a set"
    with pytest.raises(TypeError):
        state_manager.save_processed_ids(test_ids)


def test_save_processed_ids_invalid_element_type():
    """测试保存已处理ID，元素类型无效"""
    test_ids = {"id1", "not an ID", "id3"}
    with pytest.raises(TypeError):
        state_manager.save_processed_ids(test_ids)


def test_save_processed_ids_invalid_element_value():
    """测试保存已处理ID，元素值无效"""
    test_ids = {"id1", "id2", "invalid ID"}
    with pytest.raises(ValueError):
        state_manager.save_processed_ids(test_ids)
