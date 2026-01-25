"""健康检查路由"""
import logging
import time
from fastapi import APIRouter
from api.schemas import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# 记录启动时间
START_TIME = time.time()


@router.get("", response_model=HealthResponse)
@router.get("/", response_model=HealthResponse)
async def health_check():
    """
    健康检查接口

    返回系统健康状态
    """
    uptime = time.time() - START_TIME

    # 检查各个组件状态
    checks = {
        "api": True,
        "llm": await check_llm_health(),
        "vector_store": await check_vector_store_health(),
        "dialogue_manager": True,
    }

    status = "healthy" if all(checks.values()) else "degraded"

    return HealthResponse(
        status=status,
        version="2.0.0",
        uptime=uptime,
        checks=checks
    )


async def check_llm_health() -> bool:
    """检查 LLM 健康状态"""
    try:
        from core.llm.router import llm_router
        # 简单检查是否有可用的提供商
        return len(llm_router.providers) > 0
    except Exception as e:
        logger.error(f"LLM health check failed: {e}")
        return False


async def check_vector_store_health() -> bool:
    """检查向量存储健康状态"""
    try:
        from core.rag.vector_store import vector_store
        # 检查是否可以访问
        return vector_store.collection is not None
    except Exception as e:
        logger.error(f"Vector store health check failed: {e}")
        return False


@router.get("/live")
async def liveness():
    """
    存活检查（Kubernetes liveness probe）
    """
    return {"status": "alive"}


@router.get("/ready")
async def readiness():
    """
    就绪检查（Kubernetes readiness probe）
    """
    # 检查关键组件
    checks = {
        "llm": await check_llm_health(),
        "vector_store": await check_vector_store_health(),
    }

    if all(checks.values()):
        return {"status": "ready", "checks": checks}
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail={"status": "not ready", "checks": checks})
