import json
import logging
from datetime import datetime, timedelta

import requests

from MarketPulse import config


class NewsFetcher:
    def __init__(self):
        self.api_key = config.FINNHUB_API_KEY
        self.market_symbols = config.MARKET_SYMBOLS
        self.last_fetch_time = None
        self.min_interval = config.NEWS_FETCH_INTERVAL

    def _make_request(self, url):
        """统一处理API请求和初步的错误处理"""
        try:
            response = requests.get(url)
            response.raise_for_status()  # 对错误的HTTP状态码抛出异常
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"获取新闻时发生网络错误: {e}, URL: {url}")
            return None
        except json.JSONDecodeError:
            logging.error(f"无法解析API响应的JSON内容: {url}")
            return None

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

    def _fetch_news_by_category(self, category):
        """第一步和第三步：根据类别获取新闻 (forex, crypto, general)"""
        logging.info(f"正在获取 '{category}' 类别的新闻...")
        url = f"https://finnhub.io/api/v1/news?category={category}&token={self.api_key}"
        news_list = self._make_request(url)
        if not news_list:
            return []
        return news_list[: config.MAX_NEWS_PER_CATEGORY]

    def _fetch_company_news(self):
        """第二步：获取所有配置的股票代码的公司新闻"""
        logging.info("正在获取美股公司相关新闻...")
        all_company_news = []
        symbols_to_fetch = [
            symbol
            for symbol_list in self.market_symbols.values()
            for symbol in symbol_list
        ]

        to_date = datetime.now().strftime("%Y-%m-%d")
        from_date = (
            datetime.now() - timedelta(days=config.COMPANY_NEWS_DAYS_AGO)
        ).strftime("%Y-%m-%d")

        for symbol in symbols_to_fetch:
            logging.info(f"  - 获取 {symbol} 的新闻...")
            url = f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from={from_date}&to={to_date}&token={self.api_key}"
            news_list = self._make_request(url)
            if news_list:
                all_company_news.extend(news_list[: config.MAX_NEWS_PER_SYMBOL])
        return all_company_news

    def fetch_latest_news(self):
        """
        主函数：执行分步获取、汇总、去重、过滤和排序
        """
        if not self.should_fetch_news():
            logging.info("距离上次获取新闻时间太短，跳过本次获取。")
            return []

        # 分步获取原始新闻
        raw_news = []
        if config.FETCH_FOREX_NEWS:
            raw_news.extend(self._fetch_news_by_category("forex"))
        if config.FETCH_CRYPTO_NEWS:
            raw_news.extend(self._fetch_news_by_category("crypto"))
        if config.FETCH_GENERAL_NEWS:
            raw_news.extend(self._fetch_news_by_category("general"))
        if config.FETCH_COMMODITY_NEWS:
            raw_news.extend(self._fetch_news_by_category("commodity"))
        if config.FETCH_COMPANY_NEWS:
            raw_news.extend(self._fetch_company_news())

        if not raw_news:
            logging.warning("未能从任何来源获取到新闻。")
            return []

        # --- 汇总和处理 ---
        logging.info(f"共获取到 {len(raw_news)} 条原始新闻，开始去重和格式化...")
        processed_news = {}  # 使用字典通过ID去重
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
news_fetcher = NewsFetcher()


def fetch_latest_news():
    """对外提供的获取新闻接口"""
    return news_fetcher.fetch_latest_news()
