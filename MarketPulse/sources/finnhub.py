import json
import logging
from datetime import datetime, timedelta

import requests

from MarketPulse import config


def _make_request(url):
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


def _fetch_news_by_category(category, api_key):
    """根据类别获取新闻 (forex, crypto, general)"""
    logging.info(f"正在获取 '{category}' 类别的新闻...")
    url = f"https://finnhub.io/api/v1/news?category={category}&token={api_key}"
    news_list = _make_request(url)
    if not news_list:
        return []
    return news_list[: config.MAX_NEWS_PER_CATEGORY]


def _fetch_company_news(market_symbols, api_key):
    """获取所有配置的股票代码的公司新闻，包括美股和A股。"""
    logging.info("正在获取公司相关新闻...")
    all_company_news = []

    # 初始化学员列表
    symbols_to_fetch = []

    # 添加美股市场的符号
    for symbol_list in market_symbols.values():
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
        url = f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from={from_date}&to={to_date}&token={api_key}"
        news_list = _make_request(url)
        if news_list:
            all_company_news.extend(news_list[: config.MAX_NEWS_PER_SYMBOL])
    return all_company_news


def fetch_finnhub_news():
    """统一获取所有Finnhub相关新闻（general, forex, crypto, company, A股）"""
    news = []
    api_key = config.FINNHUB_API_KEY
    market_symbols = config.MARKET_SYMBOLS

    if config.FETCH_GENERAL_NEWS:
        news.extend(_fetch_news_by_category("general", api_key))
    if config.FETCH_FOREX_NEWS:
        news.extend(_fetch_news_by_category("forex", api_key))
    if config.FETCH_CRYPTO_NEWS:
        news.extend(_fetch_news_by_category("crypto", api_key))
    if config.FETCH_COMPANY_NEWS or config.FETCH_CHINA_A_SHARE_NEWS:
        news.extend(_fetch_company_news(market_symbols, api_key))
    return news
