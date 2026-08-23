"""Tests for parameter validators."""


import pytest

from sam_gov_mcp.errors import ValidationError
from sam_gov_mcp.validators import ParameterValidator


class TestDateValidation:
    """Test date validation."""

    def test_valid_date_range(self):
        """Test valid date range."""
        start, end = ParameterValidator.validate_date_range(
            "01/01/2024", "12/31/2024"
        )
        assert start.year == 2024
        assert start.month == 1
        assert end.month == 12

    def test_invalid_date_format(self):
        """Test invalid date format."""
        with pytest.raises(ValidationError):
            ParameterValidator.validate_date_range(
                "2024-01-01", "2024-12-31"
            )

    def test_date_range_exceeds_max(self):
        """Test date range exceeds maximum."""
        with pytest.raises(ValidationError):
            ParameterValidator.validate_date_range(
                "01/01/2024", "12/31/2025"
            )

    def test_start_date_after_end_date(self):
        """Test start date is after end date."""
        with pytest.raises(ValidationError):
            ParameterValidator.validate_date_range(
                "12/31/2024", "01/01/2024"
            )


class TestPaginationValidation:
    """Test pagination validation."""

    def test_valid_pagination(self):
        """Test valid pagination parameters."""
        limit, offset = ParameterValidator.validate_pagination(100, 0)
        assert limit == 100
        assert offset == 0

    def test_invalid_limit(self):
        """Test invalid limit."""
        with pytest.raises(ValidationError):
            ParameterValidator.validate_pagination(2000, 0)

    def test_negative_offset(self):
        """Test negative offset."""
        with pytest.raises(ValidationError):
            ParameterValidator.validate_pagination(100, -1)


class TestProcurementTypeValidation:
    """Test procurement type validation."""

    def test_valid_procurement_type(self):
        """SAM.gov ptype codes are lowercase and must round-trip unchanged."""
        ptype = ParameterValidator.validate_procurement_type("o")
        assert ptype == "o"

    def test_every_documented_procurement_type_is_accepted(self):
        """Regression: the validator used to reject all six valid codes."""
        for code in ("u", "o", "a", "k", "s", "p"):
            assert ParameterValidator.validate_procurement_type(code) == code

    def test_procurement_type_is_case_insensitive(self):
        """Uppercase input is normalized rather than rejected."""
        assert ParameterValidator.validate_procurement_type("O") == "o"

    def test_invalid_procurement_type(self):
        """Test invalid procurement type."""
        with pytest.raises(ValidationError):
            ParameterValidator.validate_procurement_type("x")


class TestNaicsValidation:
    """Test NAICS code validation."""

    def test_valid_naics(self):
        """Test valid NAICS code."""
        ncode = ParameterValidator.validate_naics_code("236115")
        assert ncode == "236115"

    def test_invalid_naics(self):
        """Test invalid NAICS code."""
        with pytest.raises(ValidationError):
            ParameterValidator.validate_naics_code("12345678")
