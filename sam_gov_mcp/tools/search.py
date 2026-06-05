"""Search opportunities tool."""

import logging
from typing import Any, Dict, Optional
from sam_gov_mcp.tools.base import BaseTool
from sam_gov_mcp.errors import ValidationError, APIError

logger = logging.getLogger(__name__)


class SearchOpportunitiesTool(BaseTool):
    """Tool for searching SAM.gov opportunities."""

    @property
    def name(self) -> str:
        return "search_opportunities"

    @property
    def description(self) -> str:
        return """Search for federal procurement opportunities on SAM.gov.
        
        Supports filtering by date range, procurement type, NAICS code, status, and set-aside type.
        Date range cannot exceed 1 year.
        """

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "posted_from": {
                    "type": "string",
                    "description": "Start date (MM/dd/yyyy format)",
                },
                "posted_to": {
                    "type": "string",
                    "description": "End date (MM/dd/yyyy format)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Records per page (1-1000, default 10)",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 1000,
                },
                "offset": {
                    "type": "integer",
                    "description": "Page offset (default 0)",
                    "default": 0,
                    "minimum": 0,
                },
                "ptype": {
                    "type": "string",
                    "description": "Procurement type (u=Justification, o=Solicitation, a=Award, k=Combined)",
                },
                "ncode": {
                    "type": "string",
                    "description": "NAICS code (1-6 digits)",
                },
                "status": {
                    "type": "string",
                    "enum": ["active", "inactive", "archived", "cancelled", "deleted"],
                    "description": "Opportunity status",
                },
                "type_of_set_aside": {
                    "type": "string",
                    "enum": ["SBA", "8A", "WOSB", "HUBZONE", "VOSB", "SDVOSB"],
                    "description": "Set-aside type",
                },
                "keyword": {
                    "type": "string",
                    "description": "Keyword search term",
                },
            },
            "required": ["posted_from", "posted_to"],
        }

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute search.

        Args:
            posted_from: Start date (MM/dd/yyyy)
            posted_to: End date (MM/dd/yyyy)
            limit: Records per page
            offset: Page offset
            ptype: Procurement type code
            ncode: NAICS code
            status: Status filter
            type_of_set_aside: Set-aside code
            keyword: Keyword search

        Returns:
            Search results with opportunities
        """
        try:
            # Validate required parameters
            posted_from = kwargs.get("posted_from")
            posted_to = kwargs.get("posted_to")
            limit = kwargs.get("limit", 10)
            offset = kwargs.get("offset", 0)

            if not posted_from or not posted_to:
                raise ValidationError("posted_from and posted_to are required")

            # Validate dates
            self.validator.validate_date_range(posted_from, posted_to)

            # Validate pagination
            limit, offset = self.validator.validate_pagination(limit, offset)

            # Build filters
            filters = {}
            
            if kwargs.get("ptype"):
                filters["ptype"] = self.validator.validate_procurement_type(kwargs["ptype"])
            
            if kwargs.get("ncode"):
                filters["ncode"] = self.validator.validate_naics_code(kwargs["ncode"])
            
            if kwargs.get("status"):
                filters["status"] = self.validator.validate_status(kwargs["status"])
            
            if kwargs.get("type_of_set_aside"):
                filters["typeOfSetAside"] = self.validator.validate_set_aside_code(
                    kwargs["type_of_set_aside"]
                )
            
            if kwargs.get("keyword"):
                filters["keyword"] = kwargs["keyword"]

            # Call API
            logger.info(f"Searching opportunities: {posted_from} to {posted_to}")
            raw_response = await self.api_client.search(
                posted_from=posted_from,
                posted_to=posted_to,
                limit=limit,
                offset=offset,
                **filters,
            )

            # Map response
            response = self.response_mapper.map_search_response(
                raw_response,
                self.api_client.config.api_key,
            )

            return {
                "status": "success",
                "data": response.model_dump(),
            }

        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return {
                "status": "error",
                "error_type": "validation_error",
                "message": str(e),
            }
        except APIError as e:
            logger.error(f"API error: {e}")
            return {
                "status": "error",
                "error_type": "api_error",
                "message": e.message,
                "status_code": e.status_code,
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                "status": "error",
                "error_type": "unexpected_error",
                "message": str(e),
            }