"""Entry point for the SAM.gov MCP Server."""

import asyncio
import logging
import sys

from sam_gov_mcp.cache import CacheManager, MemoryCache, NoCache
from sam_gov_mcp.config import AppConfig
from sam_gov_mcp.errors import SamMcpException
from sam_gov_mcp.server import MCPServer

logger = logging.getLogger(__name__)


def configure_logging(level: str) -> None:
    """Send logs to stderr.

    The stdio transport owns stdout: anything written there that is not a
    JSON-RPC message corrupts the stream and breaks the client connection.
    """
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )


def create_cache_manager(config: AppConfig) -> CacheManager:
    """Create a cache manager from configuration.

    Args:
        config: Application configuration.

    Returns:
        A configured cache manager. Caching that is disabled is represented
        by a :class:`~sam_gov_mcp.cache.NoCache` backend rather than by
        ``None``, so callers never have to branch on it.
    """
    if not config.cache.enabled:
        logger.info("Caching disabled")
        return CacheManager(NoCache(), ttl=config.cache.ttl)

    if config.cache.cache_type == "none":
        logger.info("Cache type 'none' selected; caching disabled")
        return CacheManager(NoCache(), ttl=config.cache.ttl)

    logger.info("Using memory cache backend (ttl=%ss)", config.cache.ttl)
    return CacheManager(MemoryCache(), ttl=config.cache.ttl)


async def serve() -> None:
    """Load configuration, start the server, and serve until disconnect."""
    config = AppConfig()
    configure_logging(config.mcp_server.log_level)
    logger.info("Configuration loaded (environment=%s)", config.sam_api.environment)

    cache_manager = create_cache_manager(config)
    mcp_server = MCPServer(config=config, cache_manager=cache_manager)

    try:
        await mcp_server.start()
    finally:
        await mcp_server.stop()


def run() -> None:
    """Console-script entry point."""
    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        logger.info("Interrupted; shutting down")
    except SamMcpException as exc:
        logger.error("Server error: %s", exc)
        raise SystemExit(1) from exc
    except Exception as exc:  # noqa: BLE001 - surface startup failures clearly
        logger.error("Failed to start server: %s", exc, exc_info=True)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    run()
