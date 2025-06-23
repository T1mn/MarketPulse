import json
import logging
from abc import ABC, abstractmethod

from google import genai

from MarketPulse import config


class AIBaseAnalyst(ABC):
    """
    一个抽象基类，用于所有AI分析师。
    它负责初始化客户端和封装通用的API调用逻辑。
    """

    def __init__(self):
        """在基类中注册和初始化API客户端。"""
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.model_name = ""  # 将由子类定义

    @abstractmethod
    def _create_prompt(self, articles: list) -> str:
        """子类必须实现此方法来创建它们特定的提示。"""
        pass

    def run(self, articles: list):
        """
        运行分析的核心方法。
        它创建提示，调用AI，并处理响应。
        """
        if not articles:
            return None

        prompt = self._create_prompt(articles)

        try:
            logging.info(f"向AI模型 '{self.model_name}' 发送请求...")
            # 使用 client.generate_content，功能与您期望的完全一致
            response = self.client.models.generate_content(
                model=self.model_name, contents=prompt
            )

            clean_json_str = (
                response.text.strip().replace("```json", "").replace("```", "")
            )
            analysis_results = json.loads(clean_json_str)
            logging.info(f"成功从AI模型 '{self.model_name}' 接收并解析了响应。")
            return analysis_results

        except json.JSONDecodeError as e:
            logging.error(
                f"AI响应JSON解析失败: {e}. 响应内容: '{response.text[:200]}...'"
            )
            return None
        except Exception as e:
            logging.error(f"调用AI模型 '{self.model_name}' 时发生未知错误: {e}")
            if "response" in locals() and hasattr(response, "prompt_feedback"):
                logging.error(f"Prompt Feedback: {response.prompt_feedback}")
            return None


class InformationExtractor(AIBaseAnalyst):
    """信息提取分析师，负责生成简短摘要。"""

    def __init__(self):
        super().__init__()
        self.model_name = "gemini-1.5-flash"

    def _create_prompt(self, articles: list) -> str:
        input_articles_str = json.dumps(
            [
                {
                    "id": article.get("id"),
                    "title": article.get("title", ""),
                    "content": article.get("content", ""),
                }
                for article in articles
            ],
            indent=2,
            ensure_ascii=False,
        )
        return f"""
        你是一个高效的信息提取专家。请为以下新闻列表中的每一篇文章生成一个不超过50字的精炼摘要。
        新闻文章列表: {input_articles_str}
        请严格按照以下JSON数组格式返回结果，每个对象包含文章的`id`和你的`summary`。
        [
          {{"id": "...", "summary": "..."}}
        ]
        """


class MarketAnalyst(AIBaseAnalyst):
    """市场分析师，负责进行深入的金融分析。"""

    def __init__(self):
        super().__init__()
        self.model_name = "gemini-2.0-flash-lite"

    def _create_prompt(self, articles: list) -> str:
        input_articles_str = json.dumps(
            [
                {
                    "id": article.get("id"),
                    "title": article.get("title", ""),
                    "content": article.get("content", ""),  # 此处内容是精简摘要
                    "source": article.get("source", ""),
                }
                for article in articles
            ],
            indent=2,
            ensure_ascii=False,
        )
        return f"""
        你是一位顶级的金融分析师。请基于以下JSON格式的新闻文章列表，为每一篇文章提供独立的、专业的市场分析和投资建议。
        请严格按照指定的JSON数组格式输出你的分析结果。

        新闻文章列表:
        {input_articles_str}

        请为列表中的每一篇文章生成一个对应的JSON对象，并把所有对象放入一个JSON数组中。
        每个JSON对象的格式严格按照如下格式输出:
        {{
            "id": "对应输入文章的ID",
            "summary": "用一句话精准总结这则新闻的核心要点，突出最重要的信息。",
            "source_confidence": "基于新闻来源的声誉和常见可靠性，以百分比形式（例如：85%）评估其可信度。如果不明确，写'未知'。",
            "market_impact": {{"market": "...", "impact_level": "..."}},
            "actionable_insight": {{
                "asset": {{"name": "...", "ticker": "..."}},
                "action": "做多或做空或观望",
                "reasoning": "...",
                "confidence": "0-100%的信心"
            }}
        }}

        ---
        ### 特别指令：顶级新闻社VIP分析标准
        对于来源为以下列表中的新闻，你的分析必须遵循更高标准：
        - **顶级新闻社列表**: {list(config.TOP_TIER_NEWS_SOURCES)}
        - **市场影响分析**: 必须给出最具体的影响范围，严禁使用模糊词汇。
        - **来源可信度**: 必须给出95%-100%之间的一个具体数值。
        ---
        """


def run_analysis_pipeline(articles: list):
    """
    运行完整的AI分析流水线：提取 -> 分析。
    这是外部模块调用的唯一入口。
    """
    logging.info("启动信息提取流程...")
    extractor = InformationExtractor()
    summaries = extractor.run(articles)

    if not isinstance(summaries, list):
        logging.error("信息提取步骤未能返回有效列表，中止本次任务。")
        return None

    # 将摘要更新回文章列表，为市场分析师准备输入
    summaries_map = {
        item["id"]: item["summary"] for item in summaries if isinstance(item, dict)
    }
    updated_articles = []
    for article in articles:
        new_article = article.copy()
        if new_article.get("id") in summaries_map:
            new_article["content"] = summaries_map[new_article["id"]]
            # logging.info(f"文章(ID: {new_article['id']})内容已更新为摘要。")
        updated_articles.append(new_article)

    logging.info("信息提取完成，启动市场分析流程...")
    analyst = MarketAnalyst()
    market_analyses = analyst.run(updated_articles)

    return market_analyses


class SummaryGenerator(AIBaseAnalyst):
    """总结归纳师，负责将分析结果汇总成精炼的摘要。"""

    def __init__(self):
        super().__init__()
        # 用户指定使用 gemini-2.0-flash-lite，我们使用最接近的 gemini-1.5-flash
        self.model_name = "gemini-1.5-flash"

    def _create_prompt(self, content: str) -> str:
        return f"""
        你是一个专业的市场评论员。请将以下市场分析内容总结归纳在100字以内，提取最核心的投资洞见。
        你的总结需要精炼、专业、直击要点。

        待总结的内容:
        ---
        {content}
        ---

        请直接返回总结内容，不要包含任何其他说明或标题。
        """

    def run(self, content: str):
        """
        重写 run 方法以接受字符串内容。
        """
        if not content:
            return "没有发现需要总结的内容。"

        prompt = self._create_prompt(content)

        try:
            logging.info(f"向AI模型 '{self.model_name}' 发送总结请求...")
            response = self.client.models.generate_content(
                model=self.model_name, contents=prompt
            )
            summary = response.text.strip()
            logging.info("成功生成市场分析总结。")
            return summary

        except Exception as e:
            logging.error(f"调用AI模型 '{self.model_name}' 进行总结时发生错误: {e}")
            if "response" in locals() and hasattr(response, "prompt_feedback"):
                logging.error(f"Prompt Feedback: {response.prompt_feedback}")
            return "AI总结生成失败。"


def run_summary_pipeline(content: str) -> str:
    """
    运行总结归纳流水线。
    这是外部模块调用的唯一入口。
    """
    logging.info("启动总结归纳流程...")
    generator = SummaryGenerator()
    summary = generator.run(content)
    return summary
