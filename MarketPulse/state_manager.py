import json
import os
import logging
from MarketPulse import config

# 定义默认状态结构
DEFAULT_STATE = {
    "processed_ids": [],
    "pushplus_restricted_until": 0  # 存储时间戳
}

def load_state():
    """从文件加载应用状态。如果文件不存在或无效，则返回默认状态。"""
    if not os.path.exists(config.APP_STATE_FILE):
        return DEFAULT_STATE.copy()
    try:
        with open(config.APP_STATE_FILE, "r") as f:
            state = json.load(f)
            # 确保所有键都存在
            for key, value in DEFAULT_STATE.items():
                state.setdefault(key, value)
            return state
    except (json.JSONDecodeError, IOError) as e:
        logging.warning(f"无法加载状态文件，将使用默认状态: {e}")
        return DEFAULT_STATE.copy()

def save_state(state):
    """将应用状态保存到文件。"""
    try:
        with open(config.APP_STATE_FILE, "w") as f:
            json.dump(state, f, indent=4)
    except IOError as e:
        logging.error(f"保存状态文件失败: {e}")

def load_processed_ids():
    """从状态文件加载已处理的新闻ID集合。"""
    state = load_state()
    return set(state.get("processed_ids", []))

def save_processed_ids(ids_set):
    """将已处理的新闻ID集合保存到状态文件。"""
    state = load_state()
    state["processed_ids"] = list(ids_set)
    save_state(state)
