"""Model management endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.services.model import get_model_service, ModelConfig, BackendType, QuantizationType

router = APIRouter()


class ModelInfo(BaseModel):
    id: str
    name: str
    size_gb: float
    quantization: str
    backend: str
    path: str
    num_layers: int = 0
    num_experts: int = 0
    expert_size_mb: float = 0.0
    context_length: int = 4096


class ModelListResponse(BaseModel):
    models: List[ModelInfo]


class ModelConfigRequest(BaseModel):
    id: str
    name: str
    path: str
    size_gb: float
    quantization: str
    backend: str
    num_layers: int = 0
    num_experts: int = 0
    expert_size_mb: float = 0.0
    context_length: int = 4096
    metadata: dict = {}


@router.get("", response_model=ModelListResponse)
async def list_models():
    """List available models."""
    service = get_model_service()
    models = service.list_models()
    return {
        "models": [
            ModelInfo(
                id=model.id,
                name=model.name,
                size_gb=model.size_gb,
                quantization=model.quantization.value,
                backend=model.backend.value,
                path=model.path,
                num_layers=model.num_layers,
                num_experts=model.num_experts,
                expert_size_mb=model.expert_size_mb,
                context_length=model.context_length,
            )
            for model in models
        ]
    }


@router.get("/{model_id}", response_model=ModelInfo)
async def get_model(model_id: str):
    """Get model details."""
    service = get_model_service()
    model = service.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

    return ModelInfo(
        id=model.id,
        name=model.name,
        size_gb=model.size_gb,
        quantization=model.quantization.value,
        backend=model.backend.value,
        path=model.path,
        num_layers=model.num_layers,
        num_experts=model.num_experts,
        expert_size_mb=model.expert_size_mb,
        context_length=model.context_length,
    )


@router.post("/{model_id}/register")
async def register_model(model_id: str, config: ModelConfigRequest):
    """Register a new model."""
    service = get_model_service()
    if model_id != config.id:
        raise HTTPException(status_code=400, detail="Model ID mismatch")

    model_config = ModelConfig(
        id=config.id,
        name=config.name,
        path=config.path,
        size_gb=config.size_gb,
        quantization=QuantizationType(config.quantization),
        backend=BackendType(config.backend),
        num_layers=config.num_layers,
        num_experts=config.num_experts,
        expert_size_mb=config.expert_size_mb,
        context_length=config.context_length,
        metadata=config.metadata,
    )
    service.register_model(model_config)
    return {"status": "registered", "model_id": model_id}


@router.get("/{model_id}/expert-size")
async def get_expert_size(model_id: str):
    """Get estimated expert size for a model."""
    service = get_model_service()
    size_mb = service.estimate_expert_size(model_id)
    return {"model_id": model_id, "expert_size_mb": size_mb}
