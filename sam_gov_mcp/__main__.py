"""Main entry point for SAM.gov MCP Server."""

import asyncio
import logging
from typing import Optional
from sam_gov_mcp.config import AppConfig
from sam_gov_mcp.server import MCPServer
from sam_gov_mcp.cache import MemoryCache, NoCache, CacheManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_cache_manager(config: AppConfig) -> CacheManager:
    """Create cache manager based on configuration.
    
    Args:
        config: Application configuration
        
    Returns:
        Configured cache manager
    """
    if not config.cache.enabled:
        logger.info("Caching disabled")
        return CacheManager(NoCache(), ttl=config.cache.ttl)
    
    cache_type = config.cache.cache_type
    logger.info(f"Using {cache_type} cache backend")
    
    if cache_type == "memory":
        return CacheManager(MemoryCache(), ttl=config.cache.ttl)
    elif cache_type == "none":
        return CacheManager(NoCache(), ttl=config.cache.ttl)
    else:
        logger.warning(f"Unknown cache type {cache_type}, using memory")
        return CacheManager(MemoryCache(), ttl=config.cache.ttl)


async def main():
    """Main entry point."""
    try:
        # Load configuration
        config = AppConfig()
        logger.info("Configuration loaded")
        logger.info(f"Environment: {config.sam_api.environment}")
        logger.info(f"MCP Server: {config.mcp_server.host}:{config.mcp_server.port}")
        
        # Create cache manager
        cache_manager = create_cache_manager(config)
        
        # Create MCP server
        mcp_server = MCPServer(config=config, cache_manager=cache_manager)
        logger.info("MCP Server created")
        
        # Start server
        await mcp_server.start()
        logger.info("MCP Server started successfully")
        
        # Keep server running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            await mcp_server.stop()
            logger.info("MCP Server stopped")
    
    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())