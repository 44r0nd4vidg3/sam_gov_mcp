"""Tests for API client."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from sam_gov_mcp.api_client import SamApiClient
from sam_gov_mcp.config import SamApiConfig
from sam_gov_mcp.errors import (
    APIError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    ServerError,
)


@pytest.fixture
def api_config():
    """Create test API config."""
    return SamApiConfig(
        api_key="test-key-123",
        api_url="https://api.sam.gov/opportunities/v2/search",
        timeout=30,
        max_retries=1,  # no backoff sleeps in tests
    )


@pytest.fixture
def api_client(api_config):
    """Create test API client."""
    return SamApiClient(api_config)


class TestSamApiClient:
    """Test SAM API client."""

    @pytest.mark.asyncio
    async def test_search_success(self, api_client):
        """Test successful search."""
        # Mock the HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = {
            "totalRecords": 1,
            "limit": 10,
            "offset": 0,
            "opportunitiesData": [
                {
                    "_id": "123",
                    "title": "Test Opportunity",
                    "solicitationNumber": "SOL-001",
                    "postedDate": "2024-01-01T00:00:00Z",
                    "description": "Test description",
                }
            ],
        }
        
        # Mock the client get method
        api_client.client.get = AsyncMock(return_value=mock_response)
        
        result = await api_client.search(
            posted_from="01/01/2024",
            posted_to="12/31/2024",
            limit=10,
        )
        
        assert result["totalRecords"] == 1
        assert len(result["opportunitiesData"]) == 1

    @pytest.mark.asyncio
    async def test_authentication_error(self, api_client):
        """Test 401 authentication error."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Invalid API key"}
        
        api_client.client.get = AsyncMock(return_value=mock_response)
        
        with pytest.raises(AuthenticationError):
            await api_client.search(
                posted_from="01/01/2024",
                posted_to="12/31/2024",
            )

    @pytest.mark.asyncio
    async def test_bad_request_error(self, api_client):
        """Test 400 bad request error."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Invalid parameters"}
        
        api_client.client.get = AsyncMock(return_value=mock_response)
        
        with pytest.raises(BadRequestError):
            await api_client.search(
                posted_from="01/01/2024",
                posted_to="12/31/2024",
            )

    @pytest.mark.asyncio
    async def test_not_found_error(self, api_client):
        """Test 404 not found error."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "No opportunities found"}
        
        api_client.client.get = AsyncMock(return_value=mock_response)
        
        with pytest.raises(NotFoundError):
            await api_client.search(
                posted_from="01/01/2024",
                posted_to="12/31/2024",
            )

    @pytest.mark.asyncio
    async def test_server_error(self, api_client):
        """Test 500 server error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Internal server error"}
        
        api_client.client.get = AsyncMock(return_value=mock_response)
        
        with pytest.raises(ServerError):
            await api_client.search(
                posted_from="01/01/2024",
                posted_to="12/31/2024",
            )

    @pytest.mark.asyncio
    async def test_search_with_filters(self, api_client):
        """Test search with optional filters."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = {
            "totalRecords": 0,
            "opportunitiesData": [],
        }
        
        api_client.client.get = AsyncMock(return_value=mock_response)
        
        await api_client.search(
            posted_from="01/01/2024",
            posted_to="12/31/2024",
            ptype="O",
            ncode="236115",
            status="active",
        )
        
        # Verify the call was made with correct params
        api_client.client.get.assert_called_once()
        call_args = api_client.client.get.call_args
        assert call_args[1]["params"]["ptype"] == "O"
        assert call_args[1]["params"]["ncode"] == "236115"

    @pytest.mark.asyncio
    async def test_rate_limited(self, api_client):
        """Test 429 responses surface as APIError."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"error": "Too many requests"}

        api_client.client.get = AsyncMock(return_value=mock_response)

        with pytest.raises(APIError):
            await api_client.search(
                posted_from="01/01/2024",
                posted_to="12/31/2024",
            )

    @pytest.mark.asyncio
    async def test_html_error_body_does_not_mask_status(self, api_client):
        """A non-JSON error body must still raise the status-specific error.

        SAM.gov serves HTML error pages for some failures; parsing the body
        eagerly used to raise a JSON decode error instead of ServerError.
        """
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.side_effect = ValueError("not json")

        api_client.client.get = AsyncMock(return_value=mock_response)

        with pytest.raises(ServerError):
            await api_client.search(
                posted_from="01/01/2024",
                posted_to="12/31/2024",
            )

    @pytest.mark.asyncio
    async def test_retries_transport_errors(self, api_config):
        """Transport failures are retried up to max_retries."""
        api_config.max_retries = 3
        client = SamApiClient(api_config)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = {"totalRecords": 0, "opportunitiesData": []}

        client.client.get = AsyncMock(
            side_effect=[httpx.RequestError("boom"), mock_response]
        )

        with patch("asyncio.sleep", new=AsyncMock()):
            await client.search(
                posted_from="01/01/2024",
                posted_to="12/31/2024",
            )

        assert client.client.get.call_count == 2
        await client.close()
