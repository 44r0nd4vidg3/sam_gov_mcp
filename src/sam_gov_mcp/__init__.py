"""SAM.gov Opportunities MCP Server.

A modular Model Context Protocol (MCP) server for the SAM.gov Get
Opportunities Public API (v2).
"""

__version__ = "0.2.0"
__author__ = "Aaron Davidge"
__email__ = "aaronthomasthegreat@gmail.com"

__all__ = ["MCPServer", "__version__"]


def __getattr__(name: str):
    """Import the server lazily.

    Keeps ``import sam_gov_mcp`` cheap and, more importantly, keeps a failure
    inside the server module from breaking imports of small leaf modules such
    as ``sam_gov_mcp.validators``.
    """
    if name == "MCPServer":
        from sam_gov_mcp.server import MCPServer

        return MCPServer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
