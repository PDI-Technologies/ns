"""
Salesforce revenue pipeline analysis.

Based on financial-analytics Salesforce integration patterns.
"""

from dataclasses import dataclass
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from financial_analytics.db.models import SalesforceOpportunity


@dataclass
class RevenuePipelineData:
    """Revenue pipeline metrics."""

    stage_name: str
    opportunity_count: int
    total_amount: float
    weighted_amount: float
    avg_deal_size: float
    win_probability: float


@dataclass
class ProductRevenueData:
    """Product revenue breakdown."""

    industry: str
    opportunity_count: int
    total_revenue: float
    avg_deal_size: float


def analyze_revenue_pipeline(session: Session) -> list[RevenuePipelineData]:
    """
    Analyze Salesforce opportunity pipeline by stage.

    Args:
        session: Database session

    Returns:
        Pipeline metrics by stage
    """
    query = session.query(
        SalesforceOpportunity.stage_name,
        SalesforceOpportunity.amount,
        SalesforceOpportunity.probability,
        SalesforceOpportunity.is_closed,
    ).filter(SalesforceOpportunity.is_closed == False)  # noqa: E712

    df = pd.read_sql(query.statement, session.bind)

    if df.empty:
        return []

    # Calculate weighted amount
    df["weighted_amount"] = df["amount"].fillna(0) * (df["probability"].fillna(0) / 100.0)

    # Aggregate by stage
    aggregated = df.groupby("stage_name").agg({
        "amount": ["count", "sum", "mean"],
        "weighted_amount": "sum",
        "probability": "mean",
    })

    results: list[RevenuePipelineData] = []

    for stage_name, row in aggregated.iterrows():
        results.append(
            RevenuePipelineData(
                stage_name=str(stage_name),
                opportunity_count=int(row[("amount", "count")]),
                total_amount=float(row[("amount", "sum")]),
                weighted_amount=float(row[("weighted_amount", "sum")]),
                avg_deal_size=float(row[("amount", "mean")]),
                win_probability=float(row[("probability", "mean")]),
            )
        )

    # Sort by weighted amount descending
    results.sort(key=lambda x: x.weighted_amount, reverse=True)
    return results


def analyze_closed_won_revenue(
    session: Session,
    months: int = 12,
) -> list[dict[str, Any]]:
    """
    Analyze closed-won revenue by period.

    Args:
        session: Database session
        months: Number of months to analyze

    Returns:
        Monthly revenue metrics
    """
    query = session.query(
        SalesforceOpportunity.close_date,
        SalesforceOpportunity.amount,
        SalesforceOpportunity.account_name,
    ).filter(SalesforceOpportunity.is_won == True)  # noqa: E712

    df = pd.read_sql(query.statement, session.bind)

    if df.empty:
        return []

    # Convert date and filter to period
    df["close_date"] = pd.to_datetime(df["close_date"])
    cutoff_date = pd.Timestamp.now() - pd.DateOffset(months=months)
    df = df[df["close_date"] >= cutoff_date]

    # Extract period (YYYY-MM)
    df["period"] = df["close_date"].dt.to_period("M").astype(str)

    # Aggregate by period
    aggregated = df.groupby("period").agg({
        "amount": ["sum", "count", "mean"],
        "account_name": "nunique",
    })

    results = []
    prev_revenue = None

    for period, row in aggregated.iterrows():
        total_revenue = float(row[("amount", "sum")])

        # Calculate growth
        growth_pct = None
        if prev_revenue is not None and prev_revenue > 0:
            growth_pct = ((total_revenue - prev_revenue) / prev_revenue) * 100

        results.append({
            "period": str(period),
            "total_revenue": total_revenue,
            "deal_count": int(row[("amount", "count")]),
            "avg_deal_size": float(row[("amount", "mean")]),
            "unique_accounts": int(row[("account_name", "nunique")]),
            "revenue_growth_pct": growth_pct,
        })

        prev_revenue = total_revenue

    return results


def analyze_by_industry(session: Session) -> list[ProductRevenueData]:
    """
    Analyze revenue by customer industry.

    Args:
        session: Database session

    Returns:
        Revenue breakdown by industry
    """
    query = session.query(
        SalesforceOpportunity.industry,
        SalesforceOpportunity.amount,
    ).filter(
        SalesforceOpportunity.is_won == True,  # noqa: E712
        SalesforceOpportunity.industry.isnot(None),
    )

    df = pd.read_sql(query.statement, session.bind)

    if df.empty:
        return []

    # Aggregate by industry
    aggregated = df.groupby("industry").agg({
        "amount": ["count", "sum", "mean"],
    })

    results: list[ProductRevenueData] = []

    for industry, row in aggregated.iterrows():
        results.append(
            ProductRevenueData(
                industry=str(industry),
                opportunity_count=int(row[("amount", "count")]),
                total_revenue=float(row[("amount", "sum")]),
                avg_deal_size=float(row[("amount", "mean")]),
            )
        )

    # Sort by total revenue descending
    results.sort(key=lambda x: x.total_revenue, reverse=True)
    return results
