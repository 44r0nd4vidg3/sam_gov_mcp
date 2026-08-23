"""MCP server implementation for the SAM.gov Opportunities API."""

import json
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from sam_gov_mcp.api_client import SamApiClient
from sam_gov_mcp.cache import CacheManager
from sam_gov_mcp.config import AppConfig
from sam_gov_mcp.response_mapper import ResponseMapper
from sam_gov_mcp.tools import SearchOpportunitiesTool
from sam_gov_mcp.validators import ParameterValidator

logger = logging.getLogger(__name__)


class MCPServer:
    """Model Context Protocol server for SAM.gov."""

    def __init__(
        self,
        config: AppConfig | None = None,
        cache_manager: CacheManager | None = None,
    ):
        """Initialize the MCP server.

        Args:
            config: Application configuration (loaded from the environment
                and ``.env`` when omitted).
            cache_manager: Cache manager instance, or ``None`` to disable
                caching.
        """
        self.config = config or AppConfig()
        self.cache_manager = cache_manager
        self.mcp = Server("sam-gov-mcp")

        # Initialize components
        self.api_client = SamApiClient(self.config.sam_api)
        self.response_mapper = ResponseMapper()
        self.validator = ParameterValidator()

        # Initialize tools
        self.tools = {
            "search_opportunities": SearchOpportunitiesTool(
                self.api_client,
                self.response_mapper,
                self.validator,
                cache_manager=cache_manager,
            ),
        }

        # Register MCP handlers
        self._register_handlers()

        logger.info("MCP Server initialized with tools: %s", ", ".join(self.tools))

    def _register_handlers(self) -> None:
        """Register MCP protocol handlers."""

        @self.mcp.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools."""
            return [
                Tool(
                    name=tool.name,
                    description=tool.description,
                    inputSchema=tool.input_schema,
                )
                for tool in self.tools.values()
            ]

        @self.mcp.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """Call a tool by name."""
            if name not in self.tools:
                raise ValueError(f"Unknown tool: {name}")

            tool = self.tools[name]
            result = await tool.execute(**arguments)

            # Serialize as JSON rather than str() so the client receives
            # parseable output instead of a Python repr.
            return [
                TextContent(
                    type="text",
                    text=json.dumps(result, indent=2, default=str),
                )
            ]

    async def start(self) -> None:
        """Serve over the stdio transport until the client disconnects.

        This coroutine blocks for the lifetime of the connection. The MCP
        client (Claude Desktop, Cline, Cursor, ...) launches this process and
        communicates over its stdin/stdout pipes.
        """
        logger.info("Starting MCP Server on stdio transport")
        async with stdio_server() as (read_stream, write_stream):
            await self.mcp.run(
                read_stream,
                write_stream,
                self.mcp.create_initialization_options(),
            )

    async def stop(self) -> None:
        """Release resources held by the server."""
        logger.info("Stopping MCP Server...")
        await self.api_client.close()
        if self.cache_manager:
            await self.cache_manager.close()
        logger.info("MCP Server stopped")

    def get_server(self) -> Server:
        """Return the underlying MCP server instance."""
        return self.mcp
