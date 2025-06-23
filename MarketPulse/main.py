import logging
import time

import schedule

from MarketPulse import ai_analyzer, config, news_fetcher, notifier, state_manager
from MarketPulse.logger_setup import setup_logging


def run_job():
    """
    定义一个完整的工作流：获取新闻 -> 批量分析 -> 过滤 -> 汇总推送。
    """
    logging.info("=" * 50)
    logging.info("任务开始...")

    # 1. 加载已经处理过的新闻ID
    processed_ids = state_manager.load_processed_ids()
    logging.info(f"已加载 {len(processed_ids)} 个已处理的新闻ID。")

    # 2. 获取最新新闻
    articles = news_fetcher.fetch_latest_news()
    if not articles:
        logging.info("任务结束: 没有从API获取到新闻。")
        return

    # 3. 过滤掉已经处理过的新闻
    new_articles = [
        article for article in articles if article.get("id") not in processed_ids
    ]

    if not new_articles:
        logging.info("所有获取到的新闻都已被处理过，任务结束。")
        return

    # --- 分批处理逻辑 ---
    chunk_size = 5
    article_chunks = [
        new_articles[i:i + chunk_size]
        for i in range(0, len(new_articles), chunk_size)
    ]
    total_batches = len(article_chunks)
    logging.info(f"发现 {len(new_articles)} 条新文章，将分 {total_batches} 批进行处理...")

    for i, chunk in enumerate(article_chunks):
        current_batch = i + 1
        logging.info("=" * 50)
        logging.info(f"正在处理第 {current_batch}/{total_batches} 批，包含 {len(chunk)} 条文章...")

        # 4. 对当前批次的新闻进行批量AI分析
        analysis_results = ai_analyzer.run_analysis_pipeline(chunk)

        if not isinstance(analysis_results, list):
            logging.error(f"批次 {current_batch} 的AI分析返回结果不是列表，跳过此批次。")
            # 记录失败批次的ID，避免重复处理
            for article in chunk:
                if article.get("id"):
                    processed_ids.add(article.get("id"))
            continue

        # 过滤无效建议
        articles_map = {article["id"]: article for article in chunk}
        valid_analyses = []
        for analysis in analysis_results:
            insight = analysis.get("actionable_insight", {})
            asset = insight.get("asset", {})
            if not isinstance(insight, dict) or not isinstance(asset, dict) or not asset.get("name") or asset.get("name") == "未知":
                continue
            valid_analyses.append(analysis)

        # 6. 如果有有效建议，则为当前批次发送通知
        if valid_analyses:
            logging.info(f"批次 {current_batch} 分析完成，发现 {len(valid_analyses)} 条有效建议，准备发送通知。")
            notifier.send_summary_notification(
                valid_analyses, articles_map, batch_info=(current_batch, total_batches)
            )
        else:
            logging.info(f"批次 {current_batch} AI分析完成，但没有发现可操作的有效建议。")

        # 7. 将当前批次处理过的文章ID加入集合
        for article in chunk:
            if article.get("id"):
                processed_ids.add(article.get("id"))
    
    # 所有批次处理完毕后，统一保存状态
    state_manager.save_processed_ids(processed_ids)

    logging.info("所有批次处理完成。")
    logging.info("=" * 50 + "\n")


def run_service():
    """
    运行主服务循环
    """
    logging.info("MarketPulse服务启动...")

    # 立即执行一次任务
    run_job()

    # 设置定时任务
    schedule.every(config.NEWS_FETCH_INTERVAL).minutes.do(run_job)
    logging.info(f"调度器已设置，将每 {config.NEWS_FETCH_INTERVAL} 分钟运行一次")

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("收到终止信号，服务正在停止...")
    except Exception as e:
        logging.error(f"服务发生错误: {e}")
        raise


if __name__ == "__main__":
    # 直接运行时使用控制台输出
    setup_logging(to_console=False)
    run_service()
