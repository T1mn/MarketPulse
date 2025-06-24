import logging
import time
from datetime import datetime, timedelta

import requests

from MarketPulse import config, state_manager
from MarketPulse.ai_analyzer import run_summary_pipeline


def format_datetime(timestamp):
    """将时间戳格式化为易于阅读的字符串"""
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def _send_bark_notification(title, body, key):
    """通过Bark发送通知"""
    try:
        logging.info(f"正在向设备 {key[:5]}... 发送Bark通知...")
        response = requests.post(
            f"https://api.day.app/{key}",
            json={
                "title": title,
                "body": body,
                "group": config.BARK_GROUP,
                "icon": "https://raw.githubusercontent.com/CRO-Manager/MarketPulse/master/img/logo.png",
                "sound": "calypso",
            },
        )
        response.raise_for_status()
        logging.info(f"向设备 {key[:5]}... 发送Bark通知成功！")
    except requests.RequestException as e:
        logging.warning(f"向设备 {key[:5]}... 发送Bark通知失败: {e}")


def _send_pushplus_notification(title, body):
    """通过PushPlus发送通知"""
    app_state = state_manager.load_state()
    restricted_until = app_state.get("pushplus_restricted_until", 0)

    if time.time() < restricted_until:
        restricted_time_str = format_datetime(restricted_until)
        logging.warning(
            f"PushPlus因发送频率过高被限制，将在 {restricted_time_str} 后恢复。"
        )
        return

    try:
        body_html = body.replace("\n", "<br/>")
        pushplus_payload = {
            "token": config.PUSHPLUS_TOKEN,
            "title": title,
            "content": body_html,
            "template": "html",
        }
        if config.PUSHPLUS_TOPIC:
            pushplus_payload["topic"] = config.PUSHPLUS_TOPIC

        response = requests.post("http://www.pushplus.plus/send", json=pushplus_payload)
        response.raise_for_status()

        result = response.json()
        if result.get("code") == 900:
            logging.error(
                "PushPlus通知失败: 用户账号因请求次数过多受限。将在6小时后重试。"
            )
            app_state["pushplus_restricted_until"] = (
                datetime.now() + timedelta(hours=6)
            ).timestamp()
            state_manager.save_state(app_state)
        elif result.get("code") != 200:
            logging.error(f"PushPlus通知发送失败: {result.get('msg')}")
        else:
            logging.info("PushPlus通知发送成功！")

    except requests.RequestException as e:
        logging.error(f"发送PushPlus通知失败: {e}")
    except Exception as e:
        logging.error(f"处理PushPlus响应时出错: {e}")


def send_summary_notification(analyses, articles_map, batch_info=(1, 1)):
    """
    汇总分析结果，并发送单一的摘要通知。
    现在支持分批发送，并能在推送前生成最终摘要。
    """
    if not analyses:
        return

    body_parts = []
    for analysis in analyses:
        article_id = analysis.get("id")
        original_article = articles_map.get(article_id, {})
        source = original_article.get("source", "未知来源")
        # url = original_article.get("url", "")  # 链接不再展示

        # 标注顶级新闻来源
        source_display = source
        if "Bloomberg" in source:
            source_display += " (顶级新闻来源)"

        insight = analysis.get("actionable_insight", {})
        asset = insight.get("asset", {})
        asset_name = asset.get("name")
        asset_ticker = asset.get("ticker")
        action = insight.get("action")
        confidence = insight.get("confidence")

        # 过滤无效建议
        if (
            not asset_name
            or asset_name == "未知资产"
            or not asset_ticker
            or not action
            or action == "无建议"
            or not confidence
            or confidence == "未知"
        ):
            logging.info(f"过滤无效建议 (ID: {article_id})，因包含无效内容。")
            continue

        # 摘要作为小标题，建议中包含资产信息
        part = (
            f"[{analysis.get('summary', 'N/A')}]\n"
            f"   - 建议: {action} {asset_name} ({asset_ticker}) (信心: {confidence})\n"
            f"   - 理由: {insight.get('reasoning', 'N/A')}\n"
            f"   - 来源: {source_display}"
        )
        body_parts.append(part)

    if not body_parts:
        logging.info("所有建议都被过滤，没有内容可推送。")
        return

    full_body = "\n\n".join(body_parts)

    # 生成最终摘要
    final_summary = run_summary_pipeline(full_body)

    final_body_with_summary = f"【AI市场洞察总结】\n{final_summary}\n\n{full_body}"

    current_batch, total_batches = batch_info
    title = config.BARK_GROUP
    if total_batches > 1:
        title += f" ({current_batch}/{total_batches})"

    # 限制推送内容长度，避免HTTP 413错误
    max_length = 3500  # Bark的实际限制约为4KB
    if len(final_body_with_summary.encode("utf-8")) > max_length:
        logging.warning("推送内容过长，将被截断。")
        # 尝试保留总结部分
        truncated_body = (
            final_body_with_summary[:max_length] + "\n...(内容过长，已被截断)"
        )
    else:
        truncated_body = final_body_with_summary

    for key in config.BARK_KEYS:
        _send_bark_notification(title, truncated_body, key)
        # 在分批推送之间增加延迟，避免过于频繁
        if total_batches > 1:
            time.sleep(2)

    if config.PUSHPLUS_TOKEN:
        _send_pushplus_notification(title, truncated_body)
