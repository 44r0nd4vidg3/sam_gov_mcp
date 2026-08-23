"""Tests for API client."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sam_gov_mcp.api_client import SamApiClient
from sam_gov_mcp.config import SamApiConfig
from sam_gov_mcp.errors import AuthenticationError, BadRequestError, NotFoundError, ServerError


@pytest.fixture
def api_config():
    """Create test API config."""
    return SamApiConfig(
        api_key="test-key-123",
        api_url="https://api.sam.gov/opportunities/v2/search",
        timeout=30,
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
        
        result = await api_client.search(
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
