"""Tests for the response mapper."""

import pytest

from sam_gov_mcp.response_mapper import ResponseMapper


@pytest.fixture
def mapper():
    """Create response mapper."""
    return ResponseMapper()


def _envelope(record: dict) -> dict:
    """Wrap a single opportunity record in a search-response envelope."""
    return {
        "totalRecords": 1,
        "limit": 10,
        "offset": 0,
        "opportunitiesData": [record],
    }


class TestResponseMapper:
    """Test response mapping."""

    def test_map_search_response_success(self, mapper):
        """Test successful response mapping."""
        response = mapper.map_search_response(
            _envelope(
                {
                    "noticeId": "123",
                    "title": "Test Opportunity",
                    "solicitationNumber": "SOL-001",
                    "postedDate": "2024-01-01T00:00:00Z",
                    "description": "https://api.sam.gov/.../description",
                    "fullParentPathName": "Test Agency",
                    "active": "Yes",
                }
            )
        )

        assert response.pagination.total_records == 1
        assert response.pagination.limit == 10
        assert len(response.opportunities) == 1

        opportunity = response.opportunities[0]
        assert opportunity.id == "123"
        assert opportunity.title == "Test Opportunity"
        assert opportunity.agency == "Test Agency"
        assert opportunity.status == "active"

    def test_legacy_id_and_agency_keys_still_map(self, mapper):
        """Older payload keys fall back rather than producing nulls."""
        response = mapper.map_search_response(
            _envelope(
                {
                    "_id": "legacy-id",
                    "title": "Test Opportunity",
                    "solicitationNumber": "SOL-001",
                    "postedDate": "2024-01-01T00:00:00Z",
                    "agency": "Test Agency",
                }
            )
        )

        assert response.opportunities[0].id == "legacy-id"
        assert response.opportunities[0].agency == "Test Agency"

    def test_contact_uses_full_name(self, mapper):
        """SAM.gov returns 'fullName' for a point of contact, not 'name'."""
        response = mapper.map_search_response(
            _envelope(
                {
                    "noticeId": "123",
                    "title": "Test Opportunity",
                    "solicitationNumber": "SOL-001",
                    "postedDate": "2024-01-01T00:00:00Z",
                    "pointOfContact": [
                        {
                            "type": "primary",
                            "email": "test@example.com",
                            "phone": "123-456-7890",
                            "fullName": "John Doe",
                        }
                    ],
                }
            )
        )

        contacts = response.opportunities[0].contact_info
        assert len(contacts) == 1
        assert contacts[0].email == "test@example.com"
        assert contacts[0].name == "John Doe"

    def test_award_with_nested_awardee(self, mapper):
        """Awardee details are nested under 'award.awardee'."""
        response = mapper.map_search_response(
            _envelope(
                {
                    "noticeId": "123",
                    "title": "Test Opportunity",
                    "solicitationNumber": "SOL-001",
                    "postedDate": "2024-01-01T00:00:00Z",
                    "award": {
                        "amount": "1000000",
                        "date": "2024-01-15",
                        "awardee": {"name": "Test Company", "ueiSAM": "123456789ABC"},
                    },
                }
            )
        )

        award = response.opportunities[0].award_info
        assert award is not None
        assert award.amount == 1000000
        assert award.awardee_name == "Test Company"
        assert award.awardee_uei == "123456789ABC"

    def test_award_with_flat_awardee(self, mapper):
        """Flat awardee keys are still accepted."""
        response = mapper.map_search_response(
            _envelope(
                {
                    "noticeId": "123",
                    "title": "Test Opportunity",
                    "solicitationNumber": "SOL-001",
                    "postedDate": "2024-01-01T00:00:00Z",
                    "award": {
                        "amount": 1000000,
                        "date": "2024-01-15",
                        "awardeeName": "Test Company",
                        "awardeeUeiSAM": "123456789ABC",
                    },
                }
            )
        )

        award = response.opportunities[0].award_info
        assert award.awardee_name == "Test Company"
        assert award.awardee_uei == "123456789ABC"

    def test_empty_award_block_maps_to_none(self, mapper):
        """Unawarded notices return {"award": {"awardee": {}}}.

        That dict is truthy, so the mapper used to build an AwardInfo with
        every field null instead of omitting the award entirely.
        """
        response = mapper.map_search_response(
            _envelope(
                {
                    "noticeId": "123",
                    "title": "Test Opportunity",
                    "solicitationNumber": "SOL-001",
                    "postedDate": "2024-01-01T00:00:00Z",
                    "award": {"awardee": {}},
                }
            )
        )

        assert response.opportunities[0].award_info is None

    def test_partial_award_is_kept(self, mapper):
        """An award with any real value is still returned."""
        response = mapper.map_search_response(
            _envelope(
                {
                    "noticeId": "123",
                    "title": "Test Opportunity",
                    "solicitationNumber": "SOL-001",
                    "postedDate": "2024-01-01T00:00:00Z",
                    "award": {"amount": "41685.48", "awardee": {}},
                }
            )
        )

        assert response.opportunities[0].award_info.amount == 41685.48

    def test_api_key_is_never_embedded_in_output(self, mapper):
        """The API key must not leak into tool output.

        The description field is a URL that needs the key appended to fetch.
        Doing that here would put the credential into model context, chat
        transcripts, and logs, so the raw URL is returned instead.
        """
        url = "https://api.sam.gov/opportunities/v2/search/123/description"
        response = mapper.map_search_response(_envelope({
            "noticeId": "123",
            "title": "Test Opportunity",
            "solicitationNumber": "SOL-001",
            "postedDate": "2024-01-01T00:00:00Z",
            "description": url,
        }))

        assert response.opportunities[0].description == url
        assert "api_key" not in response.opportunities[0].description

    def test_malformed_record_is_skipped(self, mapper):
        """A bad record is dropped instead of failing the whole search."""
        response = mapper.map_search_response(
            {
                "totalRecords": 2,
                "limit": 10,
                "offset": 0,
                "opportunitiesData": [
                    "not-a-dict",
                    {
                        "noticeId": "123",
                        "title": "Good Record",
                        "solicitationNumber": "SOL-001",
                        "postedDate": "2024-01-01T00:00:00Z",
                    },
                ],
            }
        )

        assert len(response.opportunities) == 1
        assert response.opportunities[0].title == "Good Record"

    def test_unparseable_date_does_not_raise(self, mapper):
        """A bad postedDate falls back instead of dropping the record."""
        response = mapper.map_search_response(
            _envelope(
                {
                    "noticeId": "123",
                    "title": "Test Opportunity",
                    "solicitationNumber": "SOL-001",
                    "postedDate": "not-a-date",
                }
            )
        )

        assert len(response.opportunities) == 1
        assert response.opportunities[0].posted_date is not None

    def test_map_empty_response(self, mapper):
        """Test mapping an empty response."""
        response = mapper.map_search_response(
            {
                "totalRecords": 0,
                "limit": 10,
                "offset": 0,
                "opportunitiesData": [],
            }
        )

        assert response.pagination.total_records == 0
        assert len(response.opportunities) == 0
