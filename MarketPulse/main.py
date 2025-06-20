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

    logging.info(f"发现 {len(new_articles)} 条新文章，正在进行AI批量分析...")

    # 4. 对所有新新闻进行批量AI分析
    analysis_results = ai_analyzer.analyze_news_in_batch(new_articles)

    # 类型校验和异常处理，防止AI返回格式不符导致服务崩溃
    if not isinstance(analysis_results, list):
        logging.error(
            f"AI分析返回结果不是列表: {type(analysis_results)}，内容: {analysis_results}"
        )
        # 仍然需要保存ID，避免重复分析失败的文章
        for article in new_articles:
            if article.get("id"):
                processed_ids.add(article.get("id"))
        state_manager.save_processed_ids(processed_ids)
        return

    # 为快速查找文章来源，提前创建文章ID到内容的映射
    articles_map = {article["id"]: article for article in new_articles}
    valid_analyses = []

    for idx, analysis in enumerate(analysis_results):
        if not isinstance(analysis, dict):
            logging.warning(
                f"第{idx}个AI分析结果不是字典，已跳过: {analysis} (类型: {type(analysis)})"
            )
            continue

        insight = analysis.get("actionable_insight")
        if not isinstance(insight, dict):
            logging.warning(
                f"过滤无效建议 (ID: {analysis.get('id')}), 原因: 'actionable_insight' 格式不正确 (类型: {type(insight)})"
            )
            continue

        asset = insight.get("asset")
        if not isinstance(asset, dict):
            logging.warning(
                f"过滤无效建议 (ID: {analysis.get('id')}), 原因: 'asset' 格式不正确 (类型: {type(asset)})"
            )
            continue

        asset_name = asset.get("name")
        # 如果资产名称为"未知"，则认为是无效建议，直接过滤掉
        if not asset_name or asset_name == "未知":
            logging.info(f"过滤无效建议 (ID: {analysis.get('id')}, 原因: 资产名称未知)")
            continue

        # 获取新闻来源以进行特殊处理
        article_id = analysis.get("id")
        source = articles_map.get(article_id, {}).get("source", "")

        # 过滤掉"观望"的建议，但顶级新闻源的观望建议除外
        if (
            insight.get("action") == "观望"
            and source not in config.TOP_TIER_NEWS_SOURCES
        ):
            logging.info(f"过滤非顶级源的观望建议 (ID: {article_id}, 来源: {source})")
            continue

        valid_analyses.append(analysis)

    # 6. 如果有有效建议，则汇总发送通知
    if valid_analyses:
        logging.info(f"分析完成，发现 {len(valid_analyses)} 条有效建议，准备发送通知。")
        notifier.send_summary_notification(valid_analyses, articles_map)
    else:
        logging.info("AI分析完成，但没有发现可操作的有效建议。")

    # 7. 将所有新处理的文章ID加入集合并保存
    for article in new_articles:
        if article.get("id"):
            processed_ids.add(article.get("id"))
    state_manager.save_processed_ids(processed_ids)

    logging.info("任务结束。")
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
