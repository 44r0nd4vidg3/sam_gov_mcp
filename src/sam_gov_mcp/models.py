"""Pydantic models for SAM.gov API responses and requests."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PaginationInfo(BaseModel):
    """Pagination information from API response."""

    total_records: int = Field(..., description="Total number of records")
    limit: int = Field(..., description="Records per page")
    offset: int = Field(..., description="Current page offset")


class ContactInfo(BaseModel):
    """Contact information for opportunity."""

    type: str | None = Field(None, description="Contact type")
    email: str | None = Field(None, description="Contact email")
    phone: str | None = Field(None, description="Contact phone")
    name: str | None = Field(None, description="Contact name")


class AwardInfo(BaseModel):
    """Award information for opportunity."""

    amount: float | None = Field(None, description="Award amount")
    date: str | None = Field(None, description="Award date")
    awardee_name: str | None = Field(None, description="Awardee name")
    awardee_uei: str | None = Field(None, description="Awardee UEI SAM")


class ResourceLink(BaseModel):
    """Resource link for opportunity."""

    link: str = Field(..., description="Resource URL")
    rel: str | None = Field(None, description="Link relationship type")
    title: str | None = Field(None, description="Link title")


class Opportunity(BaseModel):
    """SAM.gov opportunity record."""

    id: str = Field(..., description="Unique opportunity ID")
    title: str = Field(..., description="Opportunity title")
    solicitation_number: str = Field(..., description="Solicitation number")
    posted_date: datetime = Field(..., description="Posted date")
    description: str = Field(..., description="Description or link to description")
    agency: str | None = Field(None, description="Sponsoring agency")
    status: str | None = Field(None, description="Opportunity status")
    procurement_type: str | None = Field(None, description="Procurement type")
    set_aside_type: str | None = Field(None, description="Set-aside type")
    naics_code: str | None = Field(None, description="NAICS code")
    ui_link: str | None = Field(None, description="Direct SAM.gov web interface link")
    contact_info: list[ContactInfo] | None = Field(None, description="Contact information")
    award_info: AwardInfo | None = Field(None, description="Award information")
    resource_links: list[ResourceLink] | None = Field(None, description="Resource links")
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata")


class SearchRequest(BaseModel):
    """Search request parameters."""

    posted_from: str = Field(..., description="Start date (MM/dd/yyyy)")
    posted_to: str = Field(..., description="End date (MM/dd/yyyy)")
    limit: int = Field(default=1, ge=1, le=1000, description="Records per page")
    offset: int = Field(default=0, ge=0, description="Page offset")
    ptype: str | None = Field(None, description="Procurement type code")
    ncode: str | None = Field(None, description="NAICS code")
    status: str | None = Field(None, description="Status filter")
    type_of_set_aside: str | None = Field(None, description="Set-aside code")
    keyword: str | None = Field(None, description="Keyword search")


class SearchResponse(BaseModel):
    """Search response."""

    pagination: PaginationInfo = Field(..., description="Pagination information")
    opportunities: list[Opportunity] = Field(..., description="Opportunities list")
    metadata: dict[str, Any] | None = Field(None, description="Response metadata")