"""
NetSuite-specific queries for vendor and transaction data.

All queries are read-only using SuiteTalk REST API.
"""

from typing import Any, Callable

from vendor_analysis.core.config import Settings, get_logger
from vendor_analysis.netsuite.client import NetSuiteClient
from vendor_analysis.netsuite.models import Vendor, VendorBill


def fetch_all_vendors_suiteql(
    client: NetSuiteClient,
    settings: Settings,
    max_created_date: str | None = None,
    limit: int | None = None,
    progress_callback: Callable[[str, int, int, int], None] | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch complete vendor data using SuiteQL with high-water mark.

    Uses MAX(created_date) from database as starting point.
    Fetches records created >= max_date, ordered chronologically.

    Args:
        client: NetSuite API client
        settings: Application settings
        max_created_date: Highest created_date in database (YYYY-MM-DD format)
        limit: Maximum number of records to fetch (for testing)
        progress_callback: Optional callback(phase, current, total, pages) for progress updates

    Returns:
        List of complete vendor data dictionaries from NetSuite
    """
    logger = get_logger()
    vendor_data_list: list[dict[str, Any]] = []

    # Build SuiteQL query with high-water mark
    sql_query = "SELECT * FROM vendor"

    if max_created_date:
        # Fetch records created on or after the max date (handles partial day syncs)
        sql_query += f" WHERE datecreated >= TO_DATE('{max_created_date}', 'YYYY-MM-DD')"

    # Order by created date to process chronologically
    sql_query += " ORDER BY datecreated ASC"

    logger.info(f"SuiteQL query: {sql_query}")

    # Fetch records using pagination
    offset = 0
    batch_size = settings.batch_size
    total_records = None
    total_pages = None

    while True:
        response = client.query_suiteql(sql_query, limit=batch_size, offset=offset)

        items = response.get("items", [])
        if not items:
            break

        vendor_data_list.extend(items)

        # Get total on first page
        if total_records is None and response.get("totalResults"):
            total_records = response["totalResults"]
            total_pages = (total_records + batch_size - 1) // batch_size
            logger.info(f"Total vendors to fetch: {total_records} ({total_pages} pages)")

        # Report progress
        if progress_callback and total_records and total_pages:
            current_page = (offset // batch_size) + 1
            progress_callback("fetch_records", len(vendor_data_list), total_records, total_pages)

        # Apply limit if specified (for testing)
        if limit and len(vendor_data_list) >= limit:
            vendor_data_list = vendor_data_list[:limit]
            break

        if not response.get("hasMore", False):
            break

        offset += batch_size

    logger.info(f"Fetched {len(vendor_data_list)} vendors via SuiteQL")
    return vendor_data_list




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


def fetch_vendor_bills_suiteql(
    client: NetSuiteClient,
    settings: Settings,
    vendor_id: str | None = None,
    max_created_date: str | None = None,
    limit: int | None = None,
    progress_callback: Callable[[str, int, int, int], None] | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch complete vendor bill data using SuiteQL with high-water mark.

    Uses MAX(created_date) from database as starting point.
    Fetches records created >= max_date, ordered chronologically.

    Args:
        client: NetSuite API client
        settings: Application settings
        vendor_id: Optional vendor ID to filter by
        max_created_date: Highest created_date in database (YYYY-MM-DD format)
        limit: Maximum number of records to fetch (for testing)
        progress_callback: Optional callback(phase, current, total, pages) for progress updates

    Returns:
        List of complete vendor bill data dictionaries from NetSuite
    """
    logger = get_logger()
    bill_data_list: list[dict[str, Any]] = []

    # Build SuiteQL query
    sql_query = "SELECT * FROM transaction WHERE type = 'VendBill'"

    # Add filters
    if vendor_id:
        sql_query += f" AND entity = '{vendor_id}'"

    if max_created_date:
        # Fetch records created on or after the max date (handles partial day syncs)
        sql_query += f" AND createddate >= TO_DATE('{max_created_date}', 'YYYY-MM-DD')"

    # Order by created date to process chronologically
    sql_query += " ORDER BY createddate ASC"

    logger.info(f"SuiteQL query: {sql_query}")

    # Fetch records using pagination
    offset = 0
    batch_size = settings.batch_size
    total_records = None
    total_pages = None

    while True:
        response = client.query_suiteql(sql_query, limit=batch_size, offset=offset)

        items = response.get("items", [])
        if not items:
            break

        bill_data_list.extend(items)

        # Get total on first page
        if total_records is None and response.get("totalResults"):
            total_records = response["totalResults"]
            total_pages = (total_records + batch_size - 1) // batch_size
            logger.info(f"Total bills to fetch: {total_records} ({total_pages} pages)")

        # Report progress
        if progress_callback and total_records and total_pages:
            current_page = (offset // batch_size) + 1
            progress_callback("fetch_records", len(bill_data_list), total_records, total_pages)

        # Apply limit if specified (for testing)
        if limit and len(bill_data_list) >= limit:
            bill_data_list = bill_data_list[:limit]
            break

        if not response.get("hasMore", False):
            break

        offset += batch_size

    logger.info(f"Fetched {len(bill_data_list)} bills via SuiteQL")
    return bill_data_list




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
        tran_date=data.get("tranDate"),  # Returns None if not present
        due_date=data.get("dueDate"),
        amount=float(data.get("userTotal", 0.0)),
        status=data.get("status", {}).get("refName") if "status" in data else None,
        memo=data.get("memo"),
        currency=data.get("currency", {}).get("refName") if "currency" in data else None,
        exchange_rate=float(data.get("exchangeRate", 1.0)),
    )
