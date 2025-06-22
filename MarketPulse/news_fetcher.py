import json
import logging
from datetime import datetime, timedelta

import requests

from MarketPulse import config
from MarketPulse.rss_news_fetcher import fetch_rss_news


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
        """第二步：获取所有配置的股票代码的公司新闻，包括美股和A股。"""
        logging.info("正在获取公司相关新闻...")
        all_company_news = []

        # 初始化学员列表
        symbols_to_fetch = []

        # 添加美股市场的符号
        for symbol_list in self.market_symbols.values():
            symbols_to_fetch.extend(symbol_list)

        # 如果开启了A股新闻，则添加A股代码
        if config.FETCH_CHINA_A_SHARE_NEWS:
            logging.info("已开启A股新闻获取，添加相关代码。")
            symbols_to_fetch.extend(config.CHINA_A_SHARE_SYMBOLS)

        # 使用集合去重
        unique_symbols = list(set(symbols_to_fetch))
        logging.info(f"将获取以下公司的代码新闻: {unique_symbols}")

        to_date = datetime.now().strftime("%Y-%m-%d")
        from_date = (
            datetime.now() - timedelta(days=config.COMPANY_NEWS_DAYS_AGO)
        ).strftime("%Y-%m-%d")

        for symbol in unique_symbols:
            logging.info(f"  - 获取 {symbol} 的新闻...")
            url = f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from={from_date}&to={to_date}&token={self.api_key}"
            news_list = self._make_request(url)
            if news_list:
                all_company_news.extend(news_list[: config.MAX_NEWS_PER_SYMBOL])
        return all_company_news

    def fetch_latest_news(self):
        """
        主函数：执行分步获取、汇总、去重、过滤和排序
        现在包含RSS新闻源的获取，但保持独立性
        """
        if not self.should_fetch_news():
            logging.info("距离上次获取新闻时间太短，跳过本次获取。")
            return []

        # 分别获取原始新闻
        finnhub_news = []
        rss_news = []
        
        # 获取RSS新闻源（如彭博社）
        if any([config.FETCH_BLOOMBERG_RSS, config.FETCH_REUTERS_RSS, config.FETCH_WSJ_RSS]):
            logging.info("开始获取RSS新闻源...")
            rss_news = fetch_rss_news()
            logging.info(f"从RSS源获取到 {len(rss_news)} 条新闻")
            
            # 标准化RSS新闻字段并保存到本地文件
            standardized_rss_news = []
            for news in rss_news:
                standardized_news = {
                    "id": news.get("id"),
                    "headline": news.get("title"),  # title -> headline
                    "summary": news.get("content"),  # content -> summary
                    "url": news.get("url"),
                    "source": news.get("source"),
                    "category": "top news",  # 固定为 top news
                    "datetime": news.get("datetime"),
                    "related": news.get("related")
                }
                standardized_rss_news.append(standardized_news)
            
            with open("rss_news.json", "w", encoding='utf-8') as f:
                json.dump(standardized_rss_news, f, ensure_ascii=False, indent=2)
            logging.info("RSS新闻已保存到 rss_news.json")
        
        # 获取Finnhub API新闻
        if config.FETCH_GENERAL_NEWS:
            finnhub_news.extend(self._fetch_news_by_category("general"))
        if config.FETCH_FOREX_NEWS:
            finnhub_news.extend(self._fetch_news_by_category("forex"))
        if config.FETCH_CRYPTO_NEWS:
            finnhub_news.extend(self._fetch_news_by_category("crypto"))
        if config.FETCH_COMPANY_NEWS or config.FETCH_CHINA_A_SHARE_NEWS:
            finnhub_news.extend(self._fetch_company_news())
        
        logging.info(f"从Finnhub API获取到 {len(finnhub_news)} 条新闻")
        
        # 标准化Finnhub新闻字段并保存到本地文件
        standardized_finnhub_news = []
        for news in finnhub_news:
            standardized_news = {
                "id": news.get("id"),
                "headline": news.get("headline"),
                "summary": news.get("summary"),
                "url": news.get("url"),
                "source": news.get("source"),
                "category": "finnhub",  # 固定为 finnhub
                "datetime": news.get("datetime"),
                "related": news.get("related")
            }
            standardized_finnhub_news.append(standardized_news)
        
        with open("finnhub_news.json", "w", encoding='utf-8') as f:
            json.dump(standardized_finnhub_news, f, ensure_ascii=False, indent=2)
        logging.info("Finnhub新闻已保存到 finnhub_news.json")

        # 合并所有新闻（使用原始格式进行后续处理）
        raw_news = finnhub_news + standardized_rss_news
        
        if not raw_news:
            logging.warning("未能从任何来源获取到新闻。")
            return []

        # --- 汇总和处理 ---
        logging.info(f"共获取到 {len(raw_news)} 条原始新闻（Finnhub: {len(finnhub_news)}, RSS: {len(rss_news)}），开始去重和格式化...")

        # 如果开启了只看顶级来源的过滤
        if config.FILTER_TO_TOP_TIER_ONLY:
            initial_count = len(raw_news)
            raw_news = [
                article
                for article in raw_news
                # source contains any of the top tier news sources
                if any(source in article.get("source") for source in config.TOP_TIER_NEWS_SOURCES)
            ]
            logging.info(
                f"已启用顶级来源过滤，从 {initial_count} 条新闻中筛选出 {len(raw_news)} 条。"
            )

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
