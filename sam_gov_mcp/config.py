"""Configuration management for SAM.gov MCP Server."""

from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings


class SamApiConfig(BaseSettings):
    """SAM.gov API configuration."""

    api_key: str = Field(..., description="SAM.gov public API key")
    api_url: str = Field(
        default="https://api.sam.gov/opportunities/v2/search",
        description="SAM.gov API endpoint URL"
    )
    api_alpha_url: str = Field(
        default="https://api-alpha.sam.gov/opportunities/v2/search",
        description="SAM.gov Alpha API endpoint URL"
    )
    environment: Literal["production", "alpha"] = Field(
        default="production",
        description="API environment to use"
    )
    timeout: int = Field(default=30, description="API request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retries")

    class Config:
        env_prefix = "SAM_"
        case_sensitive = False


class MCPServerConfig(BaseSettings):
    """MCP Server configuration."""

    port: int = Field(default=8000, description="Server port")
    host: str = Field(default="0.0.0.0", description="Server host")
    debug: bool = Field(default=False, description="Debug mode")

    class Config:
        env_prefix = "MCP_SERVER_"
        case_sensitive = False


class CacheConfig(BaseSettings):
    """Cache configuration."""

    enabled: bool = Field(default=False, description="Enable caching")
    ttl: int = Field(default=3600, description="Cache TTL in seconds")
    cache_type: Literal["memory", "redis", "sqlite"] = Field(
        default="memory",
        description="Cache backend type"
    )
    redis_url: str = Field(
        default="redis://localhost:6379",
        description="Redis URL for redis cache type"
    )
    sqlite_path: str = Field(
        default="./cache.db",
        description="SQLite database path for sqlite cache type"
    )

    class Config:
        env_prefix = "CACHE_"
        case_sensitive = False


class AppConfig(BaseSettings):
    """Main application configuration."""

    sam_api: SamApiConfig = Field(default_factory=SamApiConfig)
    mcp_server: MCPServerConfig = Field(default_factory=MCPServerConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)

    class Config:
        env_file = ".env"
        case_sensitive = False