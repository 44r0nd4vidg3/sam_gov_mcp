"""Validation utilities for search parameters."""

import re
from datetime import datetime
from typing import Tuple
from sam_gov_mcp.errors import ValidationError


class ParameterValidator:
    """Validate search parameters."""

    DATE_FORMAT = "%m/%d/%Y"
    DATE_PATTERN = r"^\d{2}/\d{2}/\d{4}$"
    NAICS_PATTERN = r"^\d{1,6}$"
    PROCUREMENT_TYPES = {"u", "o", "a", "k", "s", "p"}
    STATUSES = {"active", "inactive", "archived", "cancelled", "deleted"}
    SET_ASIDE_CODES = {
        "SBA",
        "8A",
        "WOSB",
        "HUBZONE",
        "VOSB",
        "SDVOSB",
    }

    @staticmethod
    def validate_date_range(
        posted_from: str,
        posted_to: str,
        max_days: int = 365,
    ) -> Tuple[datetime, datetime]:
        """Validate date range parameters.

        Args:
            posted_from: Start date string (MM/dd/yyyy)
            posted_to: End date string (MM/dd/yyyy)
            max_days: Maximum allowed range in days

        Returns:
            Tuple of (start_date, end_date) as datetime objects

        Raises:
            ValidationError: If dates are invalid or range exceeds max_days
        """
        # Validate format
        if not re.match(ParameterValidator.DATE_PATTERN, posted_from):
            raise ValidationError(
                f"Invalid 'postedFrom' format. Expected MM/dd/yyyy, got '{posted_from}'"
            )
        if not re.match(ParameterValidator.DATE_PATTERN, posted_to):
            raise ValidationError(
                f"Invalid 'postedTo' format. Expected MM/dd/yyyy, got '{posted_to}'"
            )

        # Parse dates
        try:
            start_date = datetime.strptime(posted_from, ParameterValidator.DATE_FORMAT)
            end_date = datetime.strptime(posted_to, ParameterValidator.DATE_FORMAT)
        except ValueError as e:
            raise ValidationError(f"Invalid date values: {str(e)}")

        # Validate range
        if start_date > end_date:
            raise ValidationError("'postedFrom' must be before or equal to 'postedTo'")

        day_diff = (end_date - start_date).days
        if day_diff > max_days:
            raise ValidationError(
                f"Date range cannot exceed {max_days} days. "
                f"Your range: {day_diff} days"
            )

        return start_date, end_date

    @staticmethod
    def validate_pagination(
        limit: int,
        offset: int,
        max_limit: int = 1000,
    ) -> Tuple[int, int]:
        """Validate pagination parameters.

        Args:
            limit: Records per page
            offset: Page offset
            max_limit: Maximum allowed limit

        Returns:
            Tuple of (limit, offset) after validation

        Raises:
            ValidationError: If parameters are invalid
        """
        if not isinstance(limit, int) or limit < 1:
            raise ValidationError(f"'limit' must be a positive integer, got {limit}")

        if limit > max_limit:
            raise ValidationError(
                f"'limit' cannot exceed {max_limit}, got {limit}"
            )

        if not isinstance(offset, int) or offset < 0:
            raise ValidationError(f"'offset' must be a non-negative integer, got {offset}")

        return limit, offset

    @staticmethod
    def validate_procurement_type(ptype: str) -> str:
        """Validate procurement type code.

        Args:
            ptype: Procurement type code

        Returns:
            Validated procurement type code

        Raises:
            ValidationError: If procurement type is invalid
        """
        ptype_upper = ptype.upper()
        if ptype_upper not in ParameterValidator.PROCUREMENT_TYPES:
            valid_types = ", ".join(sorted(ParameterValidator.PROCUREMENT_TYPES))
            raise ValidationError(
                f"Invalid procurement type '{ptype}'. "
                f"Valid types: {valid_types}"
            )
        return ptype_upper

    @staticmethod
    def validate_naics_code(ncode: str) -> str:
        """Validate NAICS code.

        Args:
            ncode: NAICS code

        Returns:
            Validated NAICS code

        Raises:
            ValidationError: If NAICS code is invalid
        """
        if not re.match(ParameterValidator.NAICS_PATTERN, ncode):
            raise ValidationError(
                f"Invalid NAICS code '{ncode}'. "
                f"Must be 1-6 digits."
            )
        return ncode

    @staticmethod
    def validate_status(status: str) -> str:
        """Validate status filter.

        Args:
            status: Status value

        Returns:
            Validated status

        Raises:
            ValidationError: If status is invalid
        """
        status_lower = status.lower()
        if status_lower not in ParameterValidator.STATUSES:
            valid_statuses = ", ".join(sorted(ParameterValidator.STATUSES))
            raise ValidationError(
                f"Invalid status '{status}'. "
                f"Valid statuses: {valid_statuses}"
            )
        return status_lower

    @staticmethod
    def validate_set_aside_code(code: str) -> str:
        """Validate set-aside code.

        Args:
            code: Set-aside code

        Returns:
            Validated set-aside code

        Raises:
            ValidationError: If code is invalid
        """
        code_upper = code.upper()
        if code_upper not in ParameterValidator.SET_ASIDE_CODES:
            valid_codes = ", ".join(sorted(ParameterValidator.SET_ASIDE_CODES))
            raise ValidationError(
                f"Invalid set-aside code '{code}'. "
                f"Valid codes: {valid_codes}"
            )
        return code_upper