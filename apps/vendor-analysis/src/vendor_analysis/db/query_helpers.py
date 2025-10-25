"""
Database query helpers for working with JSONB custom fields.

Provides utilities to query vendors and transactions by custom fields
in a schema-resilient way.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from vendor_analysis.db.models import TransactionRecord, VendorRecord


class CustomFieldQuery:
    """Helper class for querying custom fields in JSONB columns."""

    @staticmethod
    def get_vendor_by_custom_field(
        session: Session, field_name: str, field_value: Any
    ) -> list[VendorRecord]:
        """
        Query vendors by custom field value.

        Example:
            vendors = CustomFieldQuery.get_vendor_by_custom_field(
                session, "custentity_region", "West"
            )

        Args:
            session: SQLAlchemy session
            field_name: Custom field name (e.g., "custentity_region")
            field_value: Value to match

        Returns:
            List of VendorRecord objects matching the criteria
        """
        # Query supports both metadata structure and simple values
        return (
            session.query(VendorRecord)
            .filter(
                func.jsonb_extract_path_text(VendorRecord.custom_fields, field_name, "value")
                == str(field_value)
            )
            .all()
        )

    @staticmethod
    def get_vendors_with_field(session: Session, field_name: str) -> list[VendorRecord]:
        """
        Get all vendors that have a specific custom field (regardless of value).

        Args:
            session: SQLAlchemy session
            field_name: Custom field name

        Returns:
            List of VendorRecord objects that have this field
        """
        return (
            session.query(VendorRecord)
            .filter(VendorRecord.custom_fields.has_key(field_name))
            .all()
        )

    @staticmethod
    def get_vendors_with_active_field(
        session: Session, field_name: str
    ) -> list[VendorRecord]:
        """
        Get vendors that have a specific custom field and it's NOT deprecated.

        Args:
            session: SQLAlchemy session
            field_name: Custom field name

        Returns:
            List of VendorRecord objects with active (non-deprecated) field
        """
        return (
            session.query(VendorRecord)
            .filter(
                VendorRecord.custom_fields.has_key(field_name),
                func.jsonb_extract_path_text(
                    VendorRecord.custom_fields, field_name, "deprecated"
                )
                != "true",
            )
            .all()
        )

    @staticmethod
    def list_all_custom_fields(session: Session) -> dict[str, int]:
        """
        List all custom field names across all vendors with count.

        Returns:
            Dictionary of {field_name: count_of_vendors}
        """
        # Use PostgreSQL's jsonb_object_keys to get all keys
        result = session.execute(
            text(
                """
                SELECT DISTINCT jsonb_object_keys(custom_fields) as field_name,
                       COUNT(*) as vendor_count
                FROM vendors
                WHERE custom_fields IS NOT NULL
                GROUP BY field_name
                ORDER BY vendor_count DESC
                """
            )
        )

        return {row.field_name: row.vendor_count for row in result}

    @staticmethod
    def get_deprecated_fields(
        session: Session, days_threshold: int = 30
    ) -> dict[str, list[str]]:
        """
        Find custom fields that haven't been seen in recent syncs.

        Args:
            session: SQLAlchemy session
            days_threshold: Number of days to consider "deprecated"

        Returns:
            Dictionary of {field_name: [vendor_ids_with_deprecated_field]}
        """
        cutoff = datetime.now().isoformat()

        result = session.execute(
            text(
                """
                SELECT
                    v.id as vendor_id,
                    field_name,
                    jsonb_extract_path_text(custom_fields, field_name, 'last_seen') as last_seen
                FROM vendors v,
                     jsonb_object_keys(v.custom_fields) as field_name
                WHERE custom_fields IS NOT NULL
                  AND jsonb_extract_path_text(custom_fields, field_name, 'deprecated') = 'true'
                ORDER BY field_name, vendor_id
                """
            )
        )

        deprecated = {}
        for row in result:
            if row.field_name not in deprecated:
                deprecated[row.field_name] = []
            deprecated[row.field_name].append(row.vendor_id)

        return deprecated


class TransactionFieldQuery:
    """Helper class for querying transaction custom fields."""

    @staticmethod
    def get_transactions_by_custom_field(
        session: Session, field_name: str, field_value: Any
    ) -> list[TransactionRecord]:
        """
        Query transactions by custom field value.

        Args:
            session: SQLAlchemy session
            field_name: Custom field name (e.g., "custbody_department")
            field_value: Value to match

        Returns:
            List of TransactionRecord objects matching the criteria
        """
        return (
            session.query(TransactionRecord)
            .filter(
                func.jsonb_extract_path_text(
                    TransactionRecord.custom_fields, field_name, "value"
                )
                == str(field_value)
            )
            .all()
        )

    @staticmethod
    def list_all_custom_fields(session: Session) -> dict[str, int]:
        """
        List all custom field names across all transactions with count.

        Returns:
            Dictionary of {field_name: count_of_transactions}
        """
        result = session.execute(
            text(
                """
                SELECT DISTINCT jsonb_object_keys(custom_fields) as field_name,
                       COUNT(*) as transaction_count
                FROM transactions
                WHERE custom_fields IS NOT NULL
                GROUP BY field_name
                ORDER BY transaction_count DESC
                """
            )
        )

        return {row.field_name: row.transaction_count for row in result}


def analyze_schema_evolution(session: Session) -> dict[str, Any]:
    """
    Analyze how the NetSuite schema has evolved over time.

    Examines schema_version and custom_fields to identify:
    - New fields added
    - Fields removed/deprecated
    - Field usage patterns

    Args:
        session: SQLAlchemy session

    Returns:
        Dictionary with schema evolution analysis
    """
    # Get distinct schema versions
    versions = (
        session.query(VendorRecord.schema_version)
        .distinct()
        .order_by(VendorRecord.schema_version)
        .all()
    )

    analysis = {
        "total_schema_versions": len(versions),
        "schema_versions": [v[0] for v in versions if v[0] is not None],
        "current_custom_fields": CustomFieldQuery.list_all_custom_fields(session),
        "deprecated_fields": CustomFieldQuery.get_deprecated_fields(session),
    }

    return analysis
