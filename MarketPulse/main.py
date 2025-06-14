import time

import schedule

from MarketPulse import ai_analyzer, config, news_fetcher, notifier, state_manager


def run_job():
    """
    定义一个完整的工作流：获取新闻 -> 分析 -> 推送。
    """
    print("\n" + "=" * 50)
    print(f"任务开始: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # 1. 加载已经处理过的新闻ID
    processed_ids = state_manager.load_processed_ids()
    print(f"已加载 {len(processed_ids)} 个已处理的新闻ID。")

    # 2. 获取最新新闻
    articles = news_fetcher.fetch_latest_news()
    if not articles:
        print("任务结束: 没有新新闻可处理。")
        return

    # 3. 倒序处理新闻，确保按时间顺序推送
    new_articles_count = 0
    for article in reversed(articles):
        article_id = article.get("id")

        # 检查新闻是否已经被处理过
        if not article_id or article_id in processed_ids:
            continue

        new_articles_count += 1
        print(f"\n--- 处理新文章 ID: {article_id} ---")
        print(f"标题: {article.get('title')}")

        # 4. 对新新闻进行AI分析
        analysis_result = ai_analyzer.analyze_news_article(article)

        if analysis_result:
            # 获取相关股票信息
            related_symbols = []
            if article.get("related"):
                related_symbols = [
                    symbol for symbol in article.get("related", "").split(",") if symbol
                ]

            # 5. 发送通知
            notifier.send_bark_notification(
                analysis_result,
                article.get("url"),
                article.get("source"),
                related_symbols,
                article.get("datetime"),
            )

            # 6. 将处理过的ID加入集合
            processed_ids.add(article_id)

            # 增加延迟，避免对API的请求过于频繁
            time.sleep(5)
        else:
            print(f"文章 {article_id} 分析失败，跳过。")

    if new_articles_count == 0:
        print("所有获取到的新闻都已被处理过。")

    # 7. 保存更新后的已处理ID列表
    state_manager.save_processed_ids(processed_ids)
    print("\n" + "=" * 50)
    print(f"任务结束: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)


# --- 程序主入口 ---
if __name__ == "__main__":
    print("MarketPulse-金融资讯AI分析推送服务启动...")

    # 立即执行一次任务，方便测试
    run_job()

    # 设置定时任务，使用配置的间隔时间
    schedule.every(config.NEWS_FETCH_INTERVAL).minutes.do(run_job)

    print(f"调度器已设置，将每{config.NEWS_FETCH_INTERVAL}分钟运行一次。")

    while True:
        schedule.run_pending()
        time.sleep(1)
