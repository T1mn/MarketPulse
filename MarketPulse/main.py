import time

import schedule

from MarketPulse import ai_analyzer, config, news_fetcher, notifier, state_manager


def run_job():
    """
    定义一个完整的工作流：获取新闻 -> 批量分析 -> 过滤 -> 汇总推送。
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
        print("任务结束: 没有从API获取到新闻。")
        return

    # 3. 过滤掉已经处理过的新闻
    new_articles = [
        article for article in articles if article.get("id") not in processed_ids
    ]

    if not new_articles:
        print("所有获取到的新闻都已被处理过，任务结束。")
        return

    new_articles = new_articles[:5]

    print(f"发现 {len(new_articles)} 条新文章，正在进行AI批量分析...")

    # 4. 对所有新新闻进行批量AI分析
    analysis_results = ai_analyzer.analyze_news_in_batch(new_articles)

    if not analysis_results:
        print("AI分析未返回任何结果，任务结束。")
        # 仍然需要保存ID，避免重复分析失败的文章
        for article in new_articles:
            if article.get("id"):
                processed_ids.add(article.get("id"))
        state_manager.save_processed_ids(processed_ids)
        return

    # 5. 过滤掉无效/“未知”的分析建议
    valid_analyses = []
    for analysis in analysis_results:
        insight = analysis.get("actionable_insight", {})
        print(insight)
        asset_name = insight.get("asset", {}).get("name")
        action = insight.get("action")

        # 如果关键信息都是“未知”，则认为是无效建议，过滤掉
        if asset_name == "未知" and action == "未知":
            print(f"过滤无效建议 (ID: {analysis.get('id')})")
            continue

        valid_analyses.append(analysis)

    # 6. 如果有有效建议，则汇总发送通知
    if valid_analyses:
        print(f"分析完成，发现 {len(valid_analyses)} 条有效建议，准备发送通知。")
        # 创建文章ID到文章内容的映射，方便查找URL
        articles_map = {article["id"]: article for article in new_articles}
        notifier.send_summary_notification(valid_analyses, articles_map)
    else:
        print("AI分析完成，但没有发现可操作的有效建议。")

    # 7. 将所有新处理的文章ID加入集合并保存
    for article in new_articles:
        if article.get("id"):
            processed_ids.add(article.get("id"))
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
