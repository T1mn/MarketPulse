#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
RSS新闻获取器模块

专门用于从RSS源（如彭博社）获取新闻，并提取相关的股票代码信息。
支持从RSS的category标签中提取股票代码，为AI分析提供更丰富的结构化数据。
"""

import logging
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any

import feedparser
import requests

from MarketPulse import config


class RSSNewsFetcher:
    """RSS新闻获取器，专门处理RSS源的新闻获取和解析"""

    def __init__(self):
        self.last_fetch_time = None
        self.min_interval = config.NEWS_FETCH_INTERVAL

    def _make_request(self, url: str) -> str | None:
        """
        统一处理RSS请求和初步的错误处理

        Args:
            url: RSS源的URL

        Returns:
            RSS内容的字符串，如果请求失败则返回None
        """
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logging.error(f"获取RSS时发生网络错误: {e}, URL: {url}")
            return None
        except Exception as e:
            logging.error(f"获取RSS时发生未知错误: {e}, URL: {url}")
            return None

    def _extract_stock_symbols(self, entry) -> str:
        """
        从RSS条目中提取股票代码

        Args:
            entry: feedparser解析的RSS条目对象

        Returns:
            股票代码字符串，多个代码用逗号分隔
        """
        stock_symbols = []

        # 检查是否有tags属性
        if hasattr(entry, "tags") and entry.tags:
            for tag in entry.tags:
                # 检查是否为股票代码标签
                if hasattr(tag, "scheme") and tag.scheme == "stock-symbol":
                    if hasattr(tag, "term") and tag.term:
                        stock_symbols.append(str(tag.term))

        # 如果没有找到股票代码，尝试从category字段提取
        if not stock_symbols:
            # 检查category字段（某些RSS源可能使用不同的结构）
            if hasattr(entry, "category") and entry.category:
                # 如果category是列表
                if isinstance(entry.category, list):
                    for cat in entry.category:
                        if (
                            isinstance(cat, dict)
                            and cat.get("domain") == "stock-symbol"
                        ):
                            if cat.get("content"):
                                stock_symbols.append(str(cat["content"]))
                # 如果category是字符串，尝试解析
                elif isinstance(entry.category, str):
                    # 简单的股票代码模式匹配（如 NYS:DIS, NAS:AAPL）
                    import re

                    symbols = re.findall(r"[A-Z]{3,4}:[A-Z]+", entry.category)
                    stock_symbols.extend(symbols)

        # 从你提供的RSS数据中，我看到股票代码在category标签中，格式如：
        # <category domain="stock-symbol"><![CDATA[NYS:DIS]]></category>
        # 需要检查feedparser是否正确解析了这种结构
        if not stock_symbols:
            # 尝试从entry的所有属性中查找股票代码
            for attr_name in dir(entry):
                if "category" in attr_name.lower() or "tag" in attr_name.lower():
                    attr_value = getattr(entry, attr_name, None)
                    if attr_value:
                        logging.debug(f"检查属性 {attr_name}: {attr_value}")

        return ", ".join(stock_symbols)

    def _format_rss_item(self, entry, source_name: str) -> Dict[str, Any]:
        """
        将RSS条目格式化为标准化的新闻格式

        确保与Finnhub API格式完全一致

        Args:
            entry: feedparser解析的RSS条目对象
            source_name: 新闻来源名称

        Returns:
            格式化后的新闻字典
        """
        # 生成唯一ID（使用URL的哈希值）
        url = getattr(entry, "link", "")
        unique_id = hashlib.sha256(url.encode("utf-8")).hexdigest()

        # 增强摘要提取逻辑：优先使用summary，备用description
        # 确保content字段不为空
        summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
        if not summary or summary.strip() == "":
            summary = "该文章内容为空，无法提供摘要。"

        # 提取股票代码
        stock_symbols = self._extract_stock_symbols(entry)

        # 处理发布时间
        published_time = 0
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                # 将时间元组转换为datetime对象
                dt = datetime(*entry.published_parsed[:6])
                # 转换为UTC时间戳
                published_time = int(dt.replace(tzinfo=timezone.utc).timestamp())
            except Exception as e:
                logging.warning(f"解析发布时间失败: {e}")

        # 确保格式与Finnhub API完全一致
        formatted_item = {
            "id": unique_id,
            "title": getattr(entry, "title", "无标题"),
            "content": summary,  # 对应Finnhub的summary字段
            "url": url,
            "source": source_name,
            "category": getattr(entry, "category", ""),
            "datetime": published_time,
            "related": stock_symbols,  # 股票代码字符串
        }

        return formatted_item

    def fetch_rss_news(
        self, rss_url: str, source_name: str, max_items: int = 10
    ) -> List[Dict[str, Any]]:
        """
        从指定的RSS源获取新闻

        Args:
            rss_url: RSS源的URL
            source_name: 新闻来源名称
            max_items: 最大获取条目数

        Returns:
            格式化后的新闻列表
        """

        # 获取RSS内容
        rss_content = self._make_request(rss_url)
        if not rss_content:
            logging.error(f"无法获取RSS内容: {rss_url}")
            return []

        # 解析RSS
        try:
            feed = feedparser.parse(rss_content)
        except Exception as e:
            logging.error(f"解析RSS失败: {e}, URL: {rss_url}")
            return []

        # 检查解析结果
        if feed.bozo:
            logging.warning(f"RSS解析存在警告: {feed.bozo_exception}")

        # 格式化新闻条目
        formatted_news = []
        for entry in feed.entries[:max_items]:
            try:
                formatted_item = self._format_rss_item(entry, source_name)
                formatted_news.append(formatted_item)
            except Exception as e:
                logging.error(f"格式化RSS条目失败: {e}")
                continue

        return formatted_news

    def fetch_bloomberg_news(self) -> List[Dict[str, Any]]:
        """
        专门获取彭博社新闻

        Returns:
            彭博社新闻列表
        """
        all_bloomberg_news = []

        # 获取所有配置的彭博社RSS源
        for source_name, rss_url in config.BLOOMBERG_RSS_SOURCES.items():
            try:
                logging.info(f"正在获取彭博社 {source_name} 新闻...")
                news = self.fetch_rss_news(
                    rss_url, f"Bloomberg-{source_name}", config.MAX_NEWS_PER_CATEGORY
                )
                all_bloomberg_news.extend(news)
                logging.info(f"从彭博社 {source_name} 获取到 {len(news)} 条新闻")
            except Exception as e:
                logging.error(f"获取彭博社 {source_name} 新闻失败: {e}")
                continue

        return all_bloomberg_news

    def should_fetch_news(self) -> bool:
        """检查是否应该获取新闻"""
        if not self.last_fetch_time:
            return True
        time_diff = datetime.now() - self.last_fetch_time
        return time_diff.total_seconds() >= self.min_interval * 60

    def fetch_all_rss_news(self) -> List[Dict[str, Any]]:
        """
        获取所有配置的RSS源新闻

        Returns:
            所有RSS源的新闻列表
        """
        if not self.should_fetch_news():
            logging.info("距离上次获取RSS新闻时间太短，跳过本次获取。")
            return []

        all_news = []

        # 获取彭博社新闻
        if config.FETCH_BLOOMBERG_RSS:
            bloomberg_news = self.fetch_bloomberg_news()
            all_news.extend(bloomberg_news)

        # 可以在这里添加更多RSS源
        # 例如：路透社、华尔街日报等

        self.last_fetch_time = datetime.now()
        return all_news


# 创建全局实例
rss_news_fetcher = RSSNewsFetcher()


def fetch_rss_news():
    """对外提供的RSS新闻获取接口"""
    return rss_news_fetcher.fetch_all_rss_news()
