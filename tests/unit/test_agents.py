"""Agent 测试"""
import pytest
from core.agents import CustomerServiceAgent, MarketAnalysisAgent


@pytest.mark.asyncio
async def test_customer_service_agent_greeting():
    """测试客服 Agent 问候"""
    agent = CustomerServiceAgent()

    response = await agent.process(
        user_input="你好",
        intent="greeting",
        entities={},
        context={}
    )

    assert response.content is not None
    assert "MarketPulse" in response.content
    assert response.confidence > 0.8


@pytest.mark.asyncio
async def test_market_analysis_agent():
    """测试市场分析 Agent"""
    agent = MarketAnalysisAgent()

    assert await agent.can_handle("market_query")
    assert not await agent.can_handle("greeting")

    response = await agent.process(
        user_input="特斯拉现在多少钱？",
        intent="market_query",
        entities={"asset": "TSLA"},
        context={}
    )

    assert response.content is not None
    assert response.agent_name == "market_analysis"
