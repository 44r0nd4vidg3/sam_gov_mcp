"""Tests for the search tool, including cache behaviour."""

from unittest.mock import AsyncMock

import pytest

from sam_gov_mcp.cache import CacheManager, MemoryCache
from sam_gov_mcp.errors import AuthenticationError
from sam_gov_mcp.response_mapper import ResponseMapper
from sam_gov_mcp.tools import SearchOpportunitiesTool
from sam_gov_mcp.validators import ParameterValidator

RAW_RESPONSE = {
    "totalRecords": 1,
    "limit": 10,
    "offset": 0,
    "opportunitiesData": [
        {
            "noticeId": "abc123",
            "title": "Custom Computer Programming Services",
            "solicitationNumber": "SOL-001",
            "postedDate": "2024-01-02T00:00:00Z",
        }
    ],
}


def build_tool(api_client, cache_manager=None):
    """Assemble a search tool around a stubbed API client."""
    return SearchOpportunitiesTool(
        api_client,
        ResponseMapper(),
        ParameterValidator(),
        cache_manager=cache_manager,
    )


@pytest.fixture
def api_client():
    client = AsyncMock()
    client.search = AsyncMock(return_value=RAW_RESPONSE)
    return client


class TestSearchOpportunitiesTool:
    """Test the search tool's contract."""

    @pytest.mark.asyncio
    async def test_successful_search(self, api_client):
        result = await build_tool(api_client).execute(
            posted_from="01/01/2024",
            posted_to="03/31/2024",
        )

        assert result["status"] == "success"
        assert result["data"]["pagination"]["total_records"] == 1
        assert result["data"]["opportunities"][0]["title"].startswith("Custom")

    @pytest.mark.asyncio
    async def test_missing_dates_returns_validation_error(self, api_client):
        result = await build_tool(api_client).execute(posted_from="01/01/2024")

        assert result["status"] == "error"
        assert result["error_type"] == "validation_error"

    @pytest.mark.asyncio
    async def test_date_range_over_a_year_is_rejected(self, api_client):
        result = await build_tool(api_client).execute(
            posted_from="01/01/2023",
            posted_to="12/31/2024",
        )

        assert result["error_type"] == "validation_error"
        api_client.search.assert_not_called()

    @pytest.mark.asyncio
    async def test_lowercase_procurement_type_is_accepted(self, api_client):
        """'o' is a valid SAM.gov ptype and must reach the API unchanged."""
        result = await build_tool(api_client).execute(
            posted_from="01/01/2024",
            posted_to="03/31/2024",
            ptype="o",
        )

        assert result["status"] == "success"
        assert api_client.search.call_args.kwargs["ptype"] == "o"

    @pytest.mark.asyncio
    async def test_title_is_forwarded_to_the_api(self, api_client):
        """SAM.gov v2 filters on 'title'; it has no 'keyword' parameter.

        Regression: the tool used to send 'keyword', which the API silently
        ignores -- every search came back unfiltered while looking correct.
        """
        result = await build_tool(api_client).execute(
            posted_from="01/01/2024",
            posted_to="03/31/2024",
            title="web application",
        )

        assert result["status"] == "success"
        assert api_client.search.call_args.kwargs["title"] == "web application"

    @pytest.mark.asyncio
    async def test_unsupported_filters_are_not_forwarded(self, api_client):
        """An unknown filter must not be smuggled into the query string."""
        await build_tool(api_client).execute(
            posted_from="01/01/2024",
            posted_to="03/31/2024",
            keyword="web application",
        )

        assert "keyword" not in api_client.search.call_args.kwargs

    @pytest.mark.asyncio
    async def test_api_errors_are_returned_not_raised(self, api_client):
        api_client.search = AsyncMock(
            side_effect=AuthenticationError("bad key", status_code=401)
        )

        result = await build_tool(api_client).execute(
            posted_from="01/01/2024",
            posted_to="03/31/2024",
        )

        assert result["status"] == "error"
        assert result["error_type"] == "api_error"
        assert result["status_code"] == 401

    @pytest.mark.asyncio
    async def test_second_identical_search_is_served_from_cache(self, api_client):
        tool = build_tool(api_client, CacheManager(MemoryCache(), ttl=60))
        args = {"posted_from": "01/01/2024", "posted_to": "03/31/2024"}

        first = await tool.execute(**args)
        second = await tool.execute(**args)

        assert first["cached"] is False
        assert second["cached"] is True
        assert second["data"] == first["data"]
        api_client.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_different_filters_do_not_share_a_cache_entry(self, api_client):
        tool = build_tool(api_client, CacheManager(MemoryCache(), ttl=60))

        await tool.execute(posted_from="01/01/2024", posted_to="03/31/2024")
        await tool.execute(
            posted_from="01/01/2024", posted_to="03/31/2024", ncode="541511"
        )

        assert api_client.search.call_count == 2
