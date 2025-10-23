"""
SQLAlchemy database models for local vendor analysis storage.
"""

from datetime import datetime

from sqlalchemy import Float, String, Text, Boolean, DateTime, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class VendorRecord(Base):
    """Vendor record stored locally from NetSuite."""

    __tablename__ = "vendors"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    entity_id: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    company_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_inactive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    terms: Mapped[str | None] = mapped_column(String(100), nullable=True)
    balance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    last_modified_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    synced_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(datetime.UTC if hasattr(datetime, 'UTC') else None),  # type: ignore[arg-type]
        nullable=False
    )


class TransactionRecord(Base):
    """Vendor transaction (bill) record stored locally from NetSuite."""

    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    vendor_id: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # FK not enforced - read-only
    tran_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    tran_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    memo: Mapped[str | None] = mapped_column(Text, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    exchange_rate: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    synced_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(datetime.UTC if hasattr(datetime, 'UTC') else None),  # type: ignore[arg-type]
        nullable=False
    )


class AnalysisResult(Base):
    """Stored analysis results."""

    __tablename__ = "analysis_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    analysis_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    result_data: Mapped[str] = mapped_column(Text, nullable=False)  # JSON
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
