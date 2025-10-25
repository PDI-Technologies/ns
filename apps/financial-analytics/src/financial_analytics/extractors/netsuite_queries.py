"""
NetSuite data extraction queries.

All queries are read-only using SuiteTalk REST API.
Based on financial-analytics integration patterns.
"""

from financial_analytics.core.config import Settings
from financial_analytics.extractors.netsuite_client import NetSuiteClient
from financial_analytics.extractors.netsuite_models import (
    Account,
    Customer,
    Invoice,
    Vendor,
    VendorBill,
)


def fetch_all_vendors(client: NetSuiteClient, settings: Settings) -> list[Vendor]:
    """
    Fetch all vendors from NetSuite with pagination.

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
            vendors.append(Vendor(**item))

        if not response.get("hasMore", False):
            break

        offset += page_size

    return vendors


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

    while True:
        response = client.query_records(
            record_type="vendorBill",
            limit=page_size,
            offset=offset,
        )

        items = response.get("items", [])
        if not items:
            break

        for item in items:
            if vendor_id is None or item.get("entity") == vendor_id:
                bills.append(VendorBill(**item))

        if not response.get("hasMore", False):
            break

        offset += page_size

    return bills


def fetch_all_customers(client: NetSuiteClient, settings: Settings) -> list[Customer]:
    """
    Fetch all customers from NetSuite.

    Args:
        client: NetSuite API client
        settings: Application settings

    Returns:
        List of Customer objects
    """
    customers: list[Customer] = []
    offset = 0
    page_size = settings.page_size

    while True:
        response = client.query_records(
            record_type="customer",
            limit=page_size,
            offset=offset,
        )

        items = response.get("items", [])
        if not items:
            break

        for item in items:
            customers.append(Customer(**item))

        if not response.get("hasMore", False):
            break

        offset += page_size

    return customers


def fetch_invoices(client: NetSuiteClient, settings: Settings) -> list[Invoice]:
    """
    Fetch customer invoices.

    Args:
        client: NetSuite API client
        settings: Application settings

    Returns:
        List of Invoice objects
    """
    invoices: list[Invoice] = []
    offset = 0
    page_size = settings.page_size

    while True:
        response = client.query_records(
            record_type="invoice",
            limit=page_size,
            offset=offset,
        )

        items = response.get("items", [])
        if not items:
            break

        for item in items:
            invoices.append(Invoice(**item))

        if not response.get("hasMore", False):
            break

        offset += page_size

    return invoices


def fetch_chart_of_accounts(client: NetSuiteClient, settings: Settings) -> list[Account]:
    """
    Fetch chart of accounts.

    Args:
        client: NetSuite API client
        settings: Application settings

    Returns:
        List of Account objects
    """
    accounts: list[Account] = []
    offset = 0
    page_size = settings.page_size

    while True:
        response = client.query_records(
            record_type="account",
            limit=page_size,
            offset=offset,
        )

        items = response.get("items", [])
        if not items:
            break

        for item in items:
            accounts.append(Account(**item))

        if not response.get("hasMore", False):
            break

        offset += page_size

    return accounts
