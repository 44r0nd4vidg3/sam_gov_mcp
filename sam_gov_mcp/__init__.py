"""SAM.gov Opportunities MCP Server.

A modular Model Context Protocol (MCP) server for the SAM.gov Get Opportunities Public API (v2).
"""

__version__ = "0.1.0"
__author__ = "Aaron Davidge"
__email__ = "aaronthomasthegreat@gmail.com"

from sam_gov_mcp.server import MCPServer

__all__ = ["MCPServer"]