"""监控指标收集"""
import logging
from prometheus_client import Counter, Histogram, Gauge, Info
import time

logger = logging.getLogger(__name__)


# ==================== 应用信息 ====================

app_info = Info('marketpulse_app', 'MarketPulse application info')
app_info.info({
    'version': '2.0.0',
    'environment': 'production'
})


# ==================== 请求指标 ====================

# 请求总数
http_requests_total = Counter(
    'marketpulse_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# 请求延迟
http_request_duration_seconds = Histogram(
    'marketpulse_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)


# ==================== Chatbot 指标 ====================

# 对话总数
chatbot_conversations_total = Counter(
    'marketpulse_chatbot_conversations_total',
    'Total chatbot conversations',
    ['agent', 'intent', 'language']
)

# 意图识别准确率（需要人工标注）
chatbot_intent_accuracy = Gauge(
    'marketpulse_chatbot_intent_accuracy',
    'Intent recognition accuracy',
    ['language']
)

# NLU 置信度分布
chatbot_nlu_confidence = Histogram(
    'marketpulse_chatbot_nlu_confidence',
    'NLU confidence distribution',
    buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0]
)

# 用户自助率
chatbot_self_service_rate = Gauge(
    'marketpulse_chatbot_self_service_rate',
    'User self-service rate (no human intervention needed)'
)

# 活跃会话数
chatbot_active_sessions = Gauge(
    'marketpulse_chatbot_active_sessions',
    'Number of active chat sessions'
)


# ==================== LLM 指标 ====================

# LLM 调用总数
llm_requests_total = Counter(
    'marketpulse_llm_requests_total',
    'Total LLM API requests',
    ['provider', 'model', 'status']
)

# LLM 延迟
llm_request_duration_seconds = Histogram(
    'marketpulse_llm_request_duration_seconds',
    'LLM request duration in seconds',
    ['provider', 'model'],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

# LLM 成本
llm_cost_usd_total = Counter(
    'marketpulse_llm_cost_usd_total',
    'Total LLM API cost in USD',
    ['provider', 'model']
)

# LLM Token 使用
llm_tokens_total = Counter(
    'marketpulse_llm_tokens_total',
    'Total LLM tokens used',
    ['provider', 'model', 'type']  # type: input/output
)

# 缓存命中率
llm_cache_hit_rate = Gauge(
    'marketpulse_llm_cache_hit_rate',
    'LLM cache hit rate'
)


# ==================== RAG 指标 ====================

# 检索请求总数
rag_retrieval_total = Counter(
    'marketpulse_rag_retrieval_total',
    'Total RAG retrieval requests',
    ['intent']
)

# 检索延迟
rag_retrieval_duration_seconds = Histogram(
    'marketpulse_rag_retrieval_duration_seconds',
    'RAG retrieval duration in seconds',
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0]
)

# 知识库文档总数
rag_documents_total = Gauge(
    'marketpulse_rag_documents_total',
    'Total documents in knowledge base'
)

# 检索相关性分数
rag_relevance_score = Histogram(
    'marketpulse_rag_relevance_score',
    'RAG retrieval relevance score',
    buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)


# ==================== 系统指标 ====================

# 系统健康状态
system_healthy = Gauge(
    'marketpulse_system_healthy',
    'System health status (1=healthy, 0=unhealthy)'
)

# 组件状态
component_status = Gauge(
    'marketpulse_component_status',
    'Component health status (1=up, 0=down)',
    ['component']
)


# ==================== 辅助函数 ====================

class MetricsTracker:
    """指标追踪器"""

    @staticmethod
    def track_http_request(method: str, endpoint: str, status: int, duration: float):
        """追踪 HTTP 请求"""
        http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
        http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)

    @staticmethod
    def track_conversation(agent: str, intent: str, language: str, confidence: float):
        """追踪对话"""
        chatbot_conversations_total.labels(agent=agent, intent=intent, language=language).inc()
        chatbot_nlu_confidence.observe(confidence)

    @staticmethod
    def track_llm_request(provider: str, model: str, status: str, duration: float, cost: float, tokens_in: int, tokens_out: int):
        """追踪 LLM 请求"""
        llm_requests_total.labels(provider=provider, model=model, status=status).inc()
        llm_request_duration_seconds.labels(provider=provider, model=model).observe(duration)
        llm_cost_usd_total.labels(provider=provider, model=model).inc(cost)
        llm_tokens_total.labels(provider=provider, model=model, type='input').inc(tokens_in)
        llm_tokens_total.labels(provider=provider, model=model, type='output').inc(tokens_out)

    @staticmethod
    def track_rag_retrieval(intent: str, duration: float, relevance: float):
        """追踪 RAG 检索"""
        rag_retrieval_total.labels(intent=intent).inc()
        rag_retrieval_duration_seconds.observe(duration)
        rag_relevance_score.observe(relevance)

    @staticmethod
    def update_system_metrics(active_sessions: int, documents_count: int, cache_hit_rate: float):
        """更新系统指标"""
        chatbot_active_sessions.set(active_sessions)
        rag_documents_total.set(documents_count)
        llm_cache_hit_rate.set(cache_hit_rate)


# 全局追踪器实例
metrics_tracker = MetricsTracker()
