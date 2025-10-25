"""
NetSuite field processing utilities.

Handles extraction and transformation of NetSuite API responses into
database-ready format with proper field classification.
"""

from datetime import datetime
from typing import Any

from vendor_analysis.core.field_config import VENDOR_KNOWN_FIELDS, VENDOR_BILL_KNOWN_FIELDS


def extract_reference_value(field_value: Any) -> str | None:
    """
    Extract value from NetSuite reference field.

    NetSuite returns references as objects: {"id": "123", "refName": "USD"}
    We typically want to store the refName for display purposes.

    Args:
        field_value: Value from NetSuite API (could be dict, str, or None)

    Returns:
        Extracted string value or None
    """
    if isinstance(field_value, dict):
        # Prefer refName for display, fall back to id
        return field_value.get("refName") or field_value.get("id")
    elif isinstance(field_value, str):
        return field_value
    return None


def process_vendor_fields(raw_data: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Process vendor data from NetSuite into known and custom fields.

    Handles both Record API (camelCase) and SuiteQL (lowercase) field names.

    Args:
        raw_data: Complete vendor data from NetSuite API or SuiteQL

    Returns:
        Tuple of (known_fields, custom_fields) ready for database storage
    """
    known = {}
    custom = {}

    # Normalize field names (SuiteQL returns lowercase, Record API returns camelCase)
    # Convert SuiteQL lowercase to camelCase for consistent processing
    normalized_data = {}
    for key, value in raw_data.items():
        # SuiteQL lowercase -> camelCase mapping
        if key.lower() == "entityid":
            normalized_data["entityId"] = value
        elif key.lower() == "companyname":
            normalized_data["companyName"] = value
        elif key.lower() == "isinactive":
            normalized_data["isInactive"] = value
        elif key.lower() == "datecreated":
            normalized_data["dateCreated"] = value
        elif key.lower() == "lastmodifieddate":
            normalized_data["lastModifiedDate"] = value
        else:
            # Keep as-is (custom fields, references, etc.)
            normalized_data[key] = value

    for key, value in normalized_data.items():
        # Skip metadata
        if key in ("links", "refName"):
            continue

        # Check if this is a known field
        if key in VENDOR_KNOWN_FIELDS:
            # Handle special field types
            if key == "id":
                known["id"] = str(value)
            elif key == "entityId":
                known["entity_id"] = str(value) if value else ""
            elif key == "companyName":
                known["company_name"] = str(value) if value else None
            elif key == "email":
                known["email"] = str(value) if value else None
            elif key == "phone":
                known["phone"] = str(value) if value else None
            elif key == "isInactive":
                # Handle both Record API (boolean) and SuiteQL (string "F"/"T")
                if isinstance(value, str):
                    known["is_inactive"] = value.upper() == "T"
                else:
                    known["is_inactive"] = bool(value) if value is not None else False
            elif key == "balance":
                known["balance"] = float(value) if value is not None else 0.0
            elif key in ("currency", "terms"):
                # These are references - extract refName
                known[key] = extract_reference_value(value)
            elif key == "dateCreated":
                known["created_date"] = value  # datetime handled by Pydantic/SQLAlchemy
            elif key == "lastModifiedDate":
                known["last_modified_date"] = value  # datetime handled by Pydantic/SQLAlchemy
            # Add other known fields as needed
        else:
            # Custom field - store in JSONB
            # Handle nested objects by storing the useful part
            if isinstance(value, dict) and "refName" in value:
                custom[key] = extract_reference_value(value)
            else:
                custom[key] = value

    return known, custom


def process_vendor_bill_fields(
    raw_data: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Process vendor bill data from NetSuite into known and custom fields.

    Handles both Record API (camelCase) and SuiteQL (lowercase) field names.

    Args:
        raw_data: Complete vendor bill data from NetSuite API or SuiteQL

    Returns:
        Tuple of (known_fields, custom_fields) ready for database storage
    """
    known = {}
    custom = {}

    # Normalize field names (SuiteQL returns lowercase, Record API returns camelCase)
    normalized_data = {}
    for key, value in raw_data.items():
        # SuiteQL lowercase -> camelCase mapping for transaction fields
        if key.lower() == "tranid":
            normalized_data["tranId"] = value
        elif key.lower() == "trandate":
            normalized_data["tranDate"] = value
        elif key.lower() == "duedate":
            normalized_data["dueDate"] = value
        elif key.lower() == "createddate":
            normalized_data["createdDate"] = value
        elif key.lower() == "lastmodifieddate":
            normalized_data["lastModifiedDate"] = value
        elif key.lower() == "usertotal":
            normalized_data["userTotal"] = value
        elif key.lower() == "exchangerate":
            normalized_data["exchangeRate"] = value
        else:
            # Keep as-is (custom fields, references, etc.)
            normalized_data[key] = value

    for key, value in normalized_data.items():
        # Skip metadata
        if key in ("links", "refName"):
            continue

        # Check if this is a known field
        if key in VENDOR_BILL_KNOWN_FIELDS:
            # Handle special field types
            if key == "id":
                known["id"] = str(value)
            elif key == "entity":
                # Vendor reference
                known["vendor_id"] = extract_reference_value(value) or ""
            elif key == "tranId":
                known["tran_id"] = str(value) if value else None
            elif key == "createdDate":
                known["created_date"] = value  # datetime handled by Pydantic/SQLAlchemy
            elif key == "lastModifiedDate":
                known["last_modified_date"] = value  # datetime handled by Pydantic/SQLAlchemy
            elif key in ("tranDate", "dueDate"):
                # Dates handled by Pydantic/SQLAlchemy
                known_key = "tran_date" if key == "tranDate" else "due_date"
                known[known_key] = value
            elif key == "userTotal":
                known["amount"] = float(value) if value is not None else 0.0
            elif key in ("currency", "status"):
                # References - extract refName
                known[key] = extract_reference_value(value)
            elif key == "exchangeRate":
                known["exchange_rate"] = float(value) if value is not None else 1.0
            elif key == "memo":
                known["memo"] = str(value) if value else None
            # Add other known fields as needed
        else:
            # Custom field - store in JSONB
            if isinstance(value, dict) and "refName" in value:
                custom[key] = extract_reference_value(value)
            else:
                custom[key] = value

    return known, custom


def merge_custom_fields(
    existing: dict[str, Any] | None, new: dict[str, Any], sync_timestamp: datetime
) -> dict[str, Any]:
    """
    Merge custom fields preserving historical data.

    Strategy:
    - New/updated fields: Use new values
    - Missing fields: Keep from existing (field may have been removed from NetSuite)
    - Track field lifecycle with metadata

    Args:
        existing: Existing custom_fields from database (may be None)
        new: New custom fields from NetSuite API
        sync_timestamp: Current sync timestamp

    Returns:
        Merged custom fields dictionary with lifecycle metadata
    """
    if existing is None:
        existing = {}

    merged = {}

    # Get all unique field names
    all_fields = set(existing.keys()) | set(new.keys())

    for field in all_fields:
        if field in new:
            # Field exists in new data - update it
            merged[field] = {
                "value": new[field],
                "last_seen": sync_timestamp.isoformat(),
                "deprecated": False,
            }
            # Preserve first_seen if it exists
            if field in existing and isinstance(existing[field], dict):
                merged[field]["first_seen"] = existing[field].get(
                    "first_seen", sync_timestamp.isoformat()
                )
            else:
                merged[field]["first_seen"] = sync_timestamp.isoformat()
        else:
            # Field missing from new data - preserve from existing
            if isinstance(existing[field], dict):
                # Already has metadata structure
                merged[field] = existing[field].copy()
                # Mark as potentially deprecated if not seen recently
                last_seen_str = existing[field].get("last_seen")
                if last_seen_str:
                    last_seen = datetime.fromisoformat(last_seen_str)
                    days_since_seen = (sync_timestamp - last_seen).days
                    if days_since_seen > 30:
                        merged[field]["deprecated"] = True
            else:
                # Old format - convert to metadata structure
                merged[field] = {
                    "value": existing[field],
                    "first_seen": sync_timestamp.isoformat(),  # Unknown, use now
                    "last_seen": sync_timestamp.isoformat(),  # Last known sync
                    "deprecated": True,  # Not in current NetSuite response
                }

    return merged


def extract_simple_custom_fields(custom_fields_with_metadata: dict[str, Any]) -> dict[str, Any]:
    """
    Extract simple value-only dict from metadata structure.

    Useful for queries that just need the values without lifecycle metadata.

    Args:
        custom_fields_with_metadata: Custom fields with full metadata

    Returns:
        Simple dict with just field values
    """
    simple = {}
    for key, data in custom_fields_with_metadata.items():
        if isinstance(data, dict) and "value" in data:
            simple[key] = data["value"]
        else:
            # Old format or simple value
            simple[key] = data
    return simple
