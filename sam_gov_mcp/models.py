"""Pydantic models for SAM.gov API responses and requests."""

from typing import Optional, List, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field


class PaginationInfo(BaseModel):
    """Pagination information from API response."""

    total_records: int = Field(..., description="Total number of records")
    limit: int = Field(..., description="Records per page")
    offset: int = Field(..., description="Current page offset")


class ContactInfo(BaseModel):
    """Contact information for opportunity."""

    type: Optional[str] = Field(None, description="Contact type")
    email: Optional[str] = Field(None, description="Contact email")
    phone: Optional[str] = Field(None, description="Contact phone")
    name: Optional[str] = Field(None, description="Contact name")


class AwardInfo(BaseModel):
    """Award information for opportunity."""

    amount: Optional[float] = Field(None, description="Award amount")
    date: Optional[str] = Field(None, description="Award date")
    awardee_name: Optional[str] = Field(None, description="Awardee name")
    awardee_uei: Optional[str] = Field(None, description="Awardee UEI SAM")


class ResourceLink(BaseModel):
    """Resource link for opportunity."""

    link: str = Field(..., description="Resource URL")
    rel: Optional[str] = Field(None, description="Link relationship type")
    title: Optional[str] = Field(None, description="Link title")


class Opportunity(BaseModel):
    """SAM.gov opportunity record."""

    id: str = Field(..., description="Unique opportunity ID")
    title: str = Field(..., description="Opportunity title")
    solicitation_number: str = Field(..., description="Solicitation number")
    posted_date: datetime = Field(..., description="Posted date")
    description: str = Field(..., description="Description or link to description")
    agency: Optional[str] = Field(None, description="Sponsoring agency")
    status: Optional[str] = Field(None, description="Opportunity status")
    procurement_type: Optional[str] = Field(None, description="Procurement type")
    set_aside_type: Optional[str] = Field(None, description="Set-aside type")
    naics_code: Optional[str] = Field(None, description="NAICS code")
    ui_link: Optional[str] = Field(None, description="Direct SAM.gov web interface link")
    contact_info: Optional[List[ContactInfo]] = Field(None, description="Contact information")
    award_info: Optional[AwardInfo] = Field(None, description="Award information")
    resource_links: Optional[List[ResourceLink]] = Field(None, description="Resource links")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class SearchRequest(BaseModel):
    """Search request parameters."""

    posted_from: str = Field(..., description="Start date (MM/dd/yyyy)")
    posted_to: str = Field(..., description="End date (MM/dd/yyyy)")
    limit: int = Field(default=1, ge=1, le=1000, description="Records per page")
    offset: int = Field(default=0, ge=0, description="Page offset")
    ptype: Optional[str] = Field(None, description="Procurement type code")
    ncode: Optional[str] = Field(None, description="NAICS code")
    status: Optional[str] = Field(None, description="Status filter")
    type_of_set_aside: Optional[str] = Field(None, description="Set-aside code")
    keyword: Optional[str] = Field(None, description="Keyword search")


class SearchResponse(BaseModel):
    """Search response."""

    pagination: PaginationInfo = Field(..., description="Pagination information")
    opportunities: List[Opportunity] = Field(..., description="Opportunities list")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Response metadata")