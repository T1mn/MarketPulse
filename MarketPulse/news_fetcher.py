from datetime import datetime

import requests

from MarketPulse import config


class NewsFetcher:
    def __init__(self):
        self.api_key = config.FINNHUB_API_KEY
        self.trusted_sources = config.TRUSTED_SOURCES
        self.market_symbols = config.US_MARKET_SYMBOLS
        self.last_fetch_time = None
        self.min_interval = config.NEWS_FETCH_INTERVAL  # 使用全局配置的间隔时间

    def is_trusted_source(self, source):
        """检查新闻来源是否可信"""
        return source in self.trusted_sources

    def is_market_related(self, headline, summary):
        """检查新闻是否与关注的市场相关"""
        text = (headline + " " + summary).lower()
        return any(symbol.lower() in text for symbol in self.market_symbols)

    def should_fetch_news(self):
        """检查是否应该获取新闻"""
        if not self.last_fetch_time:
            return True
        time_diff = datetime.now() - self.last_fetch_time
        return time_diff.total_seconds() >= self.min_interval * 60

    def fetch_latest_news(self):
        """获取并过滤最新新闻"""
        if not self.should_fetch_news():
            print("距离上次获取新闻时间太短，跳过本次获取")
            return []

        try:
            url = f"https://finnhub.io/api/v1/news?category={config.NEWS_CATEGORY}&token={self.api_key}"
            response = requests.get(url)

            if response.status_code != 200:
                print(f"获取新闻失败: HTTP {response.status_code}")
                return []

            news_list = response.json()
            if not news_list:
                return []

            # 过滤和转换新闻
            filtered_news = []
            for news in news_list:
                # 检查来源是否可信
                if not self.is_trusted_source(news.get("source", "")):
                    continue

                # 检查是否与关注的市场相关
                if not self.is_market_related(
                    news.get("headline", ""), news.get("summary", "")
                ):
                    continue

                # 转换新闻格式
                filtered_news.append(
                    {
                        "id": news.get("id"),
                        "title": news.get("headline"),
                        "content": news.get("summary"),
                        "url": news.get("url", ""),
                        "source": news.get("source", ""),
                        "category": news.get("category", ""),
                        "datetime": news.get("datetime", ""),
                        "related": news.get("related", ""),
                    }
                )

            # 更新最后获取时间
            self.last_fetch_time = datetime.now()

            # 按时间排序，最新的在前面
            filtered_news.sort(key=lambda x: x.get("datetime", ""), reverse=True)

            # 只返回最新的5条新闻
            return filtered_news[:5]

        except Exception as e:
            print(f"获取新闻时发生错误: {str(e)}, 错误代码: {response.status_code}")

            return []


# 创建全局实例
news_fetcher = NewsFetcher()


def fetch_latest_news():
    """对外提供的获取新闻接口"""
    return news_fetcher.fetch_latest_news()
