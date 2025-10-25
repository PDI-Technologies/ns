"""
SQLAlchemy database models for local vendor analysis storage.

Schema Design:
- Typed columns for known, stable NetSuite fields (fast queries)
- JSONB columns for custom/evolving fields (schema flexibility)
- Resilient to NetSuite schema changes
"""

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class VendorRecord(Base):
    """
    Vendor record stored locally from NetSuite.

    Schema Strategy:
    - Typed columns: Known NetSuite standard fields (id, companyName, etc.)
    - custom_fields JSONB: All custom fields (custentity_*)
    - raw_data JSONB: Complete NetSuite response for auditing
    - Resilient to NetSuite schema evolution
    """

    __tablename__ = "vendors"

    # Core identification (typed columns for fast queries)
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    entity_id: Mapped[str] = mapped_column(String(200), nullable=False, index=True)

    # Company information
    company_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Status
    is_inactive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="Soft delete flag (not in NetSuite)"
    )

    # Financial
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    terms: Mapped[str | None] = mapped_column(String(100), nullable=True)
    balance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Dates
    created_date: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="NetSuite dateCreated timestamp"
    )
    last_modified_date: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="NetSuite lastModifiedDate timestamp"
    )

    # Flexible schema (JSONB columns)
    custom_fields: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True, comment="Custom NetSuite fields (custentity_*)"
    )
    raw_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True, comment="Complete NetSuite response for auditing"
    )

    # Sync metadata
    synced_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(datetime.UTC if hasattr(datetime, "UTC") else None),  # type: ignore[arg-type]
        nullable=False,
    )
    schema_version: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Tracks which fields were available at sync time"
    )


class TransactionRecord(Base):
    """
    Vendor transaction (bill) record stored locally from NetSuite.

    Schema Strategy:
    - Typed columns: Known NetSuite standard fields (tranId, tranDate, etc.)
    - custom_fields JSONB: All custom transaction fields (custbody_*)
    - raw_data JSONB: Complete NetSuite response for auditing
    - Resilient to NetSuite schema evolution
    """

    __tablename__ = "transactions"

    # Core identification
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    vendor_id: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # FK not enforced - read-only
    tran_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)

    # Dates
    created_date: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="NetSuite createdDate timestamp"
    )
    last_modified_date: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="NetSuite lastModifiedDate timestamp"
    )
    tran_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Financial
    amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    exchange_rate: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    # Status and details
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="Soft delete flag (not in NetSuite)"
    )
    memo: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Flexible schema (JSONB columns)
    custom_fields: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True, comment="Custom NetSuite transaction fields (custbody_*)"
    )
    raw_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True, comment="Complete NetSuite response for auditing"
    )

    # Sync metadata
    synced_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(datetime.UTC if hasattr(datetime, "UTC") else None),  # type: ignore[arg-type]
        nullable=False,
    )
    schema_version: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Tracks which fields were available at sync time"
    )


class SyncMetadata(Base):
    """
    Tracks sync operations for incremental updates.

    Stores the last successful sync timestamp for each record type,
    enabling incremental syncs that only fetch changed records.
    """

    __tablename__ = "sync_metadata"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    record_type: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True, comment="vendor or vendorbill"
    )
    last_sync_timestamp: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, comment="Last successful sync completion time"
    )
    sync_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="completed", comment="completed, in_progress, failed"
    )
    records_synced: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Number of records synced in last operation"
    )
    is_full_sync: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="Was this a full sync or incremental"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class AnalysisResult(Base):
    """Stored analysis results."""

    __tablename__ = "analysis_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    analysis_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    result_data: Mapped[str] = mapped_column(Text, nullable=False)  # JSON
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
