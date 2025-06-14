import urllib.parse
from datetime import datetime

import pytz
import requests

import config


def format_datetime(timestamp):
    """将Unix时间戳转换为中国上海时区的可读日期时间格式"""
    try:
        # 创建UTC时间
        utc_dt = datetime.fromtimestamp(timestamp, tz=pytz.UTC)
        # 转换为上海时区
        shanghai_tz = pytz.timezone("Asia/Shanghai")
        shanghai_dt = utc_dt.astimezone(shanghai_tz)
        return shanghai_dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print(f"时间转换错误: {e}")
        return None


def send_bark_notification(
    analysis_data,
    article_url,
    article_source=None,
    related_symbols=None,
    article_datetime=None,
):
    """
    将分析结果通过Bark发送通知到所有配置的设备。

    Args:
        analysis_data (dict): AI分析后的结构化数据。
        article_url (str): 原始新闻的URL，用于点击跳转。
        article_source (str): 新闻来源。
        related_symbols (list): 相关股票代码列表。
        article_datetime (int): 新闻发布时间戳（秒）。
    """
    try:
        insight = analysis_data.get("actionable_insight", {})
        asset = insight.get("asset", {})
        impact = analysis_data.get("market_impact", {})

        # 构建标题：来源 + 新闻核心要点
        source_info = f"[{article_source}]" if article_source else ""
        title = f"{source_info} {analysis_data.get('summary', '无摘要')}"

        # 构建正文，使用清晰的格式
        body_parts = []

        # 添加新闻时间
        if article_datetime:
            formatted_time = format_datetime(article_datetime)
            if formatted_time:
                body_parts.append(f"新闻时间：{formatted_time}")

        # 市场影响部分
        if impact:
            body_parts.append("\n市场影响：")
            if impact.get("market"):
                body_parts.append(f"- 影响市场：{impact.get('market')}")
            if impact.get("impact_level"):
                body_parts.append(f"- 影响程度：{impact.get('impact_level')}")

        # 操作建议部分
        if asset.get("name") != "未知":
            body_parts.append("\n操作建议：")
            if asset.get("name"):
                body_parts.append(f"- 相关资产：{asset.get('name')}")
            if asset.get("ticker") and asset.get("ticker") != "未知":
                body_parts.append(f"- 资产代码：{asset.get('ticker')}")
            if insight.get("action"):
                body_parts.append(f"- 建议操作：{insight.get('action')}")
            if insight.get("reasoning"):
                body_parts.append(f"- 操作理由：{insight.get('reasoning')}")
            if insight.get("confidence"):
                body_parts.append(f"- 信心水平：{insight.get('confidence')}")

        # 相关股票信息
        if related_symbols:
            body_parts.append("\n相关股票：")
            body_parts.append(", ".join(related_symbols))

        # 组合所有内容
        body = "\n".join(body_parts)

        # Bark API对URL中的特殊字符敏感，需要进行编码
        title_encoded = urllib.parse.quote(title)
        body_encoded = urllib.parse.quote(body)

        # 构建基础URL参数
        base_params = f"group={config.BARK_GROUP}&url={article_url}"

        # 向所有配置的设备发送通知
        success_count = 0
        for bark_key in config.BARK_KEYS:
            try:
                # 构建完整的Bark URL
                bark_url = f"https://api.day.app/{bark_key}/{title_encoded}/{body_encoded}?{base_params}"

                print(f"正在发送Bark通知到设备: {bark_key}")
                response = requests.get(bark_url)
                response.raise_for_status()
                success_count += 1
            except Exception as e:
                print(f"向设备 {bark_key} 发送通知失败: {e}")

        if success_count > 0:
            print(
                f"Bark通知发送成功！成功发送到 {success_count}/{len(config.BARK_KEYS)} 个设备"
            )
        else:
            print("所有设备通知发送失败！")

    except Exception as e:
        print(f"构建通知时发生错误: {e}")
