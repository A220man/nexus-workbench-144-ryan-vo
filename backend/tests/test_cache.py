"""Cache API tests."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import create_app
from app.services.cache import get_cache


@pytest.fixture
async def client():
    """Create test client."""
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_list_policies(client: AsyncClient):
    """Test listing cache policies."""
    response = await client.get("/api/v1/cache/policies")
    assert response.status_code == 200
    data = response.json()
    assert "policies" in data
    assert len(data["policies"]) >= 3
    policy_names = [p["name"] for p in data["policies"]]
    assert "gate-momentum" in policy_names
    assert "lru" in policy_names


@pytest.mark.asyncio
async def test_get_cache_stats(client: AsyncClient):
    """Test getting cache statistics."""
    response = await client.get("/api/v1/cache/stats")
    assert response.status_code == 200
    data = response.json()
    assert "hit_rate" in data
    assert "total_requests" in data
    assert "hits" in data
    assert "misses" in data
    assert "layer_stats" in data


@pytest.mark.asyncio
async def test_enable_policy(client: AsyncClient):
    """Test enabling a cache policy."""
    response = await client.post("/api/v1/cache/policies/lru/enable")
    assert response.status_code == 200
    data = response.json()
    assert data["policy"] == "lru"
    assert data["enabled"] is True


@pytest.mark.asyncio
async def test_disable_policy(client: AsyncClient):
    """Test disabling a cache policy."""
    response = await client.post("/api/v1/cache/policies/lru/disable")
    assert response.status_code == 200
    data = response.json()
    assert data["policy"] == "lru"
    assert data["enabled"] is False


@pytest.mark.asyncio
async def test_get_layer_stats(client: AsyncClient):
    """Test getting layer-specific statistics."""
    # First make some requests to populate layer stats
    cache = get_cache()
    cache.put(0, 0, b"test data", gate_score=0.5)
    cache.get(0, 0)
    
    response = await client.get("/api/v1/cache/stats/layer/0")
    assert response.status_code == 200
    data = response.json()
    assert data["layer"] == 0
    assert "hits" in data
    assert "misses" in data
    assert "hit_rate" in data


@pytest.mark.asyncio
async def test_get_layer_stats_not_found(client: AsyncClient):
    """Test getting stats for non-existent layer."""
    response = await client.get("/api/v1/cache/stats/layer/999")
    assert response.status_code == 404
