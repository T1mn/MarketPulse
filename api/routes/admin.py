"""管理 API 路由"""
import logging
from fastapi import APIRouter, HTTPException
from typing import List

from core.dialogue.dialogue_manager import dialogue_manager
from core.rag.retriever import retriever
from core.llm.router import llm_router
from api.schemas import (
    SessionListResponse,
    SessionInfo,
    AgentListResponse,
    AgentInfo,
    KnowledgeAddRequest,
    KnowledgeAddResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeSearchResult,
    SystemStats,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== 会话管理 ====================

@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions():
    """获取所有活跃会话"""
    try:
        session_ids = dialogue_manager.state_tracker.get_active_sessions()

        sessions = []
        for session_id in session_ids:
            state = dialogue_manager.state_tracker.states.get(session_id)
            if state:
                sessions.append(SessionInfo(
                    session_id=state.session_id,
                    user_id=state.user_id,
                    created_at=state.created_at,
                    updated_at=state.updated_at,
                    turn_count=state.turn_count,
                    current_intent=state.current_intent,
                ))

        return SessionListResponse(
            sessions=sessions,
            total=len(sessions)
        )

    except Exception as e:
        logger.error(f"List sessions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除指定会话"""
    try:
        dialogue_manager.reset_session(session_id)
        return {"success": True, "message": f"Session {session_id} deleted"}

    except Exception as e:
        logger.error(f"Delete session error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Agent 管理 ====================

@router.get("/agents", response_model=AgentListResponse)
async def list_agents():
    """获取所有可用 Agent"""
    try:
        # 导入所有 Agent
        from core.agents import (
            CustomerServiceAgent,
            MarketAnalysisAgent,
            TradingAssistantAgent,
            WorkflowAutomationAgent,
        )

        agents_list = [
            CustomerServiceAgent(),
            MarketAnalysisAgent(),
            TradingAssistantAgent(),
            WorkflowAutomationAgent(),
        ]

        agents = []
        for agent in agents_list:
            agents.append(AgentInfo(
                name=agent.name,
                description=agent.description,
                supported_intents=list(agent.supported_intents),
                available=True
            ))

        return AgentListResponse(
            agents=agents,
            total=len(agents)
        )

    except Exception as e:
        logger.error(f"List agents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 知识库管理 ====================

@router.post("/knowledge", response_model=KnowledgeAddResponse)
async def add_knowledge(request: KnowledgeAddRequest):
    """添加知识到知识库"""
    try:
        success = await retriever.add_knowledge(
            content=request.content,
            metadata=request.metadata
        )

        if success:
            import hashlib
            doc_id = hashlib.md5(request.content.encode()).hexdigest()

            return KnowledgeAddResponse(
                success=True,
                document_id=doc_id,
                message="Knowledge added successfully"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to add knowledge")

    except Exception as e:
        logger.error(f"Add knowledge error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/knowledge/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(request: KnowledgeSearchRequest):
    """搜索知识库"""
    try:
        results = await retriever.retrieve(
            query=request.query,
            filters=request.filter,
            top_k=request.top_k
        )

        search_results = [
            KnowledgeSearchResult(
                content=r.content,
                metadata=r.metadata,
                score=r.score,
                source=r.source
            )
            for r in results
        ]

        return KnowledgeSearchResponse(
            results=search_results,
            total=len(search_results)
        )

    except Exception as e:
        logger.error(f"Search knowledge error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 系统统计 ====================

@router.get("/stats", response_model=SystemStats)
async def get_stats():
    """获取系统统计信息"""
    try:
        # LLM 统计
        llm_stats = llm_router.get_stats()

        # 会话统计
        active_sessions = len(dialogue_manager.state_tracker.get_active_sessions())

        return SystemStats(
            total_requests=llm_stats["request_count"],
            total_cost=llm_stats["total_cost"],
            avg_latency=0.5,  # TODO: 实际追踪
            cache_hit_rate=llm_stats["cache_stats"]["hit_rate"],
            active_sessions=active_sessions,
            available_agents=4,
        )

    except Exception as e:
        logger.error(f"Get stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear")
async def clear_cache():
    """清空 LLM 缓存"""
    try:
        llm_router.cache.clear()
        return {"success": True, "message": "Cache cleared"}

    except Exception as e:
        logger.error(f"Clear cache error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
