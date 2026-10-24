"""Expert cache service with placement policies."""
import time
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple
from collections import OrderedDict


class PlacementPolicy(Enum):
    """Cache placement policies."""
    LRU = "lru"
    LRU_APPROX = "lru-approx"
    GATE_MOMENTUM = "gate-momentum"
    LFRU_GATED = "lru-gated"


@dataclass
class ExpertSlot:
    """Represents a cached expert."""
    layer: int
    expert_id: int
    data: bytes
    size_mb: float
    last_access: float = field(default_factory=time.time)
    access_count: int = 0
    gate_score: float = 0.0


@dataclass
class CacheStats:
    """Cache statistics."""
    hit_rate: float = 0.0
    total_requests: int = 0
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    current_size_mb: float = 0.0
    max_size_mb: float = 0.0


class ExpertCache:
    """Thread-safe expert cache with configurable placement policies."""

    def __init__(self, max_size_mb: float = 8192.0):
        self._max_size_mb = max_size_mb
        self._slots: Dict[Tuple[int, int], ExpertSlot] = {}
        self._lock = threading.RLock()
        self._policy = PlacementPolicy.LRU
        self._policy_enabled = True
        self._gate_momentum_history: Dict[Tuple[int, int], float] = {}
        self._stats = CacheStats(max_size_mb=max_size_mb)

    @property
    def policy(self) -> PlacementPolicy:
        return self._policy

    @policy.setter
    def policy(self, value: PlacementPolicy):
        with self._lock:
            self._policy = value

    def set_policy(self, policy_name: str, enabled: bool = True):
        """Set the active placement policy."""
        try:
            self._policy = PlacementPolicy(policy_name)
            self._policy_enabled = enabled
        except ValueError:
            raise ValueError(f"Unknown policy: {policy_name}")

    def get(self, layer: int, expert_id: int) -> Optional[bytes]:
        """Get expert data from cache."""
        with self._lock:
            key = (layer, expert_id)
            self._stats.total_requests += 1

            if key in self._slots:
                slot = self._slots[key]
                slot.last_access = time.time()
                slot.access_count += 1
                self._stats.hits += 1
                self._update_hit_rate()
                return slot.data

            self._stats.misses += 1
            self._update_hit_rate()
            return None

    def put(self, layer: int, expert_id: int, data: bytes, gate_score: float = 0.0):
        """Put expert data into cache."""
        with self._lock:
            key = (layer, expert_id)
            size_mb = len(data) / (1024 * 1024)

            # Check if we need to evict
            while self._stats.current_size_mb + size_mb > self._max_size_mb and self._slots:
                self._evict_one()

            # Add new slot
            self._slots[key] = ExpertSlot(
                layer=layer,
                expert_id=expert_id,
                data=data,
                size_mb=size_mb,
                gate_score=gate_score,
            )
            self._stats.current_size_mb += size_mb

            # Update gate momentum history
            if self._policy == PlacementPolicy.GATE_MOMENTUM:
                self._gate_momentum_history[key] = gate_score

    def _evict_one(self):
        """Evict one slot based on current policy."""
        if not self._slots:
            return

        if self._policy == PlacementPolicy.LRU or self._policy == PlacementPolicy.LRU_APPROX:
            # Find least recently used
            victim_key = min(self._slots.keys(), key=lambda k: self._slots[k].last_access)
        elif self._policy == PlacementPolicy.GATE_MOMENTUM:
            # Evict lowest gate score
            victim_key = min(self._slots.keys(), key=lambda k: self._slots[k].gate_score)
        elif self._policy == PlacementPolicy.LFRU_GATED:
            # LRU with gate score boost
            victim_key = min(
                self._slots.keys(),
                key=lambda k: self._slots[k].last_access - (self._slots[k].gate_score * 1000)
            )
        else:
            victim_key = min(self._slots.keys(), key=lambda k: self._slots[k].last_access)

        victim = self._slots.pop(victim_key)
        self._stats.current_size_mb -= victim.size_mb
        self._stats.evictions += 1

    def _update_hit_rate(self):
        """Update hit rate statistic."""
        if self._stats.total_requests > 0:
            self._stats.hit_rate = (self._stats.hits / self._stats.total_requests) * 100

    def get_stats(self) -> CacheStats:
        """Get current cache statistics."""
        with self._lock:
            return CacheStats(
                hit_rate=self._stats.hit_rate,
                total_requests=self._stats.total_requests,
                hits=self._stats.hits,
                misses=self._stats.misses,
                evictions=self._stats.evictions,
                current_size_mb=self._stats.current_size_mb,
                max_size_mb=self._stats.max_size_mb,
            )

    def list_policies(self) -> List[Dict]:
        """List available policies with status."""
        return [
            {
                "name": p.value,
                "description": self._policy_description(p),
                "enabled": self._policy == p and self._policy_enabled,
            }
            for p in PlacementPolicy
        ]

    def _policy_description(self, policy: PlacementPolicy) -> str:
        descriptions = {
            PlacementPolicy.LRU: "Least Recently Used eviction",
            PlacementPolicy.LRU_APPROX: "Approximate LRU with lower overhead",
            PlacementPolicy.GATE_MOMENTUM: "Router gate momentum-based placement",
            PlacementPolicy.LFRU_GATED: "LRU with router gating hints",
        }
        return descriptions.get(policy, "")

    def clear(self):
        """Clear all cache slots."""
        with self._lock:
            self._slots.clear()
            self._gate_momentum_history.clear()
            self._stats = CacheStats(max_size_mb=self._max_size_mb)


# Global cache instance
_cache_instance: Optional[ExpertCache] = None


def get_cache() -> ExpertCache:
    """Get or create the global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = ExpertCache()
    return _cache_instance
