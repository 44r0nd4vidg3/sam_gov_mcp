"""Tests for the caching layer."""

import asyncio

import pytest

from sam_gov_mcp.cache import CacheManager, MemoryCache, NoCache


class TestMemoryCache:
    """Test the in-process cache backend."""

    @pytest.mark.asyncio
    async def test_set_and_get(self):
        cache = MemoryCache()
        await cache.set("k", {"value": 1}, ttl=60)

        assert await cache.get("k") == {"value": 1}

    @pytest.mark.asyncio
    async def test_missing_key_returns_none(self):
        cache = MemoryCache()

        assert await cache.get("nope") is None

    @pytest.mark.asyncio
    async def test_entry_expires(self):
        cache = MemoryCache()
        await cache.set("k", "v", ttl=1)

        # Expiry uses a monotonic deadline, so move the deadline instead of
        # sleeping through the TTL.
        expires_at, value = cache._store["k"]
        cache._store["k"] = (expires_at - 2, value)

        assert await cache.get("k") is None
        assert len(cache) == 0

    @pytest.mark.asyncio
    async def test_zero_ttl_never_expires(self):
        cache = MemoryCache()
        await cache.set("k", "v", ttl=0)

        assert await cache.get("k") == "v"

    @pytest.mark.asyncio
    async def test_delete_and_clear(self):
        cache = MemoryCache()
        await cache.set("a", 1, ttl=60)
        await cache.set("b", 2, ttl=60)

        await cache.delete("a")
        assert await cache.get("a") is None
        assert await cache.get("b") == 2

        await cache.clear()
        assert await cache.get("b") is None

    @pytest.mark.asyncio
    async def test_concurrent_writes_are_safe(self):
        cache = MemoryCache()

        await asyncio.gather(*(cache.set(f"k{i}", i, ttl=60) for i in range(50)))

        assert len(cache) == 50


class TestNoCache:
    """Test the null backend."""

    @pytest.mark.asyncio
    async def test_reads_always_miss(self):
        cache = NoCache()
        await cache.set("k", "v", ttl=60)

        assert await cache.get("k") is None


class TestCacheManager:
    """Test key construction and manager behaviour."""

    def test_key_is_order_independent(self):
        a = CacheManager.make_key("search", {"b": 2, "a": 1})
        b = CacheManager.make_key("search", {"a": 1, "b": 2})

        assert a == b

    def test_key_ignores_none_values(self):
        a = CacheManager.make_key("search", {"a": 1, "ptype": None})
        b = CacheManager.make_key("search", {"a": 1})

        assert a == b

    def test_key_is_namespaced_and_differs_by_params(self):
        a = CacheManager.make_key("search", {"a": 1})
        b = CacheManager.make_key("search", {"a": 2})

        assert a.startswith("search:")
        assert a != b

    @pytest.mark.asyncio
    async def test_manager_applies_default_ttl(self):
        manager = CacheManager(MemoryCache(), ttl=42)
        await manager.set("k", "v")

        expires_at, _ = manager.backend._store["k"]
        assert expires_at is not None

        assert await manager.get("k") == "v"

    @pytest.mark.asyncio
    async def test_close_clears_backend(self):
        manager = CacheManager(MemoryCache(), ttl=60)
        await manager.set("k", "v")
        await manager.close()

        assert await manager.get("k") is None
