"""
Field classification for NetSuite records.

Defines which fields are "known" (typed columns) vs "custom" (JSONB).
This configuration ensures resilience to NetSuite schema changes.
"""

from typing import Final

# Vendor Fields
# Known fields are NetSuite standard fields that map to typed database columns
# These are stable and unlikely to change
VENDOR_KNOWN_FIELDS: Final[frozenset[str]] = frozenset(
    [
        # Core identification
        "id",
        "entityId",
        # Company information
        "companyName",
        "legalName",
        "email",
        "phone",
        "fax",
        "url",
        # Status
        "isInactive",
        "isPerson",
        # Financial
        "balance",
        "balancePrimary",
        "creditLimit",
        "unbilledOrders",
        "unbilledOrdersPrimary",
        # References (stored as IDs or refNames)
        "currency",
        "terms",
        "category",
        "subsidiary",
        # Dates
        "dateCreated",
        "lastModifiedDate",
        # Tax
        "taxIdNum",
        "taxRegistrationList",
        # Account
        "accountNumber",
        # Sub-resources (NetSuite standard, not custom fields)
        "addressBook",
        "contactList",
        "currencyList",
        "subscriptionsList",
        "rolesList",
        # Additional standard fields
        "comments",
        "printOnCheckAs",
        "altName",
        "defaultAddress",
        "billPay",
        "eligibleForCommission",
        "emailPreference",
        "emailTransactions",
        "printTransactions",
        "faxTransactions",
        "representingSubsidiary",
        "workCalendar",
        "giveAccess",
        "sendEmail",
        "password",
        "requirePwdChange",
        "inheritIPRules",
        "globalSubscriptionStatus",
    ]
)

# VendorBill Fields
VENDOR_BILL_KNOWN_FIELDS: Final[frozenset[str]] = frozenset(
    [
        # Core identification
        "id",
        "tranId",
        # Vendor reference
        "entity",
        # Dates
        "tranDate",
        "dueDate",
        "createdDate",
        "lastModifiedDate",
        # Financial
        "userTotal",
        "total",
        "amountRemaining",
        "exchangeRate",
        # References
        "currency",
        "status",
        "approvalStatus",
        "subsidiary",
        # Details
        "memo",
        "tranStatus",
    ]
)


def is_known_field(field_name: str, record_type: str) -> bool:
    """
    Check if a field is a known (typed) field for the given record type.

    Args:
        field_name: NetSuite field name
        record_type: Record type (vendor, vendorbill, etc.)

    Returns:
        True if field should be stored in typed column, False if custom JSONB
    """
    if record_type.lower() == "vendor":
        return field_name in VENDOR_KNOWN_FIELDS
    elif record_type.lower() == "vendorbill":
        return field_name in VENDOR_BILL_KNOWN_FIELDS
    else:
        return False


def split_fields(
    data: dict, record_type: str
) -> tuple[dict[str, any], dict[str, any]]:
    """
    Split NetSuite data into known fields and custom fields.

    Args:
        data: Complete NetSuite record data
        record_type: Record type (vendor, vendorbill, etc.)

    Returns:
        Tuple of (known_fields, custom_fields) dictionaries
    """
    known = {}
    custom = {}

    for key, value in data.items():
        # Skip metadata fields
        if key in ("links", "refName"):
            continue

        if is_known_field(key, record_type):
            known[key] = value
        else:
            custom[key] = value

    return known, custom
