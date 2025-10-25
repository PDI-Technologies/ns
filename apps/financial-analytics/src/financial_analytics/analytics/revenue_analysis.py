"""
Revenue trend analysis engine.

Based on financial-analytics skill patterns.
"""

from dataclasses import dataclass

import pandas as pd
from sqlalchemy.orm import Session

from financial_analytics.core.config import Settings
from financial_analytics.db.models import DimCustomer, FactInvoice


@dataclass
class RevenueTrendData:
    """Revenue trend by period."""

    period: str
    total_revenue: float
    invoice_count: int
    avg_invoice_size: float
    unique_customers: int
    revenue_growth_pct: float | None


def analyze_revenue_trends(
    session: Session,
    settings: Settings,
    months: int | None = None,
) -> list[RevenueTrendData]:
    """
    Analyze revenue trends by month.

    Args:
        session: Database session
        settings: Application settings
        months: Number of months to analyze (defaults to settings value)

    Returns:
        List of revenue trends by period
    """
    period_months = months if months is not None else settings.analysis_months

    # Query invoices
    query = session.query(
        FactInvoice.customer_id,
        FactInvoice.amount,
        FactInvoice.tran_date,
    )

    df = pd.read_sql(query.statement, session.bind)

    if df.empty:
        return []

    # Convert date and filter to period
    df["tran_date"] = pd.to_datetime(df["tran_date"])
    cutoff_date = pd.Timestamp.now() - pd.DateOffset(months=period_months)
    df = df[df["tran_date"] >= cutoff_date]

    # Extract period (YYYY-MM)
    df["period"] = df["tran_date"].dt.to_period("M").astype(str)

    # Aggregate by period
    aggregated = df.groupby("period").agg({
        "amount": ["sum", "count", "mean"],
        "customer_id": "nunique",
    })

    results: list[RevenueTrendData] = []
    prev_revenue = None

    for period, row in aggregated.iterrows():
        total_revenue = float(row[("amount", "sum")])

        # Calculate growth
        growth_pct = None
        if prev_revenue is not None and prev_revenue > 0:
            growth_pct = ((total_revenue - prev_revenue) / prev_revenue) * 100

        results.append(
            RevenueTrendData(
                period=str(period),
                total_revenue=total_revenue,
                invoice_count=int(row[("amount", "count")]),
                avg_invoice_size=float(row[("amount", "mean")]),
                unique_customers=int(row[("customer_id", "nunique")]),
                revenue_growth_pct=growth_pct,
            )
        )

        prev_revenue = total_revenue

    return results


@dataclass
class CustomerLifetimeValue:
    """Customer lifetime value metrics."""

    customer_id: str
    company_name: str
    total_revenue: float
    invoice_count: int
    avg_order_value: float
    first_purchase: str | None
    last_purchase: str | None
    days_since_last_purchase: int | None


def calculate_customer_ltv(session: Session) -> list[CustomerLifetimeValue]:
    """
    Calculate customer lifetime value.

    Args:
        session: Database session

    Returns:
        List of customer LTV metrics sorted by total revenue
    """
    query = session.query(
        DimCustomer.id,
        DimCustomer.company_name,
        FactInvoice.amount,
        FactInvoice.tran_date,
    ).join(FactInvoice, DimCustomer.id == FactInvoice.customer_id)

    df = pd.read_sql(query.statement, session.bind)

    if df.empty:
        return []

    df["tran_date"] = pd.to_datetime(df["tran_date"])

    # Aggregate by customer
    aggregated = df.groupby(["id", "company_name"]).agg({
        "amount": ["sum", "count", "mean"],
        "tran_date": ["min", "max"],
    })

    results: list[CustomerLifetimeValue] = []
    now = pd.Timestamp.now()

    for (customer_id, company_name), row in aggregated.iterrows():
        last_purchase = pd.to_datetime(row[("tran_date", "max")])
        days_since = (now - last_purchase).days if last_purchase else None

        results.append(
            CustomerLifetimeValue(
                customer_id=str(customer_id),
                company_name=str(company_name),
                total_revenue=float(row[("amount", "sum")]),
                invoice_count=int(row[("amount", "count")]),
                avg_order_value=float(row[("amount", "mean")]),
                first_purchase=str(row[("tran_date", "min")]),
                last_purchase=str(row[("tran_date", "max")]),
                days_since_last_purchase=days_since,
            )
        )

    # Sort by total revenue descending
    results.sort(key=lambda x: x.total_revenue, reverse=True)
    return results
