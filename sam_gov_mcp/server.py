"""MCP Server implementation for SAM.gov API."""

import logging
from typing import Any, Dict, List
from mcp.server import Server
from mcp.types import Tool, TextContent
from sam_gov_mcp.config import AppConfig
from sam_gov_mcp.api_client import SamApiClient
from sam_gov_mcp.response_mapper import ResponseMapper
from sam_gov_mcp.validators import ParameterValidator
from sam_gov_mcp.tools import SearchOpportunitiesTool, GetOpportunityDetailsTool

logger = logging.getLogger(__name__)


class MCPServer:
    """Model Context Protocol Server for SAM.gov."""

    def __init__(self, config: AppConfig = None):
        """Initialize MCP Server.

        Args:
            config: Application configuration (uses .env if None)
        """
        self.config = config or AppConfig()
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
            ),
            "get_opportunity_details": GetOpportunityDetailsTool(
                self.api_client,
                self.response_mapper,
                self.validator,
            ),
        }
        
        # Register MCP handlers
        self._register_handlers()
        
        logger.info("MCP Server initialized")

    def _register_handlers(self):
        """Register MCP protocol handlers."""
        
        @self.mcp.list_tools()
        async def list_tools() -> List[Tool]:
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
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Call a tool by name."""
            if name not in self.tools:
                raise ValueError(f"Unknown tool: {name}")
            
            tool = self.tools[name]
            result = await tool.execute(**arguments)
            
            return [TextContent(type="text", text=str(result))]

    async def start(self):
        """Start the server."""
        logger.info(
            f"Starting MCP Server on {self.config.mcp_server.host}:"
            f"{self.config.mcp_server.port}"
        )
        # Server will be started based on transport (stdio, SSE, etc.)
        # This is handled by the MCP SDK

    async def stop(self):
        """Stop the server."""
        logger.info("Stopping MCP Server...")
        await self.api_client.close()
        logger.info("MCP Server stopped")

    def get_server(self) -> Server:
        """Get the MCP server instance.
        
        Returns:
            MCP Server instance
        """
        return self.mcp