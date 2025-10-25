"""
NetSuite data models (Pydantic).

These models parse NetSuite API responses and separate known fields
from custom fields for database storage.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Vendor(BaseModel):
    """
    NetSuite Vendor record.

    This model accepts complete NetSuite vendor data. Known fields are
    explicitly typed, and custom fields are available via model_extra.
    """

    # Known NetSuite standard fields (explicitly typed)
    id: str = Field(..., description="Internal ID")
    entity_id: str = Field(..., description="Vendor name/ID", alias="entityId")
    company_name: str | None = Field(None, description="Company name", alias="companyName")
    email: str | None = Field(None, description="Email address")
    phone: str | None = Field(None, description="Phone number")
    is_inactive: bool = Field(default=False, description="Inactive status", alias="isInactive")
    currency: str | None = Field(None, description="Currency code")
    terms: str | None = Field(None, description="Payment terms")
    balance: float = Field(default=0.0, description="Current balance")
    last_modified_date: datetime | None = Field(
        None, description="Last modified", alias="lastModifiedDate"
    )

    # Custom fields and raw data are handled separately in sync logic

    class Config:
        """Pydantic config."""

        from_attributes = True
        populate_by_name = True  # Allow both snake_case and camelCase
        extra = "allow"  # Allow extra fields (custom fields)


class VendorBill(BaseModel):
    """
    NetSuite Vendor Bill (transaction).

    This model accepts complete NetSuite vendor bill data. Known fields are
    explicitly typed, and custom fields are available via model_extra.
    """

    # Known NetSuite standard fields (explicitly typed)
    id: str = Field(..., description="Internal ID")
    vendor_id: str = Field(..., description="Vendor internal ID")
    tran_id: str | None = Field(None, description="Transaction number", alias="tranId")
    tran_date: datetime | None = Field(None, description="Transaction date", alias="tranDate")
    due_date: datetime | None = Field(None, description="Due date", alias="dueDate")
    amount: float = Field(default=0.0, description="Bill amount")
    status: str | None = Field(None, description="Bill status")
    memo: str | None = Field(None, description="Memo/notes")
    currency: str | None = Field(None, description="Currency code")
    exchange_rate: float = Field(default=1.0, description="Exchange rate", alias="exchangeRate")

    # Custom fields and raw data are handled separately in sync logic

    class Config:
        """Pydantic config."""

        from_attributes = True
        populate_by_name = True  # Allow both snake_case and camelCase
        extra = "allow"  # Allow extra fields (custom transaction fields)


class NetSuiteResponse(BaseModel):
    """Generic NetSuite API response wrapper."""

    count: int = Field(..., description="Number of items returned")
    has_more: bool = Field(default=False, description="More results available")
    items: list[dict[str, Any]] = Field(..., description="Response items")
    links: list[dict[str, str]] = Field(default_factory=list, description="HATEOAS links")
    offset: int = Field(default=0, description="Offset for pagination")
    total_results: int | None = Field(None, description="Total results available")
