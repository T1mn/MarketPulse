"""API 集成测试"""
import pytest
from httpx import AsyncClient
from api.app import app


@pytest.mark.asyncio
async def test_health_check():
    """测试健康检查接口"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert "checks" in data


@pytest.mark.asyncio
async def test_chat_api():
    """测试聊天 API"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat",
            json={
                "message": "你好",
                "user_id": "test_user"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "content" in data
        assert "intent" in data
        assert "agent" in data
        assert "confidence" in data


@pytest.mark.asyncio
async def test_agents_list():
    """测试 Agent 列表 API"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/admin/agents")

        assert response.status_code == 200
        data = response.json()

        assert "agents" in data
        assert "total" in data
        assert data["total"] == 4  # 应该有4个 Agent
