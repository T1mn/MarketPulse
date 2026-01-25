"""Chatbot 配置"""
from typing import Dict, List
from pydantic import BaseModel


class IntentConfig(BaseModel):
    """意图配置"""
    name: str
    description: str
    examples: List[str]
    required_entities: List[str] = []
    agent: str  # 处理该意图的 Agent


class ChatbotConfig(BaseModel):
    """Chatbot 总体配置"""

    # ==================== NLU 配置 ====================
    # 意图识别置信度阈值
    intent_confidence_threshold: float = 0.7

    # 实体提取置信度阈值
    entity_confidence_threshold: float = 0.6

    # 支持的语言
    supported_languages: List[str] = ["zh-CN", "en", "zh-TW"]

    # 默认语言
    default_language: str = "zh-CN"

    # ==================== 对话管理配置 ====================
    # 最大对话轮次
    max_dialogue_turns: int = 20

    # 会话超时时间（秒）
    session_timeout: int = 1800  # 30分钟

    # 上下文窗口大小
    context_window_size: int = 10

    # ==================== Agent 配置 ====================
    # 启用的 Agents
    enabled_agents: List[str] = [
        "customer_service",
        "market_analysis",
        "trading_assistant",
        "workflow_automation",
    ]

    # Agent 超时时间（秒）
    agent_timeout: int = 30

    # ==================== RAG 配置 ====================
    # 检索 Top-K
    retrieval_top_k: int = 5

    # 重排序 Top-N
    rerank_top_n: int = 3

    # 相似度阈值
    similarity_threshold: float = 0.7

    # ==================== 意图定义 ====================
    intents: Dict[str, IntentConfig] = {
        "market_query": IntentConfig(
            name="market_query",
            description="查询市场行情、股价、指数等",
            examples=[
                "特斯拉现在多少钱？",
                "今天美股怎么样？",
                "帮我查一下比特币价格",
                "纳斯达克指数",
            ],
            required_entities=["asset"],
            agent="market_analysis",
        ),
        "news_analysis": IntentConfig(
            name="news_analysis",
            description="分析金融新闻、解读市场事件",
            examples=[
                "帮我分析一下最新的美联储会议",
                "特斯拉的新闻有什么影响？",
                "今天有什么重要财经新闻？",
            ],
            required_entities=[],
            agent="market_analysis",
        ),
        "trade_execute": IntentConfig(
            name="trade_execute",
            description="执行交易、下单、止损等",
            examples=[
                "帮我买入100股苹果",
                "卖出我持有的特斯拉",
                "设置止损价",
            ],
            required_entities=["asset", "action", "quantity"],
            agent="trading_assistant",
        ),
        "account_inquiry": IntentConfig(
            name="account_inquiry",
            description="查询账户信息、持仓、收益等",
            examples=[
                "我的账户余额是多少？",
                "查看我的持仓",
                "今天收益怎么样？",
            ],
            required_entities=[],
            agent="trading_assistant",
        ),
        "risk_alert": IntentConfig(
            name="risk_alert",
            description="风险提示、预警、安全建议",
            examples=[
                "这个股票有什么风险？",
                "帮我评估一下风险",
                "现在投资安全吗？",
            ],
            required_entities=["asset"],
            agent="trading_assistant",
        ),
        "crypto_price": IntentConfig(
            name="crypto_price",
            description="查询加密货币价格行情",
            examples=[
                "BTC现在多少钱？",
                "比特币价格",
                "ETH行情",
                "以太坊多少钱",
                "查一下比特币",
            ],
            required_entities=["symbol"],
            agent="trading_assistant",
        ),
        "crypto_analysis": IntentConfig(
            name="crypto_analysis",
            description="加密货币K线分析、趋势分析",
            examples=[
                "BTC的K线走势",
                "分析一下比特币趋势",
                "ETH 4小时K线",
                "比特币日线分析",
            ],
            required_entities=["symbol"],
            agent="trading_assistant",
        ),
        "customer_service": IntentConfig(
            name="customer_service",
            description="客服咨询、问题反馈、使用帮助",
            examples=[
                "怎么充值？",
                "如何修改密码？",
                "我有个问题",
                "客服在吗？",
            ],
            required_entities=[],
            agent="customer_service",
        ),
        "workflow_automation": IntentConfig(
            name="workflow_automation",
            description="自动化任务、定时提醒、策略设置",
            examples=[
                "每天早上提醒我看盘",
                "特斯拉跌到200美元提醒我",
                "设置自动定投",
            ],
            required_entities=["task_type"],
            agent="workflow_automation",
        ),
        "greeting": IntentConfig(
            name="greeting",
            description="问候、寒暄",
            examples=[
                "你好",
                "hi",
                "早上好",
            ],
            required_entities=[],
            agent="customer_service",
        ),
        "chitchat": IntentConfig(
            name="chitchat",
            description="闲聊、非金融相关话题",
            examples=[
                "今天天气怎么样？",
                "你是谁？",
                "讲个笑话",
            ],
            required_entities=[],
            agent="customer_service",
        ),
    }

    # ==================== 实体定义 ====================
    entity_types: Dict[str, Dict] = {
        "asset": {
            "description": "金融资产（股票、指数、加密货币等）",
            "examples": ["AAPL", "苹果", "特斯拉", "比特币", "纳斯达克"],
        },
        "symbol": {
            "description": "加密货币交易对符号",
            "examples": ["BTC", "ETH", "BTCUSDT", "ETHUSDT", "比特币", "以太坊"],
        },
        "interval": {
            "description": "K线周期",
            "examples": ["1m", "15m", "1h", "4h", "1d", "1小时", "4小时", "日线"],
        },
        "action": {
            "description": "交易动作",
            "examples": ["买入", "卖出", "持有", "止损", "止盈"],
        },
        "quantity": {
            "description": "数量",
            "examples": ["100股", "全部", "一半", "50%"],
        },
        "price": {
            "description": "价格",
            "examples": ["200美元", "$150", "市价"],
        },
        "time": {
            "description": "时间",
            "examples": ["明天", "下周", "2024-01-20", "每天早上9点"],
        },
        "task_type": {
            "description": "任务类型",
            "examples": ["提醒", "定投", "监控"],
        },
    }

    # ==================== 响应配置 ====================
    # 默认响应模板
    default_responses: Dict[str, List[str]] = {
        "greeting": [
            "您好！我是 MarketPulse AI，您的金融智能助手。有什么可以帮您的吗？",
            "Hi！很高兴为您服务，请问有什么金融问题需要咨询？",
        ],
        "fallback": [
            "抱歉，我没有完全理解您的意思。您可以换个方式问我，或者说'帮助'查看我能做什么。",
            "我可能没理解对，能再详细说说吗？",
        ],
        "error": [
            "抱歉，系统出现了一点问题，请稍后重试。",
        ],
        "clarification": [
            "您是想问关于 {asset} 的 {intent} 吗？",
        ],
    }

    # ==================== 性能配置 ====================
    # 并发请求限制
    max_concurrent_requests: int = 100

    # 单用户请求速率限制（请求/分钟）
    rate_limit_per_user: int = 60

    # 响应延迟告警阈值（秒）
    latency_alert_threshold: float = 5.0


# 全局 Chatbot 配置实例
chatbot_config = ChatbotConfig()
