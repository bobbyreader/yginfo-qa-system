import pytest
import pytest_asyncio
from httpx import AsyncClient
from app.main import app


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_check(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_chat_flow(client):
    """测试完整对话流程"""
    payload = {
        "tenant_id": "test",
        "channel": "webchat",
        "user_id": "test_user",
        "session_id": "test_session",
        "message": "你们的产品有什么功能？",
    }
    resp = await client.post("/api/chat/message", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "reply" in data
    assert "session_id" in data
