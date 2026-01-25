"""Pydantic 请求/响应模型"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ==================== Chatbot API ====================

class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(..., min_length=1, max_length=2000, description="用户消息")
    session_id: Optional[str] = Field(None, description="会话 ID，不提供则创建新会话")
    user_id: str = Field(..., description="用户 ID")
    language: Optional[str] = Field("zh-CN", description="语言")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="额外元数据")


class ChatResponse(BaseModel):
    """聊天响应"""
    content: str = Field(..., description="回复内容")
    session_id: str = Field(..., description="会话 ID")
    intent: str = Field(..., description="识别的意图")
    confidence: float = Field(..., description="置信度")
    agent: str = Field(..., description="处理的 Agent")
    entities: Dict[str, Any] = Field(default_factory=dict, description="提取的实体")
    suggested_actions: List[Dict] = Field(default_factory=list, description="建议操作")
    requires_confirmation: bool = Field(False, description="是否需要用户确认")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class ChatStreamChunk(BaseModel):
    """流式聊天响应块"""
    type: str = Field(..., description="消息类型: content/metadata/done")
    content: Optional[str] = Field(None, description="内容")
    metadata: Optional[Dict] = Field(None, description="元数据")


# ==================== 会话管理 ====================

class SessionInfo(BaseModel):
    """会话信息"""
    session_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    turn_count: int
    current_intent: Optional[str] = None


class SessionListResponse(BaseModel):
    """会话列表响应"""
    sessions: List[SessionInfo]
    total: int


# ==================== Agent 管理 ====================

class AgentInfo(BaseModel):
    """Agent 信息"""
    name: str
    description: str
    supported_intents: List[str]
    available: bool = True


class AgentListResponse(BaseModel):
    """Agent 列表响应"""
    agents: List[AgentInfo]
    total: int


# ==================== 知识库管理 ====================

class KnowledgeAddRequest(BaseModel):
    """添加知识请求"""
    content: str = Field(..., min_length=1, description="知识内容")
    metadata: Dict[str, Any] = Field(..., description="元数据（category, source, title 等）")


class KnowledgeAddResponse(BaseModel):
    """添加知识响应"""
    success: bool
    document_id: str
    message: str


class KnowledgeSearchRequest(BaseModel):
    """知识搜索请求"""
    query: str = Field(..., min_length=1, description="搜索查询")
    top_k: int = Field(5, ge=1, le=20, description="返回结果数量")
    filter: Optional[Dict] = Field(None, description="元数据过滤")


class KnowledgeSearchResult(BaseModel):
    """知识搜索结果"""
    content: str
    metadata: Dict[str, Any]
    score: float
    source: str


class KnowledgeSearchResponse(BaseModel):
    """知识搜索响应"""
    results: List[KnowledgeSearchResult]
    total: int


# ==================== 统计和监控 ====================

class SystemStats(BaseModel):
    """系统统计"""
    total_requests: int
    total_cost: float
    avg_latency: float
    cache_hit_rate: str
    active_sessions: int
    available_agents: int


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str
    uptime: float
    checks: Dict[str, bool]


# ==================== 错误响应 ====================

class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
