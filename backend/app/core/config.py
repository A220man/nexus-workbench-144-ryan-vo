"""Application configuration."""
import os
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path


@dataclass
class LLMConfig:
    """LLM provider configuration."""
    api_key: str = ""
    provider: str = "openai-compatible"
    model: str = ""
    base_url: str = ""
    timeout: float = 30.0
    max_retries: int = 3


@dataclass
class KeycloakConfig:
    """Keycloak OIDC configuration."""
    url: str = "http://keycloak:8080"
    realm: str = "nexus"
    client_id: str = "nexus-workbench"
    client_secret: str = ""
    admin_user: str = "admin"
    admin_password: str = "admin"


@dataclass
class CacheConfig:
    """Expert cache configuration."""
    max_size_mb: float = 8192.0
    default_policy: str = "lru"
    enable_compression: bool = False
    compression_ratio_threshold: float = 0.9


@dataclass
class InferenceConfig:
    """Inference engine configuration."""
    mtp_enabled: bool = True
    mtp_depth: int = 1
    draft_tokens: int = 8
    cuda_pipe: int = 2
    cuda_dense: bool = True
    cuda_attn: bool = True
    cuda_tc_w4a16: bool = True
    vulkan_enabled: bool = False
    vulkan_dense: bool = False
    vulkan_attn: bool = False


@dataclass
class ModelConfig:
    """Model storage configuration."""
    root_path: str = "/models"
    auto_scan: bool = True


@dataclass
class AppConfig:
    """Main application configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    cors_origins: List[str] = field(default_factory=lambda: [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ])
    llm: LLMConfig = field(default_factory=LLMConfig)
    keycloak: KeycloakConfig = field(default_factory=KeycloakConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    inference: InferenceConfig = field(default_factory=InferenceConfig)
    model: ModelConfig = field(default_factory=ModelConfig)


def load_config() -> AppConfig:
    """Load configuration from environment variables."""
    config = AppConfig()

    # Server
    config.host = os.environ.get("HOST", config.host)
    config.port = int(os.environ.get("PORT", str(config.port)))
    config.debug = os.environ.get("DEBUG", "false").lower() == "true"

    # CORS
    cors_origins = os.environ.get("CORS_ORIGINS")
    if cors_origins:
        config.cors_origins = [o.strip() for o in cors_origins.split(",")]

    # LLM
    config.llm.api_key = os.environ.get("LLM_API_KEY", config.llm.api_key)
    config.llm.provider = os.environ.get("LLM_PROVIDER", config.llm.provider)
    config.llm.model = os.environ.get("LLM_MODEL", config.llm.model)
    config.llm.base_url = os.environ.get("LLM_BASE_URL", config.llm.base_url)

    # Keycloak
    config.keycloak.url = os.environ.get("KEYCLOAK_URL", config.keycloak.url)
    config.keycloak.realm = os.environ.get("KEYCLOAK_REALM", config.keycloak.realm)
    config.keycloak.client_id = os.environ.get("KEYCLOAK_CLIENT_ID", config.keycloak.client_id)
    config.keycloak.client_secret = os.environ.get("KEYCLOAK_CLIENT_SECRET", config.keycloak.client_secret)

    # Cache
    config.cache.max_size_mb = float(os.environ.get("CACHE_MAX_SIZE_MB", str(config.cache.max_size_mb)))
    config.cache.default_policy = os.environ.get("CACHE_DEFAULT_POLICY", config.cache.default_policy)
    config.cache.enable_compression = os.environ.get("COLI_ZSTREAM", "0") == "1"

    # Inference
    config.inference.mtp_enabled = os.environ.get("COLI_CUDA_MTP", "1") == "1"
    config.inference.cuda_pipe = int(os.environ.get("COLI_CUDA_PIPE", str(config.inference.cuda_pipe)))
    config.inference.cuda_dense = os.environ.get("COLI_CUDA_DENSE", "1") == "1"
    config.inference.cuda_attn = os.environ.get("COLI_CUDA_ATTN", "1") == "1"
    config.inference.cuda_tc_w4a16 = os.environ.get("COLI_CUDA_TC_W4A16", "1") == "1"
    config.inference.vulkan_enabled = os.environ.get("COLI_VULKAN", "0") == "1"
    config.inference.vulkan_dense = os.environ.get("COLI_VK_DENSE", "0") == "1"
    config.inference.vulkan_attn = os.environ.get("COLI_VK_ATTN", "0") == "1"

    # Model
    config.model.root_path = os.environ.get("COLI_MODEL_PATH", config.model.root_path)

    return config


# Global config instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = load_config()
    return _config
