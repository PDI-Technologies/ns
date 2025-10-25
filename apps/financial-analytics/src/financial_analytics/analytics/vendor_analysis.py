"""
Vendor spend analysis engine.

Based on financial-analytics and vendor-cost-analytics skill patterns.
"""

from dataclasses import dataclass
from difflib import SequenceMatcher

import pandas as pd
from sqlalchemy.orm import Session

from financial_analytics.core.config import Settings
from financial_analytics.db.models import DimVendor, FactVendorBill


@dataclass
class VendorSpendSummary:
    """Vendor spend analysis results."""

    vendor_id: str
    company_name: str
    total_spend: float
    transaction_count: int
    avg_transaction: float
    first_transaction: str | None
    last_transaction: str | None


@dataclass
class DuplicatePair:
    """Potential duplicate vendor pair."""

    vendor1_id: str
    vendor1_name: str
    vendor2_id: str
    vendor2_name: str
    similarity: float


def analyze_vendor_spend(session: Session, settings: Settings) -> list[VendorSpendSummary]:
    """
    Analyze vendor spend from database.

    Args:
        session: Database session
        settings: Application settings

    Returns:
        List of vendor spend summaries sorted by total spend
    """
    # Query vendor bills
    query = session.query(
        DimVendor.id,
        DimVendor.company_name,
        FactVendorBill.amount,
        FactVendorBill.tran_date,
    ).join(FactVendorBill, DimVendor.id == FactVendorBill.vendor_id)

    df = pd.read_sql(query.statement, session.bind)

    if df.empty:
        return []

    # Aggregate by vendor
    aggregated = df.groupby(["id", "company_name"]).agg({
        "amount": ["sum", "count", "mean"],
        "tran_date": ["min", "max"],
    })

    results: list[VendorSpendSummary] = []
    for (vendor_id, company_name), row in aggregated.iterrows():
        results.append(
            VendorSpendSummary(
                vendor_id=str(vendor_id),
                company_name=str(company_name),
                total_spend=float(row[("amount", "sum")]),
                transaction_count=int(row[("amount", "count")]),
                avg_transaction=float(row[("amount", "mean")]),
                first_transaction=str(row[("tran_date", "min")]),
                last_transaction=str(row[("tran_date", "max")]),
            )
        )

    # Sort by total spend descending
    results.sort(key=lambda x: x.total_spend, reverse=True)
    return results


def get_top_vendors(
    session: Session,
    settings: Settings,
    top_n: int | None = None,
) -> list[VendorSpendSummary]:
    """
    Get top N vendors by spend.

    Args:
        session: Database session
        settings: Application settings
        top_n: Number of top vendors (defaults to settings value)

    Returns:
        List of top vendors by spend
    """
    all_vendors = analyze_vendor_spend(session, settings)
    limit = top_n if top_n is not None else settings.top_n_vendors
    return all_vendors[:limit]


def calculate_similarity(name1: str, name2: str) -> float:
    """
    Calculate similarity between two vendor names.

    Args:
        name1: First vendor name
        name2: Second vendor name

    Returns:
        Similarity score between 0.0 and 1.0
    """
    return SequenceMatcher(None, name1.lower(), name2.lower()).ratio()


def detect_duplicate_vendors(
    session: Session,
    settings: Settings,
    threshold: float | None = None,
) -> list[DuplicatePair]:
    """
    Detect potential duplicate vendors using fuzzy matching.

    Args:
        session: Database session
        settings: Application settings
        threshold: Similarity threshold (defaults to settings value)

    Returns:
        List of potential duplicate pairs
    """
    similarity_threshold = threshold if threshold is not None else settings.duplicate_threshold

    # Get all vendors
    vendors = session.query(DimVendor).all()

    duplicates: list[DuplicatePair] = []

    # Pairwise comparison
    for i, vendor1 in enumerate(vendors):
        for vendor2 in vendors[i + 1 :]:
            similarity = calculate_similarity(vendor1.company_name, vendor2.company_name)

            if similarity >= similarity_threshold:
                duplicates.append(
                    DuplicatePair(
                        vendor1_id=vendor1.id,
                        vendor1_name=vendor1.company_name,
                        vendor2_id=vendor2.id,
                        vendor2_name=vendor2.company_name,
                        similarity=similarity,
                    )
                )

    # Sort by similarity descending
    duplicates.sort(key=lambda x: x.similarity, reverse=True)
    return duplicates
