"""FastAPI 应用主入口"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from config import settings
from sources.binance import binance_service
from .routes import chatbot, health, admin, market
from .middleware.logging import LoggingMiddleware
from .middleware.rate_limit import RateLimitMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("MarketPulse API starting...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # 启动 Binance WebSocket
    await binance_service.start()

    yield

    # 关闭时执行
    await binance_service.stop()
    logger.info("MarketPulse API shutting down...")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="MarketPulse AI - 企业级金融智能助手 API",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# ==================== 中间件配置 ====================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gzip 压缩
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 自定义中间件
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

# ==================== 路由注册 ====================

# 健康检查
app.include_router(health.router, prefix="/health", tags=["Health"])

# Chatbot API
app.include_router(chatbot.router, prefix=settings.API_PREFIX, tags=["Chatbot"])

# 管理 API
app.include_router(admin.router, prefix=f"{settings.API_PREFIX}/admin", tags=["Admin"])

# Market API
app.include_router(market.router, prefix=f"{settings.API_PREFIX}/market", tags=["Market"])


# ==================== 根路径 ====================

@app.get("/")
async def root():
    """API 根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs" if settings.DEBUG else "disabled",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.app:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
