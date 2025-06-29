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


def format_notatesla_news_item(entry):
    """
    将从Feedparser获取的'Not a Tesla App'新闻条目统一格式化。
    """
    time_struct = entry.get("published_parsed") or entry.get("updated_parsed")
    if time_struct:
        dt_object = datetime.fromtimestamp(time.mktime(time_struct))
        timestamp = int(dt_object.timestamp())
    else:
        timestamp = int(datetime.now().timestamp())

    link = entry.get("link", "")
    id_str = str(uuid.uuid5(uuid.NAMESPACE_URL, link)) if link else str(uuid.uuid4())

    title = unescape(entry.get("title", "无标题"))
    summary = unescape(entry.get("summary", "无摘要"))

    return {
        "id": id_str,
        "headline": title,
        "summary": summary,
        "url": link,
        "source": "Not a Tesla App",
        "category": "TESLA",
        "datetime": timestamp,
        "related": "TSLA",
    }


def fetch_notatesla_news():
    """
    通过RSS获取并解析'Not a Tesla App'新闻。
    """
    url = config.NOTATESLA_RSS_URL
    logging.info("正在获取 'Not a Tesla App' RSS 新闻...")

    try:
        feedparser.RESOLVE_RELATIVE_URIS = False
        feedparser.SANITIZE_HTML = False

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            raw_content = response.content
        except requests.RequestException as e:
            logging.error(f"获取 'Not a Tesla App' RSS内容失败: {e}")
            return []

        feed = feedparser.parse(raw_content)

        if feed.bozo:
            if isinstance(feed.get("bozo_exception"), SAXParseException):
                logging.warning("RSS源包含XML解析错误，但可能不影响内容提取。")
            else:
                logging.warning(
                    f"'Not a Tesla App' RSS源解析警告: {feed.bozo_exception}"
                )

        if not feed.entries:
            logging.warning("未能从 'Not a Tesla App' RSS源获取到任何新闻条目。")
            return []

        entries = feed.entries[:10]
        logging.info(
            f"从 'Not a Tesla App' 获取到 {len(feed.entries)} 条新闻，将处理前 10 条。"
        )

        formatted_news = [format_notatesla_news_item(entry) for entry in entries]

        if config.SAVE_RAW_NEWS_TO_FILE:
            with open("notatesla_news.json", "w", encoding="utf-8") as f:
                json.dump(formatted_news, f, ensure_ascii=False, indent=2, default=str)
            logging.info(
                "已将格式化后的 'Not a Tesla App' 新闻保存到 notatesla_news.json"
            )

        return formatted_news

    except Exception as e:
        logging.error(f"处理 'Not a Tesla App' RSS源时发生未知错误: {e}")
        return []
