"""Tests for response mapper."""

import pytest
from datetime import datetime
from sam_gov_mcp.response_mapper import ResponseMapper
from sam_gov_mcp.errors import ValidationError


@pytest.fixture
def mapper():
    """Create response mapper."""
    return ResponseMapper()


class TestResponseMapper:
    """Test response mapping."""

    def test_map_search_response_success(self, mapper):
        """Test successful response mapping."""
        raw_response = {
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
                    "agency": "Test Agency",
                    "status": "active",
                }
            ],
        }
        
        response = mapper.map_search_response(raw_response, "test-api-key")
        
        assert response.pagination.total_records == 1
        assert response.pagination.limit == 10
        assert len(response.opportunities) == 1
        assert response.opportunities[0].title == "Test Opportunity"
        assert response.opportunities[0].agency == "Test Agency"

    def test_map_opportunity_with_contacts(self, mapper):
        """Test mapping opportunity with contact info."""
        raw_response = {
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
                    "pointOfContact": [
                        {
                            "type": "Primary",
                            "email": "test@example.com",
                            "phone": "123-456-7890",
                            "name": "John Doe",
                        }
                    ],
                }
            ],
        }
        
        response = mapper.map_search_response(raw_response, "test-api-key")
        
        assert len(response.opportunities[0].contact_info) == 1
        assert response.opportunities[0].contact_info[0].email == "test@example.com"

    def test_map_opportunity_with_award_info(self, mapper):
        """Test mapping opportunity with award info."""
        raw_response = {
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
                    "award": {
                        "amount": 1000000,
                        "date": "2024-01-15",
                        "awardeeName": "Test Company",
                        "awardeeUeiSAM": "123456789ABC",
                    },
                }
            ],
        }
        
        response = mapper.map_search_response(raw_response, "test-api-key")
        
        assert response.opportunities[0].award_info is not None
        assert response.opportunities[0].award_info.amount == 1000000
        assert response.opportunities[0].award_info.awardee_name == "Test Company"

    def test_map_opportunity_description_with_api_key(self, mapper):
        """Test that API key is appended to description link."""
        raw_response = {
            "totalRecords": 1,
            "limit": 10,
            "offset": 0,
            "opportunitiesData": [
                {
                    "_id": "123",
                    "title": "Test Opportunity",
                    "solicitationNumber": "SOL-001",
                    "postedDate": "2024-01-01T00:00:00Z",
                    "description": "https://api.sam.gov/opportunities/v2/search/123/description",
                }
            ],
        }
        
        response = mapper.map_search_response(raw_response, "test-api-key")
        
        assert "?api_key=test-api-key" in response.opportunities[0].description

    def test_map_empty_response(self, mapper):
        """Test mapping empty response."""
        raw_response = {
            "totalRecords": 0,
            "limit": 10,
            "offset": 0,
            "opportunitiesData": [],
        }
        
        response = mapper.map_search_response(raw_response, "test-api-key")
        
        assert response.pagination.total_records == 0
        assert len(response.opportunities) == 0
