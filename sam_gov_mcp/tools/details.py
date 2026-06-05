"""Get opportunity details tool."""

import logging
from typing import Any, Dict
from sam_gov_mcp.tools.base import BaseTool
from sam_gov_mcp.errors import ValidationError, APIError

logger = logging.getLogger(__name__)


class GetOpportunityDetailsTool(BaseTool):
    """Tool for getting full details of a specific opportunity."""

    @property
    def name(self) -> str:
        return "get_opportunity_details"

    @property
    def description(self) -> str:
        return """Get detailed information about a specific SAM.gov opportunity.
        
        Use this tool to retrieve full details of an opportunity including
        contacts, attachments, award information, and resource links.
        """

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "opportunity_id": {
                    "type": "string",
                    "description": "The unique ID of the opportunity to retrieve",
                },
                "solicitation_number": {
                    "type": "string",
                    "description": "The solicitation number (alternative to opportunity_id)",
                },
            },
            "anyOf": [
                {"required": ["opportunity_id"]},
                {"required": ["solicitation_number"]},
            ],
        }

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute get details.

        Args:
            opportunity_id: The opportunity ID
            solicitation_number: The solicitation number

        Returns:
            Opportunity details
        """
        try:
            opportunity_id = kwargs.get("opportunity_id")
            solicitation_number = kwargs.get("solicitation_number")

            if not opportunity_id and not solicitation_number:
                raise ValidationError(
                    "Either opportunity_id or solicitation_number must be provided"
                )

            logger.info(
                f"Getting opportunity details: "
                f"id={opportunity_id}, solicitation={solicitation_number}"
            )

            # Note: This is a placeholder.
            # In a real implementation, you would fetch the specific opportunity
            # from the API using the ID or solicitation number.
            # For now, we return a message that this requires a different API endpoint.

            return {
                "status": "info",
                "message": "Detailed opportunity lookup requires the full opportunity object "
                "from a search result. Use search_opportunities first to find opportunities.",
                "note": "The SAM.gov API v2 returns full opportunity details in search results. "
                "For additional details, use the 'uiLink' field to access the SAM.gov web interface.",
            }

        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return {
                "status": "error",
                "error_type": "validation_error",
                "message": str(e),
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                "status": "error",
                "error_type": "unexpected_error",
                "message": str(e),
            }