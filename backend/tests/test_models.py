"""Model API tests."""
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
async def test_list_models(client: AsyncClient):
    """Test listing models."""
    response = await client.get("/api/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert isinstance(data["models"], list)


@pytest.mark.asyncio
async def test_get_model_not_found(client: AsyncClient):
    """Test getting a non-existent model returns 404."""
    response = await client.get("/api/v1/models/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_register_model(client: AsyncClient):
    """Test registering a new model."""
    config = {
        "id": "test-model",
        "name": "Test Model",
        "path": "/models/test-model",
        "size_gb": 10.0,
        "quantization": "int4",
        "backend": "cpu",
        "num_layers": 24,
        "num_experts": 8,
        "expert_size_mb": 1024.0,
        "context_length": 4096,
        "metadata": {}
    }
    response = await client.post("/api/v1/models/test-model/register", json=config)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "registered"
    assert data["model_id"] == "test-model"

    # Verify it's listed
    response = await client.get("/api/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert len(data["models"]) >= 1
    model = data["models"][0]
    assert model["id"] == "test-model"
    assert model["name"] == "Test Model"
