"""统一启动入口"""
import sys
import argparse
import logging

from monitoring.logger import setup_logging

logger = logging.getLogger(__name__)


def start_api():
    """启动 API 服务"""
    import uvicorn
    from config import settings

    logger.info("🚀 Starting MarketPulse API...")

    uvicorn.run(
        "api.app:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )


def start_ui():
    """启动 Web UI (React 前端)"""
    import subprocess

    logger.info("🎨 Starting MarketPulse React UI...")
    logger.info("📍 请在 frontend/ 目录运行: npm run dev")
    logger.info("📍 或访问: http://localhost:5173")

    # 尝试启动 React 开发服务器
    try:
        subprocess.run(
            ["npm", "run", "dev"],
            cwd="frontend",
            check=True
        )
    except FileNotFoundError:
        logger.error("❌ npm 未安装，请手动启动前端: cd frontend && npm run dev")


def init_knowledge():
    """初始化知识库"""
    import asyncio
    from scripts.init_knowledge import init_knowledge_base

    logger.info("📚 Initializing knowledge base...")

    asyncio.run(init_knowledge_base())


def run_tests():
    """运行测试"""
    import pytest

    logger.info("🧪 Running tests...")

    sys.exit(pytest.main(["-v", "tests/"]))


def main():
    """主入口"""
    parser = argparse.ArgumentParser(description="MarketPulse - 企业级金融智能助手")

    parser.add_argument(
        "command",
        choices=["api", "ui", "init-knowledge", "test"],
        help="运行命令"
    )

    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别"
    )

    args = parser.parse_args()

    # 配置日志
    setup_logging(log_level=args.log_level)

    # 执行命令
    if args.command == "api":
        start_api()
    elif args.command == "ui":
        start_ui()
    elif args.command == "init-knowledge":
        init_knowledge()
    elif args.command == "test":
        run_tests()


if __name__ == "__main__":
    main()
