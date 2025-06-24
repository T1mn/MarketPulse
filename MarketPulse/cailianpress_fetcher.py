import json
import logging
import time
import uuid
from datetime import datetime
from html import unescape
from xml.sax import SAXParseException

import feedparser
import requests

from MarketPulse import config


def format_cls_news_item(entry):
    """
    将从Feedparser获取的财联社新闻条目统一格式化。
    """
    # 从 'published_parsed' 或 'updated_parsed' 获取时间
    time_struct = entry.get("published_parsed") or entry.get("updated_parsed")
    if time_struct:
        # feedparser 返回的时间元组是UTC时间
        dt_object = datetime.fromtimestamp(time.mktime(time_struct))
        timestamp = int(dt_object.timestamp())
    else:
        timestamp = int(datetime.now().timestamp())

    # 使用链接生成唯一的、确定性的ID
    link = entry.get("link", "")
    if link:
        # 使用UUIDv5和链接生成ID
        id_str = str(uuid.uuid5(uuid.NAMESPACE_URL, link))
    else:
        # Fallback to a random UUID if no link is present
        id_str = str(uuid.uuid4())

    # 处理HTML内容，确保所有实体都被正确解码
    title = unescape(entry.get("title", "无标题"))
    summary = unescape(entry.get("summary", "无摘要"))

    return {
        "id": id_str,
        "headline": title,
        "summary": summary,
        "url": link,
        "source": "财联社",
        "category": "CLS",  # 财联社新闻分类
        "datetime": timestamp,
        "related": "",  # RSS源通常没有相关性字段
    }


def fetch_cls_news():
    """
    通过RSSHub获取并解析财联社热门新闻。
    """
    url = "https://rsshub.app/cls/hot"
    logging.info("正在获取财联社 (CLS) RSS 新闻...")

    try:
        # 配置feedparser以更宽容地处理XML错误
        feedparser.RESOLVE_RELATIVE_URIS = False
        feedparser.SANITIZE_HTML = False

        # 先获取原始内容
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            raw_content = response.content
        except requests.RequestException as e:
            logging.error(f"获取财联社RSS内容失败: {e}")
            return []

        # 使用feedparser解析内容
        feed = feedparser.parse(raw_content)

        # 检查feed是否被正确解析
        if feed.bozo:
            bozo_exception = feed.get("bozo_exception")
            if isinstance(bozo_exception, SAXParseException):
                logging.warning("RSS源包含XML解析错误，但这不影响新闻内容的提取")
            else:
                logging.warning(f"财联社RSS源解析警告: {bozo_exception}")

        if not feed.entries:
            logging.warning("未能从RSS源获取到任何新闻条目")
            return []

        # 只取前10条新闻
        entries = feed.entries[:10]
        logging.info(f"从财联社获取到 {len(feed.entries)} 条新闻，将处理前 10 条。")

        # 格式化新闻条目
        formatted_news = [format_cls_news_item(entry) for entry in entries]

        # 如果开启了保存原始文件
        if config.SAVE_RAW_NEWS_TO_FILE:
            # 保存为结构化的JSON，而不是原始XML
            with open("cls_news.json", "w", encoding="utf-8") as f:
                json.dump(formatted_news, f, ensure_ascii=False, indent=2, default=str)
            logging.info("已将格式化后的财联社新闻保存到 cls_news.json")

        return formatted_news

    except Exception as e:
        logging.error(f"处理财联社RSS源时发生未知错误: {e}")
        return []
