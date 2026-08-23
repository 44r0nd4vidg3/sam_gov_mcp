"""Configuration management for SAM.gov MCP Server.

Every settings class reads the ``.env`` file as well as the process
environment. The ``env_file`` setting has to be repeated on each nested
class: pydantic-settings resolves nested models independently, so declaring
it only on :class:`AppConfig` would leave ``SAM_API_KEY`` unreadable from
``.env``.
"""

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SamApiConfig(BaseSettings):
    """SAM.gov API configuration."""

    model_config = SettingsConfigDict(
        env_prefix="SAM_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    api_key: str = Field(..., description="SAM.gov public API key")
    api_url: str = Field(
        default="https://api.sam.gov/opportunities/v2/search",
        description="SAM.gov API endpoint URL",
    )
    api_alpha_url: str = Field(
        default="https://api-alpha.sam.gov/opportunities/v2/search",
        description="SAM.gov Alpha API endpoint URL",
    )
    environment: Literal["production", "alpha"] = Field(
        default="production",
        description="API environment to use",
    )
    timeout: int = Field(default=30, description="API request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retries")


class MCPServerConfig(BaseSettings):
    """MCP server configuration.

    The server speaks the stdio transport, so there is no host or port to
    configure: the MCP client launches the process and talks to it over the
    pipe it created.
    """

    model_config = SettingsConfigDict(
        env_prefix="MCP_SERVER_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    debug: bool = Field(default=False, description="Debug mode")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Logging verbosity",
    )


class CacheConfig(BaseSettings):
    """Cache configuration."""

    model_config = SettingsConfigDict(
        env_prefix="CACHE_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    enabled: bool = Field(default=False, description="Enable caching")
    ttl: int = Field(default=3600, description="Cache TTL in seconds")
    cache_type: Literal["memory", "none"] = Field(
        default="memory",
        description="Cache backend type",
    )


class AppConfig(BaseSettings):
    """Top-level application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    sam_api: SamApiConfig = Field(default_factory=SamApiConfig)
    mcp_server: MCPServerConfig = Field(default_factory=MCPServerConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
