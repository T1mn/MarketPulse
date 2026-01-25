"""Prompt 管理器"""
from typing import Dict, Optional
from datetime import datetime
from jinja2 import Template

from config import llm_config


class PromptManager:
    """
    Prompt 工程管理

    功能：
    1. 模板化 Prompt 管理
    2. 多语言支持
    3. 场景化 Prompt 库
    4. 动态参数注入
    """

    def __init__(self):
        self.templates: Dict[str, Template] = {}
        self._init_templates()

    def _init_templates(self):
        """初始化 Prompt 模板"""

        # 系统 Prompt
        self.templates["system"] = Template(llm_config.system_prompt_template)

        # NLU 意图识别
        self.templates["nlu_intent"] = Template("""
你是一个专业的意图识别专家。

可能的意图类别：
{% for intent_name, intent in intents.items() %}
- {{ intent_name }}: {{ intent.description }}
  示例：{{ intent.examples|join(', ') }}
{% endfor %}

对话历史：
{% for msg in context %}
{{ msg.role }}: {{ msg.content }}
{% endfor %}

用户输入：{{ user_input }}

请识别用户意图，返回 JSON 格式：
{
    "intent": "intent_name",
    "confidence": 0.95,
    "reasoning": "识别理由",
    "entities": {}
}
""")

        # 实体提取
        self.templates["nlu_entity"] = Template("""
从以下文本中提取实体信息。

实体类型：
{% for entity_type, entity_info in entity_types.items() %}
- {{ entity_type }}: {{ entity_info.description }}
  示例：{{ entity_info.examples|join(', ') }}
{% endfor %}

文本：{{ text }}

返回 JSON 格式：
{
    "entities": [
        {
            "type": "entity_type",
            "value": "entity_value",
            "confidence": 0.9
        }
    ]
}
""")

        # 市场分析
        self.templates["market_analysis"] = Template("""
你是一位资深的金融分析师。请分析以下市场信息。

{% if news_context %}
相关新闻：
{{ news_context }}
{% endif %}

{% if market_data %}
市场数据：
{{ market_data }}
{% endif %}

用户问题：{{ query }}

请提供专业的分析，包括：
1. 市场现状
2. 潜在影响
3. 投资建议
4. 风险提示
""")

        # 客服响应
        self.templates["customer_service"] = Template("""
你是 MarketPulse 的客服专员，友好、专业、高效。

用户问题：{{ question }}

{% if knowledge_base %}
参考知识库：
{{ knowledge_base }}
{% endif %}

请提供清晰的回答。如果不确定，引导用户联系人工客服。
""")

        # 交易辅助
        self.templates["trading_assistant"] = Template("""
你是一个谨慎的交易助手。

用户请求：{{ request }}

{% if account_info %}
账户信息：
{{ account_info }}
{% endif %}

{% if risk_assessment %}
风险评估：
{{ risk_assessment }}
{% endif %}

请提供：
1. 操作建议
2. 风险评估
3. 注意事项
4. 确认提示（如需）

重要：涉及实际交易时，必须明确风险并要求用户确认。
""")

    def render(
        self,
        template_name: str,
        language: str = "zh-CN",
        **kwargs
    ) -> str:
        """
        渲染 Prompt 模板

        Args:
            template_name: 模板名称
            language: 语言
            **kwargs: 模板参数

        Returns:
            str: 渲染后的 Prompt
        """
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found")

        # 添加通用参数
        kwargs["language"] = language
        kwargs["timestamp"] = datetime.now().isoformat()

        template = self.templates[template_name]
        return template.render(**kwargs)

    def get_system_prompt(self, language: str = "zh-CN") -> str:
        """获取系统 Prompt"""
        return self.render("system", language=language)

    def get_nlu_intent_prompt(
        self,
        user_input: str,
        intents: Dict,
        context: list,
        language: str = "zh-CN"
    ) -> str:
        """获取 NLU 意图识别 Prompt"""
        return self.render(
            "nlu_intent",
            user_input=user_input,
            intents=intents,
            context=context,
            language=language
        )

    def get_entity_extraction_prompt(
        self,
        text: str,
        entity_types: Dict,
        language: str = "zh-CN"
    ) -> str:
        """获取实体提取 Prompt"""
        return self.render(
            "nlu_entity",
            text=text,
            entity_types=entity_types,
            language=language
        )

    def get_market_analysis_prompt(
        self,
        query: str,
        news_context: Optional[str] = None,
        market_data: Optional[str] = None,
        language: str = "zh-CN"
    ) -> str:
        """获取市场分析 Prompt"""
        return self.render(
            "market_analysis",
            query=query,
            news_context=news_context,
            market_data=market_data,
            language=language
        )


# 全局 Prompt 管理器实例
prompt_manager = PromptManager()
