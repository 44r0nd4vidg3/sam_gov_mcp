"""HTTP client for SAM.gov API."""

import logging
from typing import Dict, Any, Optional
import httpx
from sam_gov_mcp.config import SamApiConfig
from sam_gov_mcp.errors import (
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    ServerError,
    APIError,
)

logger = logging.getLogger(__name__)


class SamApiClient:
    """Client for SAM.gov Get Opportunities API."""

    def __init__(self, config: SamApiConfig):
        """Initialize API client.

        Args:
            config: SAM API configuration
        """
        self.config = config
        self.base_url = (
            config.api_url if config.environment == "production"
            else config.api_alpha_url
        )
        self.client = httpx.AsyncClient(
            timeout=config.timeout,
            headers={"Accept": "application/json"},
        )

    async def search(
        self,
        posted_from: str,
        posted_to: str,
        limit: int = 1,
        offset: int = 0,
        **filters: Any,
    ) -> Dict[str, Any]:
        """Search for opportunities.

        Args:
            posted_from: Start date (MM/dd/yyyy)
            posted_to: End date (MM/dd/yyyy)
            limit: Records per page (1-1000)
            offset: Page offset
            **filters: Additional filter parameters

        Returns:
            API response data

        Raises:
            AuthenticationError: If API key is invalid
            BadRequestError: If request is malformed
            NotFoundError: If no opportunities found
            ServerError: If server error occurs
        """
        params = {
            "api_key": self.config.api_key,
            "postedFrom": posted_from,
            "postedTo": posted_to,
            "limit": limit,
            "offset": offset,
        }

        # Add optional filters
        if filters:
            for key, value in filters.items():
                if value is not None:
                    params[key] = value

        try:
            response = await self.client.get(self.base_url, params=params)
            return self._handle_response(response)
        except httpx.RequestError as e:
            logger.error(f"API request failed: {e}")
            raise APIError(f"API request failed: {str(e)}")

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Handle API response and raise appropriate errors.

        Args:
            response: HTTP response

        Returns:
            Response JSON data

        Raises:
            AuthenticationError: For 401 responses
            BadRequestError: For 400 responses
            NotFoundError: For 404 responses
            ServerError: For 500+ responses
            APIError: For other errors
        """
        try:
            if response.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed: Invalid API key",
                    status_code=response.status_code,
                    response_data=response.json(),
                )
            elif response.status_code == 400:
                raise BadRequestError(
                    "Bad request: Invalid parameters",
                    status_code=response.status_code,
                    response_data=response.json(),
                )
            elif response.status_code == 404:
                raise NotFoundError(
                    "No opportunities found",
                    status_code=response.status_code,
                    response_data=response.json(),
                )
            elif response.status_code >= 500:
                raise ServerError(
                    "Server error occurred",
                    status_code=response.status_code,
                    response_data=response.json(),
                )
            elif not response.is_success:
                raise APIError(
                    f"API error: HTTP {response.status_code}",
                    status_code=response.status_code,
                    response_data=response.json(),
                )

            return response.json()
        except httpx.ResponseNotRead:
            logger.error("Failed to read response")
            raise APIError("Failed to read API response")

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()