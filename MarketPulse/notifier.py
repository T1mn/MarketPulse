import logging
import time
import urllib.parse
from datetime import datetime, timedelta

import pytz
import requests

from MarketPulse import config, state_manager


def format_datetime(timestamp):
    """将Unix时间戳转换为中国上海时区的可读日期时间格式"""
    if not isinstance(timestamp, (int, float)) or timestamp == 0:
        return "未知时间"
    try:
        # 创建UTC时间
        utc_dt = datetime.fromtimestamp(timestamp, tz=pytz.UTC)
        # 转换为上海时区
        shanghai_tz = pytz.timezone("Asia/Shanghai")
        shanghai_dt = utc_dt.astimezone(shanghai_tz)
        return shanghai_dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print(f"时间转换错误: {e}")
        return "转换出错"


def send_summary_notification(valid_analyses, articles_map):
    """
    将所有有效的分析结果汇总成单条消息，并通过Bark和PushPlus发送。
    """
    if not valid_analyses:
        logging.info("没有有效的分析结果可以发送。")
        return

    # --- 统一构建消息内容 ---
    title = f"📈 MarketPulse - {len(valid_analyses)}条市场洞察"
    body_parts = []
    for analysis in valid_analyses:
        summary = analysis.get("summary", "无摘要")
        insight = analysis.get("actionable_insight", {})
        asset = insight.get("asset", {})
        source_confidence = analysis.get("source_confidence", "未知")

        article_id = analysis.get("id")
        article_info = articles_map.get(article_id, {})
        source_medium = article_info.get("source", "未知来源")
        source_url = article_info.get("url", "无链接")

        asset_name = asset.get("name", "未知资产")
        asset_ticker = asset.get("ticker", "")
        action = insight.get("action", "无建议")

        is_top_tier = source_medium in config.TOP_TIER_NEWS_SOURCES
        star_emoji = "⭐️ " if is_top_tier else ""

        suggestion_title = f"{star_emoji}▶︎ {action} {asset_name}"
        if asset_ticker and asset_ticker != "未知":
            suggestion_title += f" ({asset_ticker})"
        body_parts.append(suggestion_title)

        body_parts.append(f"   摘要: {summary}")
        reasoning = insight.get("reasoning", "无")
        confidence = insight.get("confidence", "未知")
        body_parts.append(f"   原因: {reasoning}")
        body_parts.append(
            f"   判断可信度: {confidence} | 来源可信度: {source_confidence}"
        )
        body_parts.append(f"   来源: {source_medium}")
        body_parts.append(f"   链接: {source_url}")
        body_parts.append("")

    body_text = "\n".join(body_parts)

    # --- Bark 推送 (使用POST) ---
    if config.BARK_KEYS:
        success_count = 0
        payload = {
            "title": title,
            "body": body_text,
            "group": config.BARK_GROUP
        }
        for bark_key in config.BARK_KEYS:
            try:
                bark_url = f"https://api.day.app/{bark_key}"
                response = requests.post(bark_url, json=payload)
                response.raise_for_status()
                success_count += 1
            except requests.RequestException as e:
                logging.warning(f"向设备 {bark_key[:5]}... 发送Bark通知失败: {e}")

        if success_count > 0:
            logging.info(f"Bark通知发送成功！ (发送到 {success_count} 个设备)")

    # --- PushPlus 推送 (使用POST) ---
    if config.PUSHPLUS_TOKEN:
        # 检查是否处于限制状态
        app_state = state_manager.load_state()
        restricted_until = app_state.get("pushplus_restricted_until", 0)

        if time.time() < restricted_until:
            restricted_time_str = format_datetime(restricted_until)
            logging.warning(f"PushPlus因发送频率过高被限制，将在 {restricted_time_str} 后恢复。")
        else:
            try:
                body_html = body_text.replace("\n", "<br/>")
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
                    logging.error("PushPlus通知失败: 用户账号因请求次数过多受限。将在6小时后重试。")
                    app_state["pushplus_restricted_until"] = (datetime.now() + timedelta(hours=6)).timestamp()
                    state_manager.save_state(app_state)
                elif result.get("code") != 200:
                    logging.error(f"PushPlus通知发送失败: {result.get('msg')}")

            except requests.RequestException as e:
                logging.error(f"发送PushPlus通知失败: {e}")
            except Exception as e:
                logging.error(f"处理PushPlus响应时出错: {e}")
