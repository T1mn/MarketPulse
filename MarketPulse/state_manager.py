import json
import os

import config


def load_processed_ids():
    """从文件加载已处理的新闻ID集合。"""
    if not os.path.exists(config.PROCESSED_NEWS_FILE):
        return set()
    try:
        with open(config.PROCESSED_NEWS_FILE, "r") as f:
            ids_list = json.load(f)
            return set(ids_list)
    except (json.JSONDecodeError, IOError):
        return set()


def save_processed_ids(ids_set):
    """将已处理的新闻ID集合保存到文件。"""
    try:
        with open(config.PROCESSED_NEWS_FILE, "w") as f:
            json.dump(list(ids_set), f)
    except IOError as e:
        print(f"保存已处理ID失败: {e}")
