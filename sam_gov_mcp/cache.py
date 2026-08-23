"""Caching layer for the SAM.gov MCP Server.

Provides a small async cache abstraction with two backends:

* :class:`MemoryCache` -- in-process TTL cache, safe for concurrent use.
* :class:`NoCache` -- a null backend used when caching is disabled.

:class:`CacheManager` wraps a backend and owns the default TTL plus key
construction, so callers never have to build cache keys by hand.
"""

import asyncio
import hashlib
import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class CacheBackend(ABC):
    """Interface implemented by every cache backend."""

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Return the cached value for ``key``, or ``None`` if absent/expired."""

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int) -> None:
        """Store ``value`` under ``key`` for ``ttl`` seconds."""

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Remove ``key`` from the cache if present."""

    @abstractmethod
    async def clear(self) -> None:
        """Remove every entry from the cache."""

    async def close(self) -> None:
        """Release any resources held by the backend."""
        return None


class MemoryCache(CacheBackend):
    """In-process cache with per-entry expiry.

    Entries are stored as ``(expires_at, value)``. ``expires_at`` is a
    :func:`time.monotonic` deadline, so the cache is immune to wall-clock
    changes. Expired entries are evicted lazily on read.
    """

    def __init__(self) -> None:
        self._store: dict[str, tuple[float | None, Any]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None

            expires_at, value = entry
            if expires_at is not None and expires_at <= time.monotonic():
                del self._store[key]
                logger.debug("Cache entry expired: %s", key)
                return None

            return value

    async def set(self, key: str, value: Any, ttl: int) -> None:
        expires_at = time.monotonic() + ttl if ttl and ttl > 0 else None
        async with self._lock:
            self._store[key] = (expires_at, value)

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._store.pop(key, None)

    async def clear(self) -> None:
        async with self._lock:
            self._store.clear()

    async def close(self) -> None:
        await self.clear()

    def __len__(self) -> int:
        return len(self._store)


class NoCache(CacheBackend):
    """Null backend. Every read misses and every write is discarded."""

    async def get(self, key: str) -> Any | None:
        return None

    async def set(self, key: str, value: Any, ttl: int) -> None:
        return None

    async def delete(self, key: str) -> None:
        return None

    async def clear(self) -> None:
        return None


class CacheManager:
    """Owns a cache backend, the default TTL, and key construction."""

    def __init__(self, backend: CacheBackend, ttl: int = 3600) -> None:
        """Initialize the manager.

        Args:
            backend: Cache backend to delegate to.
            ttl: Default time-to-live in seconds for entries written
                without an explicit TTL.
        """
        self.backend = backend
        self.ttl = ttl

    @staticmethod
    def make_key(namespace: str, params: dict[str, Any]) -> str:
        """Build a stable cache key from a namespace and a parameter mapping.

        Parameters are sorted before hashing so that two calls with the same
        arguments in a different order share a key. ``None`` values are
        dropped so that an omitted filter and an explicitly-null filter are
        treated as the same request.

        Args:
            namespace: Logical grouping, usually the tool name.
            params: Request parameters.

        Returns:
            A key of the form ``"<namespace>:<sha256 prefix>"``.
        """
        cleaned = {k: v for k, v in sorted(params.items()) if v is not None}
        payload = json.dumps(cleaned, sort_keys=True, default=str)
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]
        return f"{namespace}:{digest}"

    async def get(self, key: str) -> Any | None:
        """Read a value, logging whether it was a hit or a miss."""
        value = await self.backend.get(key)
        logger.debug("Cache %s: %s", "hit" if value is not None else "miss", key)
        return value

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Write a value using ``ttl``, falling back to the manager default."""
        await self.backend.set(key, value, self.ttl if ttl is None else ttl)

    async def delete(self, key: str) -> None:
        """Remove a single entry."""
        await self.backend.delete(key)

    async def clear(self) -> None:
        """Remove every entry."""
        await self.backend.clear()

    async def close(self) -> None:
        """Close the underlying backend."""
        await self.backend.close()
