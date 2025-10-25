"""
Pydantic models for NetSuite API responses.

Data validation at the boundary following fail-fast discipline.
Based on financial-analytics skill integration patterns.
"""

from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class Vendor(BaseModel):
    """NetSuite vendor record."""

    id: str
    companyName: str
    email: str | None = None
    balance: float = 0.0
    terms: str | None = None
    category: str | None = None
    currency: str | None = None


class VendorBill(BaseModel):
    """NetSuite vendor bill transaction."""

    id: str
    tranId: str = Field(description="Transaction number")
    entity: str = Field(description="Vendor ID")
    amount: float
    tranDate: date
    dueDate: date | None = None
    status: str
    memo: str | None = None


class Customer(BaseModel):
    """NetSuite customer record."""

    id: str
    companyName: str
    email: str | None = None
    balance: float = 0.0
    salesRep: str | None = None
    category: str | None = None


class Invoice(BaseModel):
    """NetSuite customer invoice."""

    id: str
    tranId: str
    entity: str = Field(description="Customer ID")
    amount: float
    tranDate: date
    dueDate: date | None = None
    status: str


class Account(BaseModel):
    """Chart of accounts record."""

    id: str
    acctNumber: str
    acctName: str
    acctType: str
    balance: float = 0.0


class Transaction(BaseModel):
    """General ledger transaction."""

    id: str
    tranId: str
    type: str
    entity: str | None = None
    account: str | None = None
    amount: float
    tranDate: date
    memo: str | None = None


class NetSuiteResponse(BaseModel):
    """Generic NetSuite API response wrapper."""

    items: list[dict[str, Any]]
    hasMore: bool = False
    count: int = 0
    offset: int = 0
    totalResults: int = 0
