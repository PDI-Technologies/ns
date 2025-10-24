"""Vendor spend analysis and reporting."""

from dataclasses import dataclass
from datetime import datetime

import pandas as pd
from sqlalchemy.orm import Session

from vendor_analysis.core.config import Settings
from vendor_analysis.db.models import TransactionRecord, VendorRecord


@dataclass
class VendorSpendSummary:
    """Vendor spend summary data."""

    vendor_id: str
    vendor_name: str
    total_spend: float
    transaction_count: int
    average_transaction: float
    currency: str | None
    last_transaction_date: datetime | None


def analyze_vendor_spend(
    session: Session,
    settings: Settings,
    vendor_id: str | None = None,
) -> list[VendorSpendSummary]:
    """
    Analyze vendor spend with transaction aggregation.

    Args:
        session: Database session
        settings: Application settings
        vendor_id: Optional vendor ID to analyze (None = all vendors)

    Returns:
        List of VendorSpendSummary objects sorted by total spend
    """
    # Build query
    query = session.query(TransactionRecord)
    if vendor_id:
        query = query.filter(TransactionRecord.vendor_id == vendor_id)

    transactions = query.all()

    if not transactions:
        return []

    # Convert to pandas for analysis
    df = pd.DataFrame(
        [
            {
                "vendor_id": t.vendor_id,
                "amount": t.amount,
                "tran_date": t.tran_date,
                "currency": t.currency,
            }
            for t in transactions
        ]
    )

    # Group by vendor
    summary_data: list[VendorSpendSummary] = []

    for vendor_id_group, group_df in df.groupby("vendor_id"):
        # Get vendor details
        vendor = session.query(VendorRecord).filter_by(id=str(vendor_id_group)).first()
        if not vendor:
            continue

        currency_series = group_df["currency"]
        currency_value = (
            currency_series.iloc[0] if not currency_series.isna().all() else None
        )

        summary = VendorSpendSummary(
            vendor_id=str(vendor_id_group),
            vendor_name=vendor.company_name or vendor.entity_id,
            total_spend=float(group_df["amount"].sum()),
            transaction_count=len(group_df),
            average_transaction=float(group_df["amount"].mean()),
            currency=currency_value,
            last_transaction_date=group_df["tran_date"].max(),
        )
        summary_data.append(summary)

    # Sort by total spend descending
    summary_data.sort(key=lambda x: x.total_spend, reverse=True)

    return summary_data


def get_top_vendors(
    session: Session,
    settings: Settings,
    top_n: int | None = None,
) -> list[VendorSpendSummary]:
    """
    Get top vendors by spend.

    Args:
        session: Database session
        settings: Application settings
        top_n: Number of vendors to return (None = use config default)

    Returns:
        Top N vendors by total spend
    """
    if top_n is None:
        top_n = settings.top_vendors_count

    all_summaries = analyze_vendor_spend(session, settings)
    return all_summaries[:top_n]


def get_vendors_by_date_range(
    session: Session,
    start_date: datetime,
    end_date: datetime,
) -> list[VendorSpendSummary]:
    """
    Analyze vendor spend within date range.

    Args:
        session: Database session
        start_date: Start date for analysis
        end_date: End date for analysis

    Returns:
        Vendor summaries for date range
    """
    transactions = (
        session.query(TransactionRecord)
        .filter(
            TransactionRecord.tran_date >= start_date,
            TransactionRecord.tran_date <= end_date,
        )
        .all()
    )

    if not transactions:
        return []

    # Group and aggregate (similar to analyze_vendor_spend but filtered)
    df = pd.DataFrame(
        [
            {
                "vendor_id": t.vendor_id,
                "amount": t.amount,
                "tran_date": t.tran_date,
                "currency": t.currency,
            }
            for t in transactions
        ]
    )

    summary_data: list[VendorSpendSummary] = []

    for vendor_id, group_df in df.groupby("vendor_id"):
        vendor = session.query(VendorRecord).filter_by(id=str(vendor_id)).first()
        if not vendor:
            continue

        currency_series = group_df["currency"]
        currency_value = (
            currency_series.iloc[0] if not currency_series.isna().all() else None
        )

        summary = VendorSpendSummary(
            vendor_id=str(vendor_id),
            vendor_name=vendor.company_name or vendor.entity_id,
            total_spend=float(group_df["amount"].sum()),
            transaction_count=len(group_df),
            average_transaction=float(group_df["amount"].mean()),
            currency=currency_value,
            last_transaction_date=group_df["tran_date"].max(),
        )
        summary_data.append(summary)

    summary_data.sort(key=lambda x: x.total_spend, reverse=True)
    return summary_data
