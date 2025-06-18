import json

from google import genai

from MarketPulse import config


def analyze_news_in_batch(articles):
    """
    使用Gemini批量分析新闻文章集合，并返回一个结构化的JSON数组。
    """
    if not articles:
        return []

    try:
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        model = (
            "gemini-2.5-flash-preview-05-20"  # 使用支持更大上下文和JSON模式的先进模型
        )

        # 为每个文章创建一个简洁的输入表示
        input_articles_str = json.dumps(
            [
                {
                    "id": article.get("id"),
                    "title": article.get("title", ""),
                    "content": article.get("content", ""),
                    "source": article.get("source", ""),
                }
                for article in articles
            ],
            indent=2,
            ensure_ascii=False,
        )

        prompt = f"""
        你是一位顶级的金融分析师。请基于以下JSON格式的新闻文章列表，为每一篇文章提供独立的、专业的市场分析和投资建议。
        请严格按照指定的JSON数组格式输出你的分析结果，不要添加任何额外的解释或说明文字。

        新闻文章列表:
        {input_articles_str}

        请为列表中的每一篇文章生成一个对应的JSON对象，并把所有对象放入一个JSON数组中。
        每个JSON对象的格式严格按照如下格式输出:
        {{
            "id": "对应输入文章的ID",
            "summary": "用一句话精准总结这则新闻的核心要点，突出最重要的信息。",
            "source_confidence": "基于新闻来源的声誉和常见可靠性，以百分比形式（例如：85%）评估其可信度。如果不明确，写'未知'。",
            "market_impact": {{
                "market": "分析此新闻主要影响哪个市场（例如：美股科技板块、原油市场、加密货币、中国A股等）。如果不明确，写'未知'。",
                "impact_level": "评估影响程度（高、中、低）。如果不明确，写'未知'。"
            }},
            "actionable_insight": {{
                "asset": {{
                    "name": "直接相关的股票名称或金融产品（例如：苹果公司、比特币）。如果不明确，写'未知'。",
                    "ticker": "对应的股票代码或产品代码（例如：AAPL, BTC-USD）。如果不明确，写'未知'。"
                }},
                "action": "基于此新闻，建议的操作方向（做多, 做空, 观望）。如果不明确，写'未知'。",
                "reasoning": "简要解释你提出此操作建议的逻辑和原因（不超过50字）。如果不明确，写'未知'。",
                "confidence": "以百分比形式（例如：85%）给出你对此判断的信心水平。如果不明确，写'未知'。"
            }}
        }}

        重要提示:
        1. 最终输出必须是一个完整的JSON数组，以 `[` 开始，以 `]` 结束。
        2. 如果某项分析不明确或无法确定，请使用 "未知" 作为值。
        3. 确保每个输出的JSON对象中的 `id` 字段与输入文章的 `id` 完全对应。
        4. 请使用中文进行分析。
        """

        response = client.models.generate_content(model=model, contents=prompt)
        # 兼容 Gemini 可能返回的 markdown 代码块
        clean_json_str = response.text.strip().replace("```json", "").replace("```", "")
        analysis_results = json.loads(clean_json_str)
        return analysis_results
    except Exception as e:
        print(f"AI批量分析失败: {e}")
        if "response" in locals() and hasattr(response, "prompt_feedback"):
            print(f"Prompt Feedback: {response.prompt_feedback}")
        return []
