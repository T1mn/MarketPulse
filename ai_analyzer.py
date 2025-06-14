import json
import os

from google import genai

import config


def analyze_news_article(article):
    """使用Gemini分析新闻并返回结构化JSON"""
    try:
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        model = "gemini-2.5-flash-preview-05-20"

        prompt = f"""
        你是一位专业的金融分析师。请基于以下新闻内容，提供专业的市场分析和投资建议。请严格按照指定的JSON格式输出你的分析结果，不要添加任何额外的解释或说明文字。

        新闻原文：
        标题："{article.get('title', '')}"
        摘要："{article.get('content', '')}"

        请生成如下JSON格式的分析报告：

        {{
        "summary": "用一句话精准总结这则新闻的核心要点，突出最重要的信息。",
        "market_impact": {{
            "market": "分析此新闻主要影响哪个市场（例如：美股科技板块、原油市场、加密货币、中国A股等常见市场）。如果不明确，写'未知'。",
            "impact_level": "评估影响程度（高、中、低）。如果不明确，写'未知'。"
        }},
        "actionable_insight": {{
            "asset": {{
                "name": "直接相关的股票名称或金融产品（例如：苹果公司、WTI原油期货、比特币）。如果不明确，写'未知'。",
                "ticker": "对应的股票代码或产品代码（例如：AAPL, CL=F, BTC-USD）。如果不明确，写'未知'。"
            }},
            "action": "基于此新闻，建议的操作方向（做多, 做空, 观望）。如果不明确，写'未知'。",
            "reasoning": "简要解释你提出此操作建议的逻辑和原因（不超过50字）。如果不明确，写'未知'。",
            "confidence": "给出你对此判断的信心水平（高、中、低）。如果不明确，写'未知'。"
        }}
        }}

        注意：
        1. 如果某项分析不明确或无法确定，请使用"不适用"而不是随意猜测
        2. 确保summary简洁明了，突出新闻要点
        3. 分析要客观专业，避免过度解读
        4. 请严格按照指定的JSON格式输出你的分析结果，不要添加任何额外的解释或说明文字, 使用语言为中文。
        """

        response = client.models.generate_content(model=model, contents=prompt)
        clean_json_str = response.text.strip().replace("```json", "").replace("```", "")
        analysis_result = json.loads(clean_json_str)
        return analysis_result
    except Exception as e:
        print(f"AI分析失败: {str(e)}")
        return None
