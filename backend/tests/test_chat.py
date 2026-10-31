"""Chat completion API tests."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import create_app


@pytest.fixture
async def client():
    """Create test client."""
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_create_completion(client: AsyncClient):
    """Test creating a non-streaming chat completion."""
    request = {
        "model": "test-model",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": False
    }
    response = await client.post("/api/v1/chat/completions", json=request)
    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "test-model"
    assert "choices" in data
    assert len(data["choices"]) == 1
    assert data["choices"][0]["message"]["role"] == "assistant"
    assert "usage" in data


@pytest.mark.asyncio
async def test_create_completion_stream(client: AsyncClient):
    """Test creating a streaming chat completion."""
    request = {
        "model": "test-model",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": True
    }
    response = await client.post("/api/v1/chat/completions/stream", json=request)
    assert response.status_code == 200
    # Check it's an SSE response
    assert response.headers["content-type"].startswith("text/event-stream")
    
    # Read a few events
    content = response.text
    assert "role" in content or "delta" in content


@pytest.mark.asyncio
async def test_streaming_with_stream_false_returns_501(client: AsyncClient):
    """Test that stream=true on non-stream endpoint returns 501."""
    request = {
        "model": "test-model",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": True
    }
    response = await client.post("/api/v1/chat/completions", json=request)
    assert response.status_code == 501
