"""Base tool class for SAM.gov MCP tools."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseTool(ABC):
    """Base class for MCP tools."""

    def __init__(self, api_client, response_mapper, validator):
        """Initialize base tool.

        Args:
            api_client: SamApiClient instance
            response_mapper: ResponseMapper instance
            validator: ParameterValidator instance
        """
        self.api_client = api_client
        self.response_mapper = response_mapper
        self.validator = validator

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description."""
        pass

    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """JSON Schema for tool input."""
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            Tool result
        """
        pass