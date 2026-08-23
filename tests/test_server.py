"""Tests that the server can actually be built and expose its tools.

These are the tests that would have caught the missing cache module, the
BaseTool signature mismatch, and the packaging gap: every one of those
failures shows up the moment MCPServer() is constructed.
"""

import pytest

from sam_gov_mcp.cache import CacheManager, MemoryCache
from sam_gov_mcp.config import AppConfig
from sam_gov_mcp.server import MCPServer


@pytest.fixture
def config(monkeypatch):
    """Build a config from the environment without touching a real .env."""
    monkeypatch.setenv("SAM_API_KEY", "test-key-123")
    return AppConfig()


class TestMCPServer:
    """Test server construction and tool registration."""

    def test_server_constructs(self, config):
        server = MCPServer(config=config)

        assert server.get_server() is not None

    def test_server_constructs_with_cache_manager(self, config):
        """The cache manager must reach the tools, not just the server."""
        manager = CacheManager(MemoryCache(), ttl=60)
        server = MCPServer(config=config, cache_manager=manager)

        assert server.tools["search_opportunities"].cache_manager is manager

    def test_search_tool_is_registered(self, config):
        server = MCPServer(config=config)

        assert "search_opportunities" in server.tools

    def test_tool_exposes_a_valid_mcp_schema(self, config):
        server = MCPServer(config=config)
        tool = server.tools["search_opportunities"]

        assert tool.name == "search_opportunities"
        assert tool.description
        assert tool.input_schema["type"] == "object"
        assert tool.input_schema["required"] == ["posted_from", "posted_to"]

    @pytest.mark.asyncio
    async def test_stop_is_idempotent_without_cache(self, config):
        server = MCPServer(config=config)

        await server.stop()
