"""Base tool class for SAM.gov MCP tools."""

from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Base class for MCP tools."""

    def __init__(
        self,
        api_client,
        response_mapper,
        validator,
        cache_manager: Any | None = None,
    ):
        """Initialize the tool.

        Args:
            api_client: :class:`~sam_gov_mcp.api_client.SamApiClient` instance.
            response_mapper: :class:`~sam_gov_mcp.response_mapper.ResponseMapper`
                instance.
            validator: :class:`~sam_gov_mcp.validators.ParameterValidator`
                instance.
            cache_manager: Optional
                :class:`~sam_gov_mcp.cache.CacheManager` used to memoize
                responses.
        """
        self.api_client = api_client
        self.response_mapper = response_mapper
        self.validator = validator
        self.cache_manager = cache_manager

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description."""

    @property
    @abstractmethod
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input."""

    @abstractmethod
    async def execute(self, **kwargs) -> dict[str, Any]:
        """Execute the tool.

        Args:
            **kwargs: Tool-specific parameters.

        Returns:
            Tool result.
        """
