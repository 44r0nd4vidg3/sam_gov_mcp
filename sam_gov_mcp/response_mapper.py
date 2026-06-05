"""Map SAM.gov API responses to normalized models."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sam_gov_mcp.models import (
    Opportunity,
    SearchResponse,
    PaginationInfo,
    ContactInfo,
    AwardInfo,
    ResourceLink,
)
from sam_gov_mcp.errors import ValidationError

logger = logging.getLogger(__name__)


class ResponseMapper:
    """Map and normalize API responses."""

    def map_search_response(self, data: Dict[str, Any], api_key: str) -> SearchResponse:
        """Map API response to SearchResponse model.

        Args:
            data: Raw API response data
            api_key: API key for description link access

        Returns:
            Normalized SearchResponse

        Raises:
            ValidationError: If data structure is invalid
        """
        try:
            # Extract pagination info
            pagination = PaginationInfo(
                total_records=data.get("totalRecords", 0),
                limit=data.get("limit", 1),
                offset=data.get("offset", 0),
            )

            # Map opportunities
            opportunities = []
            for record in data.get("opportunitiesData", []):
                opportunity = self._map_opportunity(record, api_key)
                if opportunity:
                    opportunities.append(opportunity)

            return SearchResponse(
                pagination=pagination,
                opportunities=opportunities,
                metadata=data.get("metadata", {}),
            )
        except (KeyError, TypeError, ValueError) as e:
            logger.error(f"Failed to map response: {e}")
            raise ValidationError(f"Failed to map API response: {str(e)}")

    def _map_opportunity(self, data: Dict[str, Any], api_key: str) -> Optional[Opportunity]:
        """Map individual opportunity record.

        Args:
            data: Raw opportunity data
            api_key: API key for description link

        Returns:
            Mapped Opportunity or None if mapping fails
        """
        try:
            # Extract basic fields
            opp_id = data.get("_id", data.get("id", ""))
            title = data.get("title", "")
            solicitation_number = data.get("solicitationNumber", "")

            # Parse posted date
            posted_date_str = data.get("postedDate", "")
            try:
                posted_date = datetime.fromisoformat(posted_date_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                posted_date = datetime.now()

            # Handle description with API key
            description = data.get("description", "")
            if description and "?api_key=" not in description and api_key:
                description = f"{description}?api_key={api_key}"

            # Extract contact info
            contact_info = []
            for contact in data.get("pointOfContact", []):
                contact_info.append(
                    ContactInfo(
                        type=contact.get("type"),
                        email=contact.get("email"),
                        phone=contact.get("phone"),
                        name=contact.get("name"),
                    )
                )

            # Extract award info
            award_data = data.get("award", {})
            award_info = None
            if award_data:
                award_info = AwardInfo(
                    amount=award_data.get("amount"),
                    date=award_data.get("date"),
                    awardee_name=award_data.get("awardeeName"),
                    awardee_uei=award_data.get("awardeeUeiSAM"),
                )

            # Extract resource links
            resource_links = []
            for link in data.get("resourceLinks", []):
                resource_links.append(
                    ResourceLink(
                        link=link.get("link", ""),
                        rel=link.get("rel"),
                        title=link.get("title"),
                    )
                )

            return Opportunity(
                id=opp_id,
                title=title,
                solicitation_number=solicitation_number,
                posted_date=posted_date,
                description=description,
                agency=data.get("agency"),
                status=data.get("status"),
                procurement_type=data.get("ptype"),
                set_aside_type=data.get("typeOfSetAside"),
                naics_code=data.get("ncode"),
                ui_link=data.get("uiLink"),
                contact_info=contact_info if contact_info else None,
                award_info=award_info,
                resource_links=resource_links if resource_links else None,
                metadata=data.get("metadata"),
            )
        except Exception as e:
            logger.warning(f"Failed to map opportunity record: {e}")
            return None