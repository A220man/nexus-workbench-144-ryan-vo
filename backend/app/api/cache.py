"""Expert cache management endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from app.services.cache import get_cache, PlacementPolicy

router = APIRouter()


class PolicyInfo(BaseModel):
    name: str
    description: str
    enabled: bool


class PolicyListResponse(BaseModel):
    policies: List[PolicyInfo]


class CacheStats(BaseModel):
    hit_rate: float
    total_requests: int
    hits: int
    misses: int
    evictions: int
    current_size_mb: float
    max_size_mb: float


class PolicyActionResponse(BaseModel):
    policy: str
    enabled: bool


@router.get("/policies", response_model=PolicyListResponse)
async def list_policies():
    """List available cache placement policies."""
    cache = get_cache()
    return {"policies": cache.list_policies()}


@router.get("/stats", response_model=CacheStats)
async def get_cache_stats():
    """Get cache statistics."""
    cache = get_cache()
    stats = cache.get_stats()
    return {
        "hit_rate": stats.hit_rate,
        "total_requests": stats.total_requests,
        "hits": stats.hits,
        "misses": stats.misses,
        "evictions": stats.evictions,
        "current_size_mb": stats.current_size_mb,
        "max_size_mb": stats.max_size_mb,
    }


@router.post("/policies/{policy_name}/enable", response_model=PolicyActionResponse)
async def enable_policy(policy_name: str):
    """Enable a cache placement policy."""
    cache = get_cache()
    try:
        policy = PlacementPolicy(policy_name)
        cache.set_policy(policy_name, enabled=True)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Policy {policy_name} not found")

    return {"policy": policy_name, "enabled": True}


@router.post("/policies/{policy_name}/disable", response_model=PolicyActionResponse)
async def disable_policy(policy_name: str):
    """Disable a cache placement policy."""
    cache = get_cache()
    try:
        PlacementPolicy(policy_name)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Policy {policy_name} not found")

    # For now, disabling means reverting to LRU
    cache.set_policy("lru", enabled=True)
    return {"policy": policy_name, "enabled": False}
