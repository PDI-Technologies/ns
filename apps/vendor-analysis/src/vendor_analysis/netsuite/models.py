"""NetSuite data models (Pydantic)."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Vendor(BaseModel):
    """NetSuite Vendor record."""

    id: str = Field(..., description="Internal ID")
    entity_id: str = Field(..., description="Vendor name/ID")
    company_name: str | None = Field(None, description="Company name")
    email: str | None = Field(None, description="Email address")
    phone: str | None = Field(None, description="Phone number")
    is_inactive: bool = Field(default=False, description="Inactive status")
    currency: str | None = Field(None, description="Currency code")
    terms: str | None = Field(None, description="Payment terms")
    balance: float = Field(default=0.0, description="Current balance")
    last_modified_date: datetime | None = Field(None, description="Last modified")

    class Config:
        """Pydantic config."""

        from_attributes = True


class VendorBill(BaseModel):
    """NetSuite Vendor Bill (transaction)."""

    id: str = Field(..., description="Internal ID")
    vendor_id: str = Field(..., description="Vendor internal ID")
    tran_id: str | None = Field(None, description="Transaction number")
    tran_date: datetime = Field(..., description="Transaction date")
    due_date: datetime | None = Field(None, description="Due date")
    amount: float = Field(..., description="Bill amount")
    status: str | None = Field(None, description="Bill status")
    memo: str | None = Field(None, description="Memo/notes")
    currency: str | None = Field(None, description="Currency code")
    exchange_rate: float = Field(default=1.0, description="Exchange rate")

    class Config:
        """Pydantic config."""

        from_attributes = True


class NetSuiteResponse(BaseModel):
    """Generic NetSuite API response wrapper."""

    count: int = Field(..., description="Number of items returned")
    has_more: bool = Field(default=False, description="More results available")
    items: list[dict[str, Any]] = Field(..., description="Response items")
    links: list[dict[str, str]] = Field(default_factory=list, description="HATEOAS links")
    offset: int = Field(default=0, description="Offset for pagination")
    total_results: int | None = Field(None, description="Total results available")
