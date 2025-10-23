"""
NetSuite-specific queries for vendor and transaction data.

All queries are read-only using SuiteTalk REST API.
"""

from typing import Any

from vendor_analysis.core.config import Settings
from vendor_analysis.netsuite.client import NetSuiteClient
from vendor_analysis.netsuite.models import Vendor, VendorBill


def fetch_all_vendors(client: NetSuiteClient, settings: Settings) -> list[Vendor]:
    """
    Fetch all vendors from NetSuite (paginated).

    Args:
        client: NetSuite API client
        settings: Application settings

    Returns:
        List of Vendor objects
    """
    vendors: list[Vendor] = []
    offset = 0
    page_size = settings.page_size

    while True:
        response = client.query_records(
            record_type="vendor",
            limit=page_size,
            offset=offset,
        )

        items = response.get("items", [])
        if not items:
            break

        for item in items:
            vendors.append(_parse_vendor(item))

        # Check if more results available
        if not response.get("hasMore", False):
            break

        offset += page_size

    return vendors


def fetch_vendor_by_id(client: NetSuiteClient, vendor_id: str) -> Vendor:
    """
    Fetch single vendor by internal ID.

    Args:
        client: NetSuite API client
        vendor_id: Vendor internal ID

    Returns:
        Vendor object
    """
    data = client.get_record(record_type="vendor", record_id=vendor_id)
    return _parse_vendor(data)


def fetch_vendor_bills(
    client: NetSuiteClient,
    settings: Settings,
    vendor_id: str | None = None,
) -> list[VendorBill]:
    """
    Fetch vendor bills (transactions).

    Args:
        client: NetSuite API client
        settings: Application settings
        vendor_id: Optional vendor ID to filter by

    Returns:
        List of VendorBill objects
    """
    bills: list[VendorBill] = []
    offset = 0
    page_size = settings.page_size

    # Build query filter if vendor_id provided
    query = f"vendor.internalId = {vendor_id}" if vendor_id else None

    while True:
        response = client.query_records(
            record_type="vendorbill",
            query=query,
            limit=page_size,
            offset=offset,
        )

        items = response.get("items", [])
        if not items:
            break

        for item in items:
            bills.append(_parse_vendor_bill(item))

        if not response.get("hasMore", False):
            break

        offset += page_size

    return bills


def _parse_vendor(data: dict[str, Any]) -> Vendor:
    """Parse NetSuite vendor response to Vendor model."""
    return Vendor(
        id=data.get("id", ""),
        entity_id=data.get("entityId", ""),
        company_name=data.get("companyName"),
        email=data.get("email"),
        phone=data.get("phone"),
        is_inactive=data.get("isInactive", False),
        currency=data.get("currency", {}).get("refName") if "currency" in data else None,
        terms=data.get("terms", {}).get("refName") if "terms" in data else None,
        balance=float(data.get("balance", 0.0)),
        last_modified_date=data.get("lastModifiedDate"),
    )


def _parse_vendor_bill(data: dict[str, Any]) -> VendorBill:
    """Parse NetSuite vendor bill response to VendorBill model."""
    return VendorBill(
        id=data.get("id", ""),
        vendor_id=data.get("entity", {}).get("id", ""),
        tran_id=data.get("tranId"),
        tran_date=data.get("tranDate", ""),
        due_date=data.get("dueDate"),
        amount=float(data.get("userTotal", 0.0)),
        status=data.get("status", {}).get("refName") if "status" in data else None,
        memo=data.get("memo"),
        currency=data.get("currency", {}).get("refName") if "currency" in data else None,
        exchange_rate=float(data.get("exchangeRate", 1.0)),
    )
