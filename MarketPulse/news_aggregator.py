import json
import logging
import re
from datetime import datetime
from html import unescape

from MarketPulse import config
from MarketPulse.sources.cailianpress import fetch_cls_news
from MarketPulse.sources.finnhub import fetch_finnhub_news
from MarketPulse.sources.notatesla import fetch_notatesla_news
from MarketPulse.sources.rss import fetch_rss_news


class NewsAggregator:
    def __init__(self):
        self.last_fetch_time = None
        self.min_interval = config.NEWS_FETCH_INTERVAL

    def _format_news_item(self, news_item):
        """将从API获取的原始新闻条目统一格式化"""
        return {
            "id": news_item.get("id"),
            "title": news_item.get("headline"),
            "content": news_item.get("summary"),
            "url": news_item.get("url", ""),
            "source": news_item.get("source", ""),
            "category": news_item.get("category", ""),
            "datetime": news_item.get("datetime", 0),  # 使用0作为默认值，便于排序
            "related": news_item.get("related", ""),
        }

    def should_fetch_news(self):
        """检查是否应该获取新闻"""
        if not self.last_fetch_time:
            return True
        time_diff = datetime.now() - self.last_fetch_time
        return time_diff.total_seconds() >= self.min_interval * 60

    def format_rss_news_item(self, news):
        """标准化RSS新闻字段"""
        return {
            "id": news.get("id"),
            "headline": news.get("title"),  # title -> headline
            "summary": news.get("content"),  # content -> summary
            "url": news.get("url"),
            "source": news.get("source"),
            "category": "top news",  # 固定为 top news
            "datetime": news.get("datetime"),
            "related": news.get("related"),
        }

    def format_finnhub_news_item(self, news):
        """标准化Finnhub新闻字段"""
        return {
            "id": news.get("id"),
            "headline": news.get("headline"),
            "summary": news.get("summary"),
            "url": news.get("url"),
            "source": news.get("source"),
            "category": "finnhub",  # 固定为 finnhub
            "datetime": news.get("datetime"),
            "related": news.get("related"),
        }

    def format_cls_news_item(self, news):
        """标准化财联社新闻字段，并清理HTML内容"""

        def clean_html_content(content):
            if not content:
                return ""
            # 将<br>和</p>转换为换行符
            content = content.replace("<br>", "\n").replace("</p>", "\n")
            # 移除所有HTML标签
            content = re.sub(r"<[^>]+>", "", content)
            # 解码HTML实体
            content = unescape(content)
            # 清理多余空白行
            lines = [line.strip() for line in content.split("\n")]
            lines = [line for line in lines if line]
            return "\n".join(lines)

        return {
            "id": news.get("id"),
            "headline": clean_html_content(news.get("headline")),
            "summary": clean_html_content(news.get("summary")),
            "url": news.get("url"),
            "source": news.get("source"),
            "category": "cls",  # 固定为 cls
            "datetime": news.get("datetime"),
            "related": news.get("related", ""),
        }

    def format_notatesla_news_item(self, news):
        """标准化 'Not a Tesla App' 新闻字段"""
        return {
            "id": news.get("id"),
            "headline": news.get("headline"),
            "summary": news.get("summary"),
            "url": news.get("url"),
            "source": "Not a Tesla App",
            "category": "TESLA",
            "datetime": news.get("datetime"),
            "related": "TSLA",
        }

    def fetch_latest_news(self):
        """
        主函数：执行分步获取、汇总、去重、过滤和排序
        """
        if not self.should_fetch_news():
            logging.info("距离上次获取新闻时间太短，跳过本次获取。")
            return []

        # --- 分别获取所有来源的新闻 ---
        finnhub_news, rss_news, cls_news, notatesla_news = [], [], [], []

        # 获取财联社新闻
        if config.FETCH_CLS_NEWS:
            raw_cls_news = fetch_cls_news()
            cls_news = [self.format_cls_news_item(news) for news in raw_cls_news]
            logging.info(f"从财联社获取到 {len(cls_news)} 条新闻")

        # 获取 'Not a Tesla App' 新闻
        if config.FETCH_NOTATESLA_NEWS:
            raw_notatesla_news = fetch_notatesla_news()
            notatesla_news = [
                self.format_notatesla_news_item(news) for news in raw_notatesla_news
            ]
            logging.info(f"从 'Not a Tesla App' 获取到 {len(notatesla_news)} 条新闻")

        # 获取通用RSS新闻源 (例如彭博社)
        if any(
            [config.FETCH_BLOOMBERG_RSS, config.FETCH_REUTERS_RSS, config.FETCH_WSJ_RSS]
        ):
            raw_rss_news = fetch_rss_news()
            rss_news = [self.format_rss_news_item(news) for news in raw_rss_news]
            logging.info(f"从RSS源获取到 {len(rss_news)} 条新闻")
            if config.SAVE_RAW_NEWS_TO_FILE:
                with open("rss_news.json", "w", encoding="utf-8") as f:
                    json.dump(rss_news, f, ensure_ascii=False, indent=2)
                logging.info("RSS新闻已保存到 rss_news.json")

        # 获取Finnhub API新闻
        raw_finnhub_news = fetch_finnhub_news()
        finnhub_news = [
            self.format_finnhub_news_item(news) for news in raw_finnhub_news
        ]
        logging.info(f"从Finnhub API获取到 {len(finnhub_news)} 条新闻")
        if config.SAVE_RAW_NEWS_TO_FILE:
            with open("finnhub_news.json", "w", encoding="utf-8") as f:
                json.dump(finnhub_news, f, ensure_ascii=False, indent=2)
            logging.info("Finnhub新闻已保存到 finnhub_news.json")

        # --- 合并、去重、排序 ---
        raw_news = finnhub_news + rss_news + cls_news + notatesla_news
        if not raw_news:
            logging.warning("未能从任何来源获取到新闻。")
            return []

        logging.info(
            f"共获取到 {len(raw_news)} 条原始新闻 (Finnhub: {len(finnhub_news)}, RSS: {len(rss_news)}, CLS: {len(cls_news)}, NotATeslaApp: {len(notatesla_news)})，开始去重和格式化..."
        )

        # 过滤顶级来源
        if config.FILTER_TO_TOP_TIER_ONLY:
            initial_count = len(raw_news)
            raw_news = [
                article
                for article in raw_news
                if article.get("source")
                and any(
                    source in (article.get("source") or "")
                    for source in config.TOP_TIER_NEWS_SOURCES
                )
            ]
            logging.info(
                f"已启用顶级来源过滤，从 {initial_count} 条新闻中筛选出 {len(raw_news)} 条。"
            )

        # 通过ID去重
        processed_news = {}
        for news in raw_news:
            if not news or not news.get("id"):
                continue
            if news["id"] in processed_news:
                continue
            processed_news[news["id"]] = self._format_news_item(news)

        final_news_list = list(processed_news.values())
        final_news_list.sort(key=lambda x: x.get("datetime", 0), reverse=True)

        self.last_fetch_time = datetime.now()
        logging.info(f"处理完成，返回 {len(final_news_list)} 条唯一且格式化的新闻。")
        return final_news_list


# 创建全局实例
news_aggregator = NewsAggregator()


def fetch_latest_news():
    """对外提供的获取新闻接口"""
    return news_aggregator.fetch_latest_news()
