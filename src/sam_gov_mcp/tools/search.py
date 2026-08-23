"""Search opportunities tool."""

import logging
from typing import Any

from sam_gov_mcp.errors import APIError, ValidationError
from sam_gov_mcp.tools.base import BaseTool

logger = logging.getLogger(__name__)


class SearchOpportunitiesTool(BaseTool):
    """Tool for searching SAM.gov opportunities."""

    @property
    def name(self) -> str:
        return "search_opportunities"

    @property
    def description(self) -> str:
        return (
            "Search federal procurement opportunities on SAM.gov. Supports "
            "filtering by date range, procurement type, NAICS code, status, "
            "and set-aside type. The date range cannot exceed one year."
        )

    @property
    def input_schema(self) -> dict[str, Any]:
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
                    "description": (
                        "Procurement type (u=Justification, o=Solicitation, "
                        "a=Award, k=Combined Synopsis/Solicitation, "
                        "s=Special Notice, p=Presolicitation)"
                    ),
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

    async def execute(self, **kwargs) -> dict[str, Any]:
        """Execute a search.

        Args:
            **kwargs: See :attr:`input_schema`.

        Returns:
            A result envelope: ``{"status": "success", "data": ...}`` on
            success, or ``{"status": "error", "error_type": ..., ...}``.
            Errors are returned rather than raised so the model receives a
            usable message instead of a transport-level failure.
        """
        try:
            posted_from = kwargs.get("posted_from")
            posted_to = kwargs.get("posted_to")
            limit = kwargs.get("limit", 10)
            offset = kwargs.get("offset", 0)

            if not posted_from or not posted_to:
                raise ValidationError("posted_from and posted_to are required")

            self.validator.validate_date_range(posted_from, posted_to)
            limit, offset = self.validator.validate_pagination(limit, offset)

            filters = self._build_filters(kwargs)

            cache_key = None
            if self.cache_manager is not None:
                cache_key = self.cache_manager.make_key(
                    self.name,
                    {
                        "posted_from": posted_from,
                        "posted_to": posted_to,
                        "limit": limit,
                        "offset": offset,
                        **filters,
                    },
                )
                cached = await self.cache_manager.get(cache_key)
                if cached is not None:
                    logger.info("Returning cached results for %s", cache_key)
                    return {"status": "success", "cached": True, "data": cached}

            logger.info("Searching opportunities: %s to %s", posted_from, posted_to)
            raw_response = await self.api_client.search(
                posted_from=posted_from,
                posted_to=posted_to,
                limit=limit,
                offset=offset,
                **filters,
            )

            response = self.response_mapper.map_search_response(raw_response)
            payload = response.model_dump(mode="json")

            if cache_key is not None:
                await self.cache_manager.set(cache_key, payload)

            return {"status": "success", "cached": False, "data": payload}

        except ValidationError as exc:
            logger.error("Validation error: %s", exc)
            return {
                "status": "error",
                "error_type": "validation_error",
                "message": str(exc),
            }
        except APIError as exc:
            logger.error("API error: %s", exc)
            return {
                "status": "error",
                "error_type": "api_error",
                "message": exc.message,
                "status_code": exc.status_code,
            }
        except Exception as exc:  # noqa: BLE001 - never break the MCP call
            logger.exception("Unexpected error during search")
            return {
                "status": "error",
                "error_type": "unexpected_error",
                "message": str(exc),
            }

    def _build_filters(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Validate and translate optional filters into API parameter names."""
        filters: dict[str, Any] = {}

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

        return filters
