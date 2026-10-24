"""Model management service."""
import os
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
from enum import Enum


class BackendType(Enum):
    """Inference backend types."""
    CUDA = "cuda"
    VULKAN = "vulkan"
    METAL = "metal"
    CPU = "cpu"


class QuantizationType(Enum):
    """Model quantization types."""
    INT4 = "int4"
    INT8 = "int8"
    FP16 = "fp16"
    BF16 = "bf16"
    FP32 = "fp32"


@dataclass
class ModelConfig:
    """Model configuration."""
    id: str
    name: str
    path: str
    size_gb: float
    quantization: QuantizationType
    backend: BackendType
    num_layers: int = 0
    num_experts: int = 0
    expert_size_mb: float = 0.0
    context_length: int = 4096
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "size_gb": self.size_gb,
            "quantization": self.quantization.value,
            "backend": self.backend.value,
            "num_layers": self.num_layers,
            "num_experts": self.num_experts,
            "expert_size_mb": self.expert_size_mb,
            "context_length": self.context_length,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ModelConfig":
        return cls(
            id=data["id"],
            name=data["name"],
            path=data["path"],
            size_gb=data["size_gb"],
            quantization=QuantizationType(data["quantization"]),
            backend=BackendType(data["backend"]),
            num_layers=data.get("num_layers", 0),
            num_experts=data.get("num_experts", 0),
            expert_size_mb=data.get("expert_size_mb", 0.0),
            context_length=data.get("context_length", 4096),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ModelIndex:
    """Index of model files for streaming."""
    config_path: str
    expert_paths: Dict[tuple, str]  # (layer, expert_id) -> file path
    dense_paths: Dict[str, str]  # tensor_name -> file path
    total_size_bytes: int
    metadata: Dict


class ModelService:
    """Service for managing model configurations and discovery."""

    def __init__(self, model_root: str = "/models"):
        self._model_root = Path(model_root)
        self._models: Dict[str, ModelConfig] = {}
        self._indices: Dict[str, ModelIndex] = {}
        self._scan_models()

    def _scan_models(self):
        """Scan model directory for model configurations."""
        if not self._model_root.exists():
            return

        for model_dir in self._model_root.iterdir():
            if not model_dir.is_dir():
                continue

            config_path = model_dir / "config.json"
            if config_path.exists():
                try:
                    with open(config_path) as f:
                        config_data = json.load(f)
                    config = ModelConfig.from_dict(config_data)
                    self._models[config.id] = config
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue

    def list_models(self) -> List[ModelConfig]:
        """List all discovered models."""
        return list(self._models.values())

    def get_model(self, model_id: str) -> Optional[ModelConfig]:
        """Get model configuration by ID."""
        return self._models.get(model_id)

    def get_model_path(self, model_id: str) -> Optional[Path]:
        """Get model directory path."""
        model = self._models.get(model_id)
        if model:
            return Path(model.path)
        return None

    def register_model(self, config: ModelConfig):
        """Register a new model configuration."""
        self._models[config.id] = config
        # Only write to disk if path is writable
        try:
            config_path = Path(config.path) / "config.json"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, "w") as f:
                json.dump(config.to_dict(), f, indent=2)
        except (OSError, PermissionError):
            # In test environments, /models may be read-only
            pass

    def estimate_expert_size(self, model_id: str) -> float:
        """Estimate per-expert size in MB."""
        model = self._models.get(model_id)
        if not model or model.num_experts == 0:
            return 0.0
        # Rough estimate: total size minus dense weights, divided by experts
        dense_overhead_gb = 2.0  # Embedding, norms, routers, etc.
        expert_gb = max(0, model.size_gb - dense_overhead_gb)
        return (expert_gb * 1024) / model.num_experts


# Global model service instance
_model_service: Optional[ModelService] = None


def get_model_service() -> ModelService:
    """Get or create the global model service instance."""
    global _model_service
    if _model_service is None:
        model_root = os.environ.get("COLI_MODEL_PATH", "/models")
        _model_service = ModelService(model_root)
    return _model_service
