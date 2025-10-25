# Vendor Analytics

Comprehensive vendor spend analysis, duplicate detection, and cost optimization methodologies for enterprise finance teams.

## Contents

- [Overview](#overview)
- [Core Methodologies](#core-methodologies)
  - [Descriptive Analysis](#descriptive-analysis) - Spend aggregation, trend analysis, variance analysis
  - [Pareto Analysis (80/20 Rule)](#pareto-analysis-8020-rule)
- [Spend Segmentation](#spend-segmentation)
- [Duplicate Vendor Detection](#duplicate-vendor-detection)
  - [Fuzzy String Matching](#fuzzy-string-matching)
  - [Advanced Duplicate Detection](#advanced-duplicate-detection)
- [Payment Terms Analysis](#payment-terms-analysis)
- [Maverick Spend Detection](#maverick-spend-detection)
- [Date Range Analysis](#date-range-analysis)
- [Best Practices](#best-practices)
- [Report Generation](#report-generation)

## Overview

Vendor analytics is a strategic process that evaluates how organizations allocate procurement resources and spending patterns to drive cost reduction and operational efficiency. This document covers industry-standard methodologies used by finance and procurement teams.

## Core Methodologies

### Descriptive Analysis

Descriptive analysis focuses on what happened historically by organizing past buying data to reveal patterns and trends.

**Spend Aggregation**
```python
from dataclasses import dataclass
from datetime import datetime

import pandas as pd
from sqlalchemy.orm import Session

@dataclass
class VendorSpendSummary:
    """Vendor spend summary with key metrics."""

    vendor_id: str
    vendor_name: str
    total_spend: float
    transaction_count: int
    average_transaction: float
    currency: str | None
    last_transaction_date: datetime | None

def analyze_vendor_spend(
    session: Session,
    vendor_id: str | None = None,
) -> list[VendorSpendSummary]:
    """
    Analyze vendor spend with transaction aggregation.

    Pattern from vendor-analysis application:
    - Query database for transactions
    - Convert to Pandas DataFrame for aggregation
    - Group by vendor
    - Calculate summary metrics
    - Sort by total spend descending
    """
    query = session.query(TransactionRecord)
    if vendor_id:
        query = query.filter(TransactionRecord.vendor_id == vendor_id)

    transactions = query.all()

    if not transactions:
        return []

    # Convert to pandas for analysis
    df = pd.DataFrame([
        {
            "vendor_id": t.vendor_id,
            "amount": t.amount,
            "tran_date": t.tran_date,
            "currency": t.currency,
        }
        for t in transactions
    ])

    summary_data: list[VendorSpendSummary] = []

    for vendor_id_group, group_df in df.groupby("vendor_id"):
        vendor = session.query(VendorRecord).filter_by(id=str(vendor_id_group)).first()
        if not vendor:
            continue

        summary = VendorSpendSummary(
            vendor_id=str(vendor_id_group),
            vendor_name=vendor.company_name or vendor.entity_id,
            total_spend=float(group_df["amount"].sum()),
            transaction_count=len(group_df),
            average_transaction=float(group_df["amount"].mean()),
            currency=group_df["currency"].iloc[0] if not group_df["currency"].isna().all() else None,
            last_transaction_date=group_df["tran_date"].max(),
        )
        summary_data.append(summary)

    # Sort by total spend descending
    summary_data.sort(key=lambda x: x.total_spend, reverse=True)

    return summary_data
```

**Trend Analysis**
```python
def analyze_spend_trends(
    transactions: pd.DataFrame,
    period: str = 'M',  # 'D', 'W', 'M', 'Q', 'Y'
) -> pd.DataFrame:
    """
    Track spending patterns over time.

    Args:
        transactions: DataFrame with 'transaction_date' and 'amount' columns
        period: Pandas frequency string (D=daily, W=weekly, M=monthly, Q=quarterly, Y=yearly)

    Returns:
        DataFrame with period-over-period spend trends
    """
    transactions['date'] = pd.to_datetime(transactions['transaction_date'])

    trends = transactions.groupby(pd.Grouper(key='date', freq=period)).agg({
        'amount': 'sum',
        'transaction_id': 'count'
    }).rename(columns={'transaction_id': 'transaction_count'})

    # Calculate growth rates
    trends['spend_growth_pct'] = trends['amount'].pct_change() * 100
    trends['avg_transaction_value'] = trends['amount'] / trends['transaction_count']

    return trends
```

**Variance Analysis**
```python
@dataclass
class SpendVariance:
    """Spend variance metrics."""

    actual: float
    budget: float
    variance: float
    variance_pct: float
    is_favorable: bool
    threshold_breach: bool
    explanation: str

def analyze_spend_variance(
    actual: float,
    budget: float,
    threshold_pct: float = 5.0,
) -> SpendVariance:
    """
    Compare actual spending to budget.

    Args:
        actual: Actual spend amount
        budget: Budgeted spend amount
        threshold_pct: Percentage threshold for investigation

    Returns:
        Variance analysis with breach indicators

    Best Practice: Fail-fast on missing data
    """
    if budget == 0:
        raise ValueError("Budget cannot be zero for variance calculation")

    variance = actual - budget
    variance_pct = (variance / budget) * 100

    # For costs, negative variance is favorable (under budget)
    is_favorable = variance < 0
    threshold_breach = abs(variance_pct) > threshold_pct

    explanation = (
        f"{'Favorable' if is_favorable else 'Unfavorable'} variance of "
        f"{abs(variance_pct):.1f}% ({'under' if is_favorable else 'over'} budget)"
    )

    return SpendVariance(
        actual=actual,
        budget=budget,
        variance=variance,
        variance_pct=variance_pct,
        is_favorable=is_favorable,
        threshold_breach=threshold_breach,
        explanation=explanation,
    )
```

### Pareto Analysis (80/20 Rule)

Pareto analysis identifies which suppliers constitute the majority of organizational spend, enabling finance teams to focus resources on managing the most impactful suppliers.

```python
def pareto_analysis(
    vendor_summaries: list[VendorSpendSummary],
    target_percentage: float = 80.0,
) -> dict:
    """
    Apply Pareto analysis to vendor spend.

    Args:
        vendor_summaries: List of vendor spend summaries (sorted by spend descending)
        target_percentage: Target cumulative percentage (default 80%)

    Returns:
        Dictionary with Pareto metrics
    """
    if not vendor_summaries:
        return {
            "total_vendors": 0,
            "key_vendors": 0,
            "key_vendor_percentage": 0.0,
            "total_spend": 0.0,
            "key_vendor_spend": 0.0,
        }

    total_spend = sum(v.total_spend for v in vendor_summaries)
    cumulative_spend = 0.0
    key_vendor_count = 0

    for vendor in vendor_summaries:
        cumulative_spend += vendor.total_spend
        key_vendor_count += 1

        if (cumulative_spend / total_spend * 100) >= target_percentage:
            break

    return {
        "total_vendors": len(vendor_summaries),
        "key_vendors": key_vendor_count,
        "key_vendor_percentage": (key_vendor_count / len(vendor_summaries) * 100),
        "total_spend": total_spend,
        "key_vendor_spend": cumulative_spend,
        "key_vendor_spend_percentage": (cumulative_spend / total_spend * 100),
    }
```

## Spend Segmentation

Finance teams categorize spending into distinct segments for targeted analysis and management.

```python
from enum import Enum

class SpendCategory(Enum):
    """Spend category classification."""

    DIRECT = "direct"          # Production/core services costs
    INDIRECT = "indirect"      # Non-core expenses
    TAIL = "tail"             # Small, fragmented purchases

class VendorTier(Enum):
    """Vendor tier classification."""

    STRATEGIC = "strategic"    # Critical suppliers
    PREFERRED = "preferred"    # Regular vendors with good terms
    TRANSACTIONAL = "transactional"  # One-off or low-value vendors

def segment_vendors(
    vendor_summaries: list[VendorSpendSummary],
    strategic_threshold: float = 100000.0,  # Top spend vendors
    tail_threshold: float = 1000.0,         # Low spend vendors
) -> dict[VendorTier, list[VendorSpendSummary]]:
    """
    Segment vendors by spend tier.

    Args:
        vendor_summaries: List of vendor spend summaries
        strategic_threshold: Minimum total spend for strategic tier
        tail_threshold: Maximum total spend for tail tier

    Returns:
        Dictionary mapping tiers to vendor lists
    """
    segments: dict[VendorTier, list[VendorSpendSummary]] = {
        VendorTier.STRATEGIC: [],
        VendorTier.PREFERRED: [],
        VendorTier.TRANSACTIONAL: [],
    }

    for vendor in vendor_summaries:
        if vendor.total_spend >= strategic_threshold:
            segments[VendorTier.STRATEGIC].append(vendor)
        elif vendor.total_spend >= tail_threshold:
            segments[VendorTier.PREFERRED].append(vendor)
        else:
            segments[VendorTier.TRANSACTIONAL].append(vendor)

    return segments
```

## Duplicate Vendor Detection

Duplicate vendors lead to split payment terms, missed volume discounts, inaccurate spend reporting, and difficulty tracking vendor relationships.

### Fuzzy String Matching

```python
from difflib import SequenceMatcher

@dataclass
class DuplicatePair:
    """Potential duplicate vendor pair."""

    vendor_1_id: str
    vendor_1_name: str
    vendor_2_id: str
    vendor_2_name: str
    similarity_score: float

def calculate_similarity(str1: str, str2: str) -> float:
    """
    Calculate similarity between two strings using SequenceMatcher.

    Args:
        str1: First string
        str2: Second string

    Returns:
        Similarity score (0.0 to 1.0)

    Implementation from vendor-analysis application
    """
    if not str1 or not str2:
        return 0.0

    # Normalize strings
    s1 = str1.lower().strip()
    s2 = str2.lower().strip()

    return SequenceMatcher(None, s1, s2).ratio()

def detect_duplicate_vendors(
    session: Session,
    threshold: float = 0.85,
) -> list[DuplicatePair]:
    """
    Detect potential duplicate vendors using fuzzy matching.

    Args:
        session: Database session
        threshold: Similarity threshold (0.0 to 1.0)

    Returns:
        List of potential duplicate pairs sorted by similarity

    Best Practice: Industry-standard threshold is 0.85-0.90
    """
    # Get all active vendors
    vendors = session.query(VendorRecord).filter_by(is_inactive=False).all()

    duplicates: list[DuplicatePair] = []

    # Compare all pairs (O(n^2) - acceptable for vendor counts < 10,000)
    for i, vendor1 in enumerate(vendors):
        name1 = vendor1.company_name or vendor1.entity_id

        for vendor2 in vendors[i + 1:]:
            name2 = vendor2.company_name or vendor2.entity_id

            similarity = calculate_similarity(name1, name2)

            if similarity >= threshold:
                duplicates.append(
                    DuplicatePair(
                        vendor_1_id=vendor1.id,
                        vendor_1_name=name1,
                        vendor_2_id=vendor2.id,
                        vendor_2_name=name2,
                        similarity_score=similarity,
                    )
                )

    # Sort by similarity score descending
    duplicates.sort(key=lambda x: x.similarity_score, reverse=True)

    return duplicates
```

### Advanced Duplicate Detection

For more sophisticated detection, combine multiple signals:

```python
def advanced_duplicate_detection(
    vendors: list[VendorRecord],
    name_threshold: float = 0.85,
) -> list[DuplicatePair]:
    """
    Advanced duplicate detection using multiple signals.

    Signals:
    - Name similarity (fuzzy matching)
    - Same tax ID (exact match)
    - Same address (normalized)
    - Same contact email/phone
    """
    duplicates: list[DuplicatePair] = []

    for i, vendor1 in enumerate(vendors):
        for vendor2 in vendors[i + 1:]:
            score = 0.0
            signals = []

            # Signal 1: Name similarity (weight: 0.4)
            name_sim = calculate_similarity(
                vendor1.company_name or "",
                vendor2.company_name or ""
            )
            if name_sim >= name_threshold:
                score += name_sim * 0.4
                signals.append("name_match")

            # Signal 2: Tax ID match (weight: 0.3)
            if vendor1.tax_id and vendor2.tax_id:
                if vendor1.tax_id == vendor2.tax_id:
                    score += 0.3
                    signals.append("tax_id_match")

            # Signal 3: Address similarity (weight: 0.2)
            if vendor1.address and vendor2.address:
                addr_sim = calculate_similarity(
                    normalize_address(vendor1.address),
                    normalize_address(vendor2.address)
                )
                if addr_sim >= 0.9:
                    score += addr_sim * 0.2
                    signals.append("address_match")

            # Signal 4: Contact match (weight: 0.1)
            if vendor1.email and vendor2.email:
                if vendor1.email.lower() == vendor2.email.lower():
                    score += 0.1
                    signals.append("email_match")

            if score >= 0.85:  # Combined threshold
                duplicates.append(
                    DuplicatePair(
                        vendor_1_id=vendor1.id,
                        vendor_1_name=vendor1.company_name or vendor1.entity_id,
                        vendor_2_id=vendor2.id,
                        vendor_2_name=vendor2.company_name or vendor2.entity_id,
                        similarity_score=score,
                    )
                )

    return sorted(duplicates, key=lambda x: x.similarity_score, reverse=True)

def normalize_address(address: str) -> str:
    """Normalize address for comparison."""
    normalized = address.lower().strip()

    # Standardize common abbreviations
    replacements = {
        " street": " st",
        " avenue": " ave",
        " road": " rd",
        " drive": " dr",
        " suite": " ste",
        " building": " bldg",
        ".": "",
        ",": "",
    }

    for old, new in replacements.items():
        normalized = normalized.replace(old, new)

    return normalized
```

## Payment Terms Analysis

Optimize cash flow by analyzing vendor payment terms and negotiation opportunities.

```python
@dataclass
class PaymentTermsAnalysis:
    """Payment terms analysis results."""

    vendor_id: str
    vendor_name: str
    payment_terms: str  # e.g., "Net 30", "Net 60", "2/10 Net 30"
    average_days_to_pay: float
    early_payment_discount_available: bool
    discount_percentage: float | None
    discount_days: int | None
    annual_spend: float
    potential_savings: float

def analyze_payment_terms(
    vendor_summaries: list[VendorSpendSummary],
    payment_history: pd.DataFrame,
) -> list[PaymentTermsAnalysis]:
    """
    Analyze payment terms and identify optimization opportunities.

    Args:
        vendor_summaries: Vendor spend summaries
        payment_history: DataFrame with columns: vendor_id, invoice_date,
                        payment_date, payment_terms, amount

    Returns:
        List of payment terms analysis results
    """
    results: list[PaymentTermsAnalysis] = []

    for vendor in vendor_summaries:
        vendor_payments = payment_history[
            payment_history['vendor_id'] == vendor.vendor_id
        ]

        if vendor_payments.empty:
            continue

        # Calculate average days to pay
        vendor_payments['days_to_pay'] = (
            pd.to_datetime(vendor_payments['payment_date']) -
            pd.to_datetime(vendor_payments['invoice_date'])
        ).dt.days

        avg_days = vendor_payments['days_to_pay'].mean()

        # Parse payment terms (simplified example)
        terms = vendor_payments['payment_terms'].iloc[0]
        discount_pct, discount_days = parse_payment_terms(terms)

        # Calculate potential savings from early payment discounts
        potential_savings = 0.0
        if discount_pct and discount_days:
            if avg_days > discount_days:
                # Not taking advantage of discount
                potential_savings = vendor.total_spend * (discount_pct / 100)

        results.append(
            PaymentTermsAnalysis(
                vendor_id=vendor.vendor_id,
                vendor_name=vendor.vendor_name,
                payment_terms=terms,
                average_days_to_pay=avg_days,
                early_payment_discount_available=discount_pct is not None,
                discount_percentage=discount_pct,
                discount_days=discount_days,
                annual_spend=vendor.total_spend,
                potential_savings=potential_savings,
            )
        )

    # Sort by potential savings descending
    results.sort(key=lambda x: x.potential_savings, reverse=True)

    return results

def parse_payment_terms(terms: str) -> tuple[float | None, int | None]:
    """
    Parse payment terms string.

    Examples:
        "2/10 Net 30" -> (2.0, 10)  # 2% discount if paid in 10 days
        "Net 30" -> (None, None)
        "1/15 Net 45" -> (1.0, 15)
    """
    import re

    # Match pattern like "2/10 Net 30"
    match = re.match(r'(\d+(?:\.\d+)?)/(\d+)', terms)
    if match:
        discount_pct = float(match.group(1))
        discount_days = int(match.group(2))
        return discount_pct, discount_days

    return None, None
```

## Maverick Spend Detection

Maverick spending refers to purchases made outside established procurement processes and vendor contracts.

```python
@dataclass
class MaverickSpend:
    """Maverick spend detection result."""

    transaction_id: str
    vendor_id: str
    vendor_name: str
    amount: float
    transaction_date: datetime
    is_approved_vendor: bool
    is_under_contract: bool
    category: str
    reason: str

def detect_maverick_spend(
    session: Session,
    approved_vendor_ids: set[str],
    contracted_vendor_ids: set[str],
) -> list[MaverickSpend]:
    """
    Identify purchases outside approved processes.

    Args:
        session: Database session
        approved_vendor_ids: Set of approved vendor IDs
        contracted_vendor_ids: Set of vendors with active contracts

    Returns:
        List of maverick spend transactions
    """
    all_transactions = session.query(TransactionRecord).all()
    maverick_transactions: list[MaverickSpend] = []

    for txn in all_transactions:
        is_approved = txn.vendor_id in approved_vendor_ids
        is_contracted = txn.vendor_id in contracted_vendor_ids

        # Flag if not approved or not under contract
        if not is_approved or not is_contracted:
            vendor = session.query(VendorRecord).filter_by(id=txn.vendor_id).first()

            reason = []
            if not is_approved:
                reason.append("vendor_not_approved")
            if not is_contracted:
                reason.append("no_active_contract")

            maverick_transactions.append(
                MaverickSpend(
                    transaction_id=txn.id,
                    vendor_id=txn.vendor_id,
                    vendor_name=vendor.company_name if vendor else "Unknown",
                    amount=txn.amount,
                    transaction_date=txn.tran_date,
                    is_approved_vendor=is_approved,
                    is_under_contract=is_contracted,
                    category=txn.category or "Uncategorized",
                    reason=", ".join(reason),
                )
            )

    # Sort by amount descending (focus on high-value maverick spend)
    maverick_transactions.sort(key=lambda x: x.amount, reverse=True)

    return maverick_transactions
```

## Date Range Analysis

```python
def get_vendors_by_date_range(
    session: Session,
    start_date: datetime,
    end_date: datetime,
) -> list[VendorSpendSummary]:
    """
    Analyze vendor spend within specific date range.

    Pattern from vendor-analysis application:
    - Filter transactions by date range
    - Aggregate by vendor
    - Return sorted summaries
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

    df = pd.DataFrame([
        {
            "vendor_id": t.vendor_id,
            "amount": t.amount,
            "tran_date": t.tran_date,
            "currency": t.currency,
        }
        for t in transactions
    ])

    summary_data: list[VendorSpendSummary] = []

    for vendor_id, group_df in df.groupby("vendor_id"):
        vendor = session.query(VendorRecord).filter_by(id=str(vendor_id)).first()
        if not vendor:
            continue

        summary = VendorSpendSummary(
            vendor_id=str(vendor_id),
            vendor_name=vendor.company_name or vendor.entity_id,
            total_spend=float(group_df["amount"].sum()),
            transaction_count=len(group_df),
            average_transaction=float(group_df["amount"].mean()),
            currency=group_df["currency"].iloc[0] if not group_df["currency"].isna().all() else None,
            last_transaction_date=group_df["tran_date"].max(),
        )
        summary_data.append(summary)

    summary_data.sort(key=lambda x: x.total_spend, reverse=True)
    return summary_data
```

## Best Practices

### Data Validation

Based on industry standards for financial data accuracy:

1. **Standardize data formats** - Establish uniform formats for dates (YYYY-MM-DD), currency symbols, and numeric values
2. **Automated validation rules** - Apply predefined criteria to datasets, flagging entries that don't meet established standards
3. **Regular audits** - Verify that transactions are accurate and properly recorded
4. **Strong validation at entry** - Check for errors before data enters the system
5. **Edit tests** - Look for incorrect arithmetic, data entry errors, and significant increases/decreases

### Fail-Fast Discipline

```python
def validate_spend_data(spend_amount: float, currency: str) -> None:
    """
    Validate spend data with fail-fast approach.

    Raises:
        ValueError: If data is invalid
    """
    if spend_amount < 0:
        raise ValueError(f"Spend amount cannot be negative: {spend_amount}")

    if not currency:
        raise ValueError("Currency is required for spend analysis")

    if len(currency) != 3:
        raise ValueError(f"Currency must be 3-letter ISO code: {currency}")
```

### Performance Optimization

1. **Use database aggregation** - Don't pull all rows into memory
2. **Index date columns** - Critical for date range queries
3. **Partition large tables by period** - Improve query performance
4. **Cache calculated metrics** - Avoid redundant calculations

### Accuracy Requirements

```python
from decimal import Decimal

# ALWAYS use Decimal for financial calculations
def calculate_total_spend(amounts: list[float]) -> Decimal:
    """
    Calculate total spend with precision.

    Best Practice: Use Decimal type, not float, for financial calculations
    """
    return sum(Decimal(str(amount)) for amount in amounts)

# Round consistently to 2 decimals for currency
def format_currency(amount: Decimal) -> str:
    """Format currency with 2 decimal precision."""
    return f"{amount:.2f}"
```

## Report Generation

### Vendor Spend Report

```python
from rich.console import Console
from rich.table import Table

def generate_spend_report(
    vendor_summaries: list[VendorSpendSummary],
    top_n: int = 10,
) -> None:
    """
    Generate formatted vendor spend report.

    Uses Rich library for CLI output (pattern from vendor-analysis app)
    """
    console = Console()

    table = Table(title=f"Top {top_n} Vendors by Spend")
    table.add_column("Rank", style="cyan", justify="right")
    table.add_column("Vendor Name", style="white")
    table.add_column("Total Spend", style="green", justify="right")
    table.add_column("Transactions", style="yellow", justify="right")
    table.add_column("Avg Transaction", style="magenta", justify="right")

    for i, vendor in enumerate(vendor_summaries[:top_n], 1):
        table.add_row(
            str(i),
            vendor.vendor_name,
            f"${vendor.total_spend:,.2f}",
            str(vendor.transaction_count),
            f"${vendor.average_transaction:,.2f}",
        )

    console.print(table)
```

### Duplicate Vendor Report

```python
def generate_duplicate_report(duplicates: list[DuplicatePair]) -> None:
    """Generate formatted duplicate vendor report."""
    console = Console()

    table = Table(title="Potential Duplicate Vendors")
    table.add_column("Vendor 1", style="white")
    table.add_column("Vendor 2", style="white")
    table.add_column("Similarity", style="yellow", justify="right")

    for dup in duplicates:
        similarity_pct = f"{dup.similarity_score * 100:.1f}%"
        table.add_row(
            dup.vendor_1_name,
            dup.vendor_2_name,
            similarity_pct,
        )

    console.print(table)
```

## Integration Patterns

See [../integrations/netsuite.md](../integrations/netsuite.md) for extracting vendor and transaction data from NetSuite using the vendor-analysis application architecture.

## Complete Example

See [../examples/cost-analysis-cli.md](../examples/cost-analysis-cli.md) for a complete CLI application implementing these patterns.
