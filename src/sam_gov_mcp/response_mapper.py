"""Map SAM.gov API responses to normalized models.

Field names below follow the Get Opportunities v2 response shape. Where the
API has used more than one name over time, the mapper reads the current name
first and falls back to the older one, so a schema change degrades to a null
field rather than an exception.
"""

import logging
from datetime import datetime
from typing import Any

from sam_gov_mcp.errors import ValidationError
from sam_gov_mcp.models import (
    AwardInfo,
    ContactInfo,
    Opportunity,
    PaginationInfo,
    ResourceLink,
    SearchResponse,
)

logger = logging.getLogger(__name__)


def _first(data: dict[str, Any], *keys: str) -> Any | None:
    """Return the first non-empty value among ``keys``."""
    for key in keys:
        value = data.get(key)
        if value not in (None, "", [], {}):
            return value
    return None


class ResponseMapper:
    """Map and normalize API responses."""

    def map_search_response(self, data: dict[str, Any]) -> SearchResponse:
        """Map an API response to a :class:`SearchResponse`.

        Args:
            data: Raw API response data.

        Returns:
            Normalized :class:`SearchResponse`.

        Raises:
            ValidationError: If the payload does not have the expected shape.
        """
        try:
            pagination = PaginationInfo(
                total_records=data.get("totalRecords", 0),
                limit=data.get("limit", 1),
                offset=data.get("offset", 0),
            )

            opportunities = []
            for record in data.get("opportunitiesData", []):
                opportunity = self._map_opportunity(record)
                if opportunity:
                    opportunities.append(opportunity)

            return SearchResponse(
                pagination=pagination,
                opportunities=opportunities,
                metadata=data.get("metadata", {}),
            )
        except (KeyError, TypeError, ValueError) as exc:
            logger.error("Failed to map response: %s", exc)
            raise ValidationError(f"Failed to map API response: {exc}") from exc

    def _map_opportunity(self, data: dict[str, Any]) -> Opportunity | None:
        """Map a single opportunity record.

        Args:
            data: Raw opportunity data.

        Returns:
            The mapped :class:`Opportunity`, or ``None`` if the record could
            not be mapped. One malformed record should not fail the search.
        """
        try:
            opp_id = _first(data, "noticeId", "_id", "id") or ""
            title = data.get("title") or ""
            solicitation_number = data.get("solicitationNumber") or ""

            posted_date = self._parse_date(data.get("postedDate"))

            # The API returns a URL here, not prose. The key is deliberately
            # NOT appended: tool output is handed to a language model and
            # ends up in transcripts and logs.
            description = data.get("description") or ""

            contact_info = [
                ContactInfo(
                    type=contact.get("type"),
                    email=contact.get("email"),
                    phone=contact.get("phone"),
                    name=_first(contact, "fullName", "name"),
                )
                for contact in data.get("pointOfContact") or []
            ]

            award_info = self._map_award(data.get("award") or {})

            resource_links = [
                ResourceLink(
                    link=link.get("link", "") if isinstance(link, dict) else str(link),
                    rel=link.get("rel") if isinstance(link, dict) else None,
                    title=link.get("title") if isinstance(link, dict) else None,
                )
                for link in data.get("resourceLinks") or []
            ]

            active = data.get("active")
            status = None
            if isinstance(active, str):
                status = "active" if active.lower() == "yes" else "inactive"

            return Opportunity(
                id=opp_id,
                title=title,
                solicitation_number=solicitation_number,
                posted_date=posted_date,
                description=description,
                agency=_first(data, "fullParentPathName", "organizationName", "agency"),
                status=status or data.get("status"),
                procurement_type=_first(data, "type", "baseType", "ptype"),
                set_aside_type=_first(
                    data, "typeOfSetAsideDescription", "typeOfSetAside"
                ),
                naics_code=str(_first(data, "naicsCode", "naicsCodes", "ncode") or "")
                or None,
                ui_link=data.get("uiLink"),
                contact_info=contact_info or None,
                award_info=award_info,
                resource_links=resource_links or None,
                metadata=data.get("metadata"),
            )
        except Exception as exc:  # noqa: BLE001 - skip the record, keep the search
            logger.warning("Failed to map opportunity record: %s", exc)
            return None

    @staticmethod
    def _map_award(award: dict[str, Any]) -> AwardInfo | None:
        """Map the award block, which nests awardee details one level down."""
        if not award:
            return None

        awardee = award.get("awardee") or {}
        return AwardInfo(
            amount=award.get("amount"),
            date=award.get("date"),
            awardee_name=_first(awardee, "name") or award.get("awardeeName"),
            awardee_uei=_first(awardee, "ueiSAM") or award.get("awardeeUeiSAM"),
        )

    @staticmethod
    def _parse_date(value: str | None) -> datetime:
        """Parse a posted date, falling back to now if it is missing/invalid."""
        if not value:
            return datetime.now()
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            logger.debug("Unparseable postedDate: %r", value)
            return datetime.now()
