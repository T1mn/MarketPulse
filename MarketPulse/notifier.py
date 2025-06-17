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
    将所有有效的分析结果汇总成多条通知发送，并处理URL过长、API限制等问题。
    """
    if not valid_analyses:
        logging.info("没有有效的分析结果可以发送。")
        return

    # 定义一个保守的、适用于URL的单个消息体最大长度
    MAX_BODY_LENGTH = 1500
    batches = []
    current_batch_analyses = []
    current_length = 0

    for analysis in valid_analyses:
        # ---- 估算单条分析的文本长度 ----
        article_info = articles_map.get(analysis.get("id"), {})
        # 这是一个粗略但有效的估算，避免URL过长
        item_length = len(str(analysis)) + len(str(article_info)) + 50

        if current_batch_analyses and current_length + item_length > MAX_BODY_LENGTH:
            batches.append(current_batch_analyses)
            current_batch_analyses = []
            current_length = 0

        current_batch_analyses.append(analysis)
        current_length += item_length

    if current_batch_analyses:
        batches.append(current_batch_analyses)

    total_batches = len(batches)
    if total_batches > 1:
        print(f"数据量过大，将分 {total_batches} 条消息推送。")

    # ---- 遍历所有批次并发送 ----
    for i, batch_analyses in enumerate(batches, 1):
        try:
            # 构建标题，如果有多条，则添加 "(1/N)"
            title = f"📈 MarketPulse - {len(batch_analyses)}条市场洞察"
            if total_batches > 1:
                title += f" ({i}/{total_batches})"

            # 构建正文
            body_parts = []
            for analysis in batch_analyses:
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

                suggestion_title = f"▶︎ {action} {asset_name}"
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

            body = "\n".join(body_parts)

            # --- Bark 推送 ---
            if config.BARK_KEYS:
                # URL编码，并确保'/'被正确编码，防止404错误
                title_encoded = urllib.parse.quote(title, safe="")
                body_encoded = urllib.parse.quote(body, safe="")
                base_params = f"group={config.BARK_GROUP}"
                success_count = 0
                for bark_key in config.BARK_KEYS:
                    try:
                        bark_url = f"https://api.day.app/{bark_key}/{title_encoded}/{body_encoded}?{base_params}"
                        response = requests.get(bark_url)
                        response.raise_for_status()
                        success_count += 1
                    except requests.RequestException as e:
                        logging.warning(f"向设备 {bark_key[:5]}... 发送Bark通知失败: {e}")

                if success_count > 0:
                    logging.info(f"Bark通知 (批次 {i}/{total_batches}) 发送成功！")

            # 如果有多个批次，在每次发送后稍作延迟，以避免潜在的速率限制
            if total_batches > 1:
                time.sleep(1)

        except Exception as e:
            logging.error(f"构建或发送Bark通知批次 {i}/{total_batches} 时发生错误: {e}")

    # --- PushPlus 推送 (一次性全量推送) ---
    if config.PUSHPLUS_TOKEN:
        # 检查是否处于限制状态
        app_state = state_manager.load_state()
        restricted_until = app_state.get("pushplus_restricted_until", 0)

        if time.time() < restricted_until:
            restricted_time_str = format_datetime(restricted_until)
            logging.warning(f"PushPlus因发送频率过高被限制，将在 {restricted_time_str} 后恢复。")
        else:
            try:
                # 重新构建完整的正文
                title = f"📈 MarketPulse - {len(valid_analyses)}条市场洞察"
                full_body_parts = []
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

                    suggestion_title = f"▶︎ {action} {asset_name}"
                    if asset_ticker and asset_ticker != "未知":
                        suggestion_title += f" ({asset_ticker})"
                    full_body_parts.append(suggestion_title)

                    full_body_parts.append(f"   摘要: {summary}")
                    reasoning = insight.get("reasoning", "无")
                    confidence = insight.get("confidence", "未知")
                    full_body_parts.append(f"   原因: {reasoning}")
                    full_body_parts.append(
                        f"   判断可信度: {confidence} | 来源可信度: {source_confidence}"
                    )
                    full_body_parts.append(f"   来源: {source_medium}")
                    full_body_parts.append(f"   链接: {source_url}")
                    full_body_parts.append("")
                
                body_html = "\n".join(full_body_parts).replace("\n", "<br/>")

                params = {
                    "token": config.PUSHPLUS_TOKEN,
                    "title": title,
                    "content": body_html,
                    "template": "html",
                    "topic": config.PUSHPLUS_TOPIC
                }
                response = requests.get("https://www.pushplus.plus/send", params=params)
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
