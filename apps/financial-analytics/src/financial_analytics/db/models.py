"""
SQLAlchemy database models with star schema design.

Based on financial-analytics database integration patterns.
Follows fail-fast discipline with strict typing.
"""

from datetime import UTC, datetime

from sqlalchemy import Date, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


# Dimension Tables


class DimVendor(Base):
    """Vendor dimension table."""

    __tablename__ = "dim_vendors"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(255))
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    terms: Mapped[str | None] = mapped_column(String(100))
    category: Mapped[str | None] = mapped_column(String(100))
    currency: Mapped[str | None] = mapped_column(String(10))
    synced_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(UTC),
    )


class DimCustomer(Base):
    """Customer dimension table."""

    __tablename__ = "dim_customers"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(255))
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    sales_rep: Mapped[str | None] = mapped_column(String(100))
    category: Mapped[str | None] = mapped_column(String(100))
    synced_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(UTC),
    )


class DimAccount(Base):
    """Chart of accounts dimension table."""

    __tablename__ = "dim_accounts"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    acct_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    acct_name: Mapped[str] = mapped_column(String(255), nullable=False)
    acct_type: Mapped[str] = mapped_column(String(100), nullable=False)
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    synced_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(UTC),
    )


# Fact Tables


class FactVendorBill(Base):
    """Vendor bill fact table."""

    __tablename__ = "fact_vendor_bills"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    tran_id: Mapped[str] = mapped_column(String(100), index=True)
    vendor_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    tran_date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    due_date: Mapped[datetime | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(50), index=True)
    memo: Mapped[str | None] = mapped_column(Text)
    synced_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(UTC),
    )


class FactInvoice(Base):
    """Customer invoice fact table."""

    __tablename__ = "fact_invoices"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    tran_id: Mapped[str] = mapped_column(String(100), index=True)
    customer_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    tran_date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    due_date: Mapped[datetime | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(50), index=True)
    synced_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(UTC),
    )


# Analysis Cache Tables


class VendorSpendAnalysis(Base):
    """Cached vendor spend analysis results."""

    __tablename__ = "vendor_spend_analysis"

    vendor_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    total_spend: Mapped[float] = mapped_column(Float, nullable=False)
    transaction_count: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_transaction: Mapped[float] = mapped_column(Float)
    first_transaction: Mapped[datetime | None] = mapped_column(Date)
    last_transaction: Mapped[datetime | None] = mapped_column(Date)
    analysis_date: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(UTC),
        index=True,
    )


class RevenueTrends(Base):
    """Cached revenue trend analysis."""

    __tablename__ = "revenue_trends"

    period: Mapped[str] = mapped_column(String(10), primary_key=True)
    total_revenue: Mapped[float] = mapped_column(Float, nullable=False)
    invoice_count: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_invoice_size: Mapped[float] = mapped_column(Float)
    unique_customers: Mapped[int] = mapped_column(Integer)
    revenue_growth_pct: Mapped[float | None] = mapped_column(Float)
    analysis_date: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(UTC),
    )


class FinancialKPIs(Base):
    """Cached financial KPI calculations."""

    __tablename__ = "financial_kpis"

    period: Mapped[str] = mapped_column(String(10), primary_key=True)
    gross_margin: Mapped[float | None] = mapped_column(Float)
    operating_margin: Mapped[float | None] = mapped_column(Float)
    net_margin: Mapped[float | None] = mapped_column(Float)
    roa: Mapped[float | None] = mapped_column(Float)
    roe: Mapped[float | None] = mapped_column(Float)
    current_ratio: Mapped[float | None] = mapped_column(Float)
    quick_ratio: Mapped[float | None] = mapped_column(Float)
    debt_to_equity: Mapped[float | None] = mapped_column(Float)
    analysis_date: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(UTC),
    )


# Salesforce Tables


class SalesforceOpportunity(Base):
    """Salesforce opportunity records for revenue pipeline analysis."""

    __tablename__ = "sf_opportunities"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[float | None] = mapped_column(Float)
    close_date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    stage_name: Mapped[str] = mapped_column(String(100), nullable=False)
    probability: Mapped[float | None] = mapped_column(Float)
    opp_type: Mapped[str | None] = mapped_column(String(100))
    account_id: Mapped[str | None] = mapped_column(String(50))
    account_name: Mapped[str | None] = mapped_column(String(255), index=True)
    industry: Mapped[str | None] = mapped_column(String(100))
    owner_name: Mapped[str | None] = mapped_column(String(255))
    is_closed: Mapped[bool] = mapped_column(nullable=False, default=False)
    is_won: Mapped[bool] = mapped_column(nullable=False, default=False, index=True)
    synced_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(UTC),
    )


class SalesforceAccount(Base):
    """Salesforce account records."""

    __tablename__ = "sf_accounts"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    account_type: Mapped[str | None] = mapped_column(String(100))
    industry: Mapped[str | None] = mapped_column(String(100), index=True)
    annual_revenue: Mapped[float | None] = mapped_column(Float)
    employee_count: Mapped[int | None] = mapped_column(Integer)
    synced_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
