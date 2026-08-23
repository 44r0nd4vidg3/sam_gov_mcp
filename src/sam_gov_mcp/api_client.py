"""HTTP client for the SAM.gov API."""

import asyncio
import logging
from typing import Any

import httpx

from sam_gov_mcp.config import SamApiConfig
from sam_gov_mcp.errors import (
    APIError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    ServerError,
)

logger = logging.getLogger(__name__)


class SamApiClient:
    """Client for the SAM.gov Get Opportunities API."""

    def __init__(self, config: SamApiConfig):
        """Initialize the API client.

        Args:
            config: SAM API configuration.
        """
        self.config = config
        self.base_url = (
            config.api_url
            if config.environment == "production"
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
    ) -> dict[str, Any]:
        """Search for opportunities.

        Transport failures and 5xx responses are retried with exponential
        backoff up to ``config.max_retries`` attempts. Client errors (4xx)
        are raised immediately, since retrying them cannot help.

        Args:
            posted_from: Start date (MM/dd/yyyy).
            posted_to: End date (MM/dd/yyyy).
            limit: Records per page (1-1000).
            offset: Page offset.
            **filters: Additional filter parameters.

        Returns:
            API response data.

        Raises:
            AuthenticationError: If the API key is invalid.
            BadRequestError: If the request is malformed.
            NotFoundError: If no opportunities are found.
            ServerError: If the API keeps returning a server error.
            APIError: For transport failures and unexpected statuses.
        """
        params: dict[str, Any] = {
            "api_key": self.config.api_key,
            "postedFrom": posted_from,
            "postedTo": posted_to,
            "limit": limit,
            "offset": offset,
        }

        for key, value in filters.items():
            if value is not None:
                params[key] = value

        attempts = max(1, self.config.max_retries)
        last_error: Exception | None = None

        for attempt in range(1, attempts + 1):
            try:
                response = await self.client.get(self.base_url, params=params)
                return self._handle_response(response)
            except APIError as exc:
                # Only server-side and transport problems are worth retrying.
                if isinstance(exc, (AuthenticationError, BadRequestError, NotFoundError)):
                    raise
                last_error = exc
            except httpx.RequestError as exc:
                logger.warning("API request failed (attempt %s/%s): %s", attempt, attempts, exc)
                last_error = APIError(f"API request failed: {exc}")

            if attempt < attempts:
                await asyncio.sleep(2 ** (attempt - 1))

        assert last_error is not None  # loop always records an error before exiting
        raise last_error

    @staticmethod
    def _safe_json(response: httpx.Response) -> dict[str, Any] | None:
        """Return the response body as JSON, or ``None`` if it is not JSON.

        SAM.gov returns HTML error pages for some failures. Parsing those
        eagerly inside an error branch would replace the real error with a
        JSON decode error.
        """
        try:
            return response.json()
        except ValueError:
            return None

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Map an HTTP response onto a result or a typed exception.

        Args:
            response: HTTP response.

        Returns:
            Response JSON data.

        Raises:
            AuthenticationError: For 401/403 responses.
            BadRequestError: For 400 responses.
            NotFoundError: For 404 responses.
            ServerError: For 5xx responses.
            APIError: For other unsuccessful responses or unparseable bodies.
        """
        status = response.status_code
        body = self._safe_json(response)

        if status in (401, 403):
            raise AuthenticationError(
                "Authentication failed: invalid or missing API key",
                status_code=status,
                response_data=body,
            )
        if status == 400:
            raise BadRequestError(
                "Bad request: invalid parameters",
                status_code=status,
                response_data=body,
            )
        if status == 404:
            raise NotFoundError(
                "No opportunities found",
                status_code=status,
                response_data=body,
            )
        if status == 429:
            raise APIError(
                "Rate limited by SAM.gov; retry later",
                status_code=status,
                response_data=body,
            )
        if status >= 500:
            raise ServerError(
                "Server error occurred",
                status_code=status,
                response_data=body,
            )
        if not response.is_success:
            raise APIError(
                f"API error: HTTP {status}",
                status_code=status,
                response_data=body,
            )

        if body is None:
            raise APIError("API returned a non-JSON response", status_code=status)

        return body

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
