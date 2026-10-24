"""Health endpoint tests."""
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
async def test_health_check(client: AsyncClient):
    """Test health check endpoint returns ok."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "nexus-workbench"
