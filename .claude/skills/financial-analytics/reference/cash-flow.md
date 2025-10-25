# Cash Flow Analysis

Working capital metrics, cash conversion cycle analysis, and treasury management KPIs for Financial Planning and Analysis (FP&A).

## Contents

- [Overview](#overview)
- [Core Working Capital Metrics](#core-working-capital-metrics)
  - [Days Sales Outstanding (DSO)](#days-sales-outstanding-dso)
  - [Days Payable Outstanding (DPO)](#days-payable-outstanding-dpo)
  - [Days Inventory Outstanding (DIO)](#days-inventory-outstanding-dio)
  - [Cash Conversion Cycle (CCC)](#cash-conversion-cycle-ccc)
- [Working Capital Requirement](#working-capital-requirement)
- [AR/AP Aging Analysis](#arap-aging-analysis)
- [Treasury Management KPIs](#treasury-management-kpis)
  - [Liquidity Ratios](#liquidity-ratios)
  - [Days Cash on Hand](#days-cash-on-hand-dcoh)
- [Trend Analysis](#trend-analysis)
- [Best Practices for FP&A](#best-practices-for-fpa)

## Overview

Working capital metrics form the foundation of operational financial management, providing visibility into how efficiently a company manages its cash conversion cycle and operational liquidity. These metrics work together to reveal the timing gap between cash outflows to suppliers and cash inflows from customers.

## Core Working Capital Metrics

### Days Sales Outstanding (DSO)

Days Sales Outstanding measures the average number of days a company takes to collect payment from customers after a sale.

```python
from dataclasses import dataclass
from decimal import Decimal

@dataclass
class DSOMetrics:
    """Days Sales Outstanding metrics."""

    accounts_receivable: Decimal
    revenue: Decimal
    period_days: int
    dso: Decimal

def calculate_dso(
    accounts_receivable: Decimal,
    revenue: Decimal,
    period_days: int = 365,
) -> DSOMetrics:
    """
    Calculate Days Sales Outstanding.

    Formula: DSO = (Accounts Receivable / Net Revenue) × Period Days

    Args:
        accounts_receivable: Total AR balance
        revenue: Net revenue for the period
        period_days: Number of days in period (365 for annual, 90 for quarterly)

    Returns:
        DSO metrics

    Best Practice: Use average AR (beginning + ending / 2) rather than
    period-end balance to smooth seasonal variations
    """
    if revenue == Decimal('0'):
        raise ValueError("Revenue cannot be zero for DSO calculation")

    dso = (accounts_receivable / revenue) * Decimal(str(period_days))

    return DSOMetrics(
        accounts_receivable=accounts_receivable,
        revenue=revenue,
        period_days=period_days,
        dso=dso.quantize(Decimal('0.01')),  # Round to 2 decimals
    )
```

**Best Practices:**

1. **Use average AR** - Calculate using (beginning AR + ending AR) / 2 to smooth seasonal fluctuations
2. **Consistent periods** - Always use same period (monthly, quarterly, annually) for comparisons
3. **Lower is better** - Lower DSO indicates faster collection, improving cash flow
4. **Industry benchmarks** - Compare against industry standards (B2B typically 30-60 days, B2C 0-15 days)

### Days Payable Outstanding (DPO)

Days Payable Outstanding represents the average number of days a company takes to pay its suppliers.

```python
@dataclass
class DPOMetrics:
    """Days Payable Outstanding metrics."""

    accounts_payable: Decimal
    cogs: Decimal
    period_days: int
    dpo: Decimal

def calculate_dpo(
    accounts_payable: Decimal,
    cogs: Decimal,
    period_days: int = 365,
) -> DPOMetrics:
    """
    Calculate Days Payable Outstanding.

    Formula: DPO = (Accounts Payable / Cost of Goods Sold) × Period Days

    Args:
        accounts_payable: Total AP balance
        cogs: Cost of goods sold for the period
        period_days: Number of days in period

    Returns:
        DPO metrics

    Best Practice: Higher DPO indicates favorable payment terms and
    better cash management, but excessively high DPO can strain
    supplier relationships
    """
    if cogs == Decimal('0'):
        raise ValueError("COGS cannot be zero for DPO calculation")

    dpo = (accounts_payable / cogs) * Decimal(str(period_days))

    return DPOMetrics(
        accounts_payable=accounts_payable,
        cogs=cogs,
        period_days=period_days,
        dpo=dpo.quantize(Decimal('0.01')),
    )
```

**Strategic Considerations:**

1. **Balance optimization with relationships** - Maximize DPO without damaging supplier trust
2. **Early payment discounts** - Calculate ROI of discounts vs extended payment
3. **Negotiation leverage** - High-spend vendors may offer better terms

### Days Inventory Outstanding (DIO)

Days Inventory Outstanding measures how long inventory remains in stock before being sold.

```python
@dataclass
class DIOMetrics:
    """Days Inventory Outstanding metrics."""

    inventory: Decimal
    cogs: Decimal
    period_days: int
    dio: Decimal

def calculate_dio(
    inventory: Decimal,
    cogs: Decimal,
    period_days: int = 365,
) -> DIOMetrics:
    """
    Calculate Days Inventory Outstanding.

    Formula: DIO = (Inventory / Cost of Goods Sold) × Period Days

    Args:
        inventory: Total inventory value
        cogs: Cost of goods sold for the period
        period_days: Number of days in period

    Returns:
        DIO metrics

    Critical for manufacturing/retail: Lower DIO indicates efficient
    inventory management and reduces obsolescence risk
    """
    if cogs == Decimal('0'):
        raise ValueError("COGS cannot be zero for DIO calculation")

    dio = (inventory / cogs) * Decimal(str(period_days))

    return DIOMetrics(
        inventory=inventory,
        cogs=cogs,
        period_days=period_days,
        dio=dio.quantize(Decimal('0.01')),
    )
```

**Industry Applications:**

- **Manufacturing:** Track by product line, identify slow-moving SKUs
- **Retail:** Monitor seasonal variations, optimize reorder points
- **Distribution:** Balance carrying costs vs stockout risk

### Cash Conversion Cycle (CCC)

The cash conversion cycle combines all three metrics to show the total number of days between paying suppliers and collecting from customers.

```python
@dataclass
class CashConversionCycle:
    """Cash conversion cycle metrics."""

    dso: Decimal
    dio: Decimal
    dpo: Decimal
    ccc: Decimal
    is_negative: bool

def calculate_cash_conversion_cycle(
    dso: Decimal,
    dio: Decimal,
    dpo: Decimal,
) -> CashConversionCycle:
    """
    Calculate Cash Conversion Cycle.

    Formula: CCC = DIO + DSO - DPO

    Args:
        dso: Days Sales Outstanding
        dio: Days Inventory Outstanding
        dpo: Days Payable Outstanding

    Returns:
        Cash conversion cycle metrics

    Interpretation:
    - Negative CCC: Company receives cash before paying suppliers (optimal)
    - Positive CCC: Company must finance operations during cash gap
    - Lower (more negative) is better
    """
    ccc = dio + dso - dpo
    is_negative = ccc < Decimal('0')

    return CashConversionCycle(
        dso=dso,
        dio=dio,
        dpo=dpo,
        ccc=ccc.quantize(Decimal('0.01')),
        is_negative=is_negative,
    )
```

**Example Calculation:**

```python
# Company financials
dso_metrics = calculate_dso(
    accounts_receivable=Decimal('500000'),
    revenue=Decimal('3650000'),  # $10M annual / 365 days
    period_days=365
)
# DSO = (500,000 / 3,650,000) * 365 = 50 days

dio_metrics = calculate_dio(
    inventory=Decimal('300000'),
    cogs=Decimal('2190000'),  # 60% of revenue
    period_days=365
)
# DIO = (300,000 / 2,190,000) * 365 = 50 days

dpo_metrics = calculate_dpo(
    accounts_payable=Decimal('400000'),
    cogs=Decimal('2190000'),
    period_days=365
)
# DPO = (400,000 / 2,190,000) * 365 = 67 days

ccc = calculate_cash_conversion_cycle(
    dso=dso_metrics.dso,
    dio=dio_metrics.dio,
    dpo=dpo_metrics.dpo,
)
# CCC = 50 + 50 - 67 = 33 days

print(f"Cash Conversion Cycle: {ccc.ccc} days")
# Output: Cash Conversion Cycle: 33.00 days
# Interpretation: Company must finance operations for 33 days
```

## Working Capital Requirement

```python
@dataclass
class WorkingCapitalRequirement:
    """Working capital requirement analysis."""

    inventory: Decimal
    accounts_receivable: Decimal
    accounts_payable: Decimal
    wcr: Decimal
    daily_operating_expense: Decimal
    days_funded: Decimal

def calculate_wcr(
    inventory: Decimal,
    accounts_receivable: Decimal,
    accounts_payable: Decimal,
    daily_operating_expense: Decimal,
) -> WorkingCapitalRequirement:
    """
    Calculate Working Capital Requirement.

    Formula: WCR = Inventory + Accounts Receivable - Accounts Payable

    This metric isolates operational components and excludes cash,
    marketable securities, and interest-bearing debt (financing items).

    Args:
        inventory: Total inventory value
        accounts_receivable: Total AR balance
        accounts_payable: Total AP balance
        daily_operating_expense: Average daily operating expenses

    Returns:
        Working capital requirement metrics
    """
    wcr = inventory + accounts_receivable - accounts_payable

    # Days of operations funded by working capital
    days_funded = wcr / daily_operating_expense if daily_operating_expense > 0 else Decimal('0')

    return WorkingCapitalRequirement(
        inventory=inventory,
        accounts_receivable=accounts_receivable,
        accounts_payable=accounts_payable,
        wcr=wcr,
        daily_operating_expense=daily_operating_expense,
        days_funded=days_funded.quantize(Decimal('0.01')),
    )
```

## AR/AP Aging Analysis

Accounts Receivable and Accounts Payable aging analysis segments outstanding balances by time period to reveal collection effectiveness and payment timing.

```python
from datetime import datetime, timedelta
from enum import Enum

class AgingBucket(Enum):
    """Aging bucket categories."""

    CURRENT = "0-30 days"
    DAYS_31_60 = "31-60 days"
    DAYS_61_90 = "61-90 days"
    OVER_90 = "90+ days"

@dataclass
class AgingBucketSummary:
    """Aging bucket summary."""

    bucket: AgingBucket
    count: int
    amount: Decimal
    percentage: Decimal

@dataclass
class AgingAnalysis:
    """AR/AP aging analysis."""

    total_amount: Decimal
    total_count: int
    buckets: list[AgingBucketSummary]
    days_sales_outstanding: Decimal | None = None

def analyze_ar_aging(
    invoices: list[dict],
    as_of_date: datetime | None = None,
) -> AgingAnalysis:
    """
    Analyze Accounts Receivable aging.

    Args:
        invoices: List of invoice dicts with 'invoice_date', 'amount', 'customer_id'
        as_of_date: Analysis date (default: today)

    Returns:
        AR aging analysis

    Best Practice: Establish aging buckets consistent with payment terms
    (typically 30, 60, 90+ days)
    """
    if as_of_date is None:
        as_of_date = datetime.now()

    buckets_data: dict[AgingBucket, dict] = {
        AgingBucket.CURRENT: {"count": 0, "amount": Decimal('0')},
        AgingBucket.DAYS_31_60: {"count": 0, "amount": Decimal('0')},
        AgingBucket.DAYS_61_90: {"count": 0, "amount": Decimal('0')},
        AgingBucket.OVER_90: {"count": 0, "amount": Decimal('0')},
    }

    total_amount = Decimal('0')

    for invoice in invoices:
        invoice_date = invoice['invoice_date']
        amount = Decimal(str(invoice['amount']))
        days_old = (as_of_date - invoice_date).days

        total_amount += amount

        # Assign to bucket
        if days_old <= 30:
            bucket = AgingBucket.CURRENT
        elif days_old <= 60:
            bucket = AgingBucket.DAYS_31_60
        elif days_old <= 90:
            bucket = AgingBucket.DAYS_61_90
        else:
            bucket = AgingBucket.OVER_90

        buckets_data[bucket]["count"] += 1
        buckets_data[bucket]["amount"] += amount

    # Convert to summaries
    bucket_summaries = [
        AgingBucketSummary(
            bucket=bucket,
            count=data["count"],
            amount=data["amount"],
            percentage=(data["amount"] / total_amount * 100) if total_amount > 0 else Decimal('0'),
        )
        for bucket, data in buckets_data.items()
    ]

    return AgingAnalysis(
        total_amount=total_amount,
        total_count=len(invoices),
        buckets=bucket_summaries,
    )
```

## Treasury Management KPIs

### Liquidity Ratios

```python
@dataclass
class LiquidityRatios:
    """Liquidity ratio metrics."""

    current_ratio: Decimal
    quick_ratio: Decimal
    cash_ratio: Decimal

def calculate_liquidity_ratios(
    current_assets: Decimal,
    current_liabilities: Decimal,
    inventory: Decimal,
    cash: Decimal,
    marketable_securities: Decimal,
) -> LiquidityRatios:
    """
    Calculate liquidity ratios.

    Ratios:
    - Current Ratio = Current Assets / Current Liabilities
    - Quick Ratio = (Current Assets - Inventory) / Current Liabilities
    - Cash Ratio = (Cash + Marketable Securities) / Current Liabilities

    Args:
        current_assets: Total current assets
        current_liabilities: Total current liabilities
        inventory: Inventory value
        cash: Cash balance
        marketable_securities: Liquid investments

    Returns:
        Liquidity ratios

    Benchmarks:
    - Current Ratio: >= 1.0x indicates adequate short-term liquidity
    - Quick Ratio: >= 0.5x to 1.0x (more conservative)
    - Cash Ratio: >= 0.2x (most conservative)
    """
    if current_liabilities == Decimal('0'):
        raise ValueError("Current liabilities cannot be zero")

    current_ratio = current_assets / current_liabilities
    quick_ratio = (current_assets - inventory) / current_liabilities
    cash_ratio = (cash + marketable_securities) / current_liabilities

    return LiquidityRatios(
        current_ratio=current_ratio.quantize(Decimal('0.01')),
        quick_ratio=quick_ratio.quantize(Decimal('0.01')),
        cash_ratio=cash_ratio.quantize(Decimal('0.01')),
    )
```

### Days Cash on Hand (DCOH)

```python
@dataclass
class DaysCashOnHand:
    """Days cash on hand metrics."""

    cash: Decimal
    marketable_securities: Decimal
    daily_operating_expense: Decimal
    dcoh: Decimal

def calculate_days_cash_on_hand(
    cash: Decimal,
    marketable_securities: Decimal,
    annual_operating_expense: Decimal,
) -> DaysCashOnHand:
    """
    Calculate Days Cash on Hand.

    Formula: DCOH = (Cash + Marketable Securities) / Daily Operating Expenses

    Args:
        cash: Cash balance
        marketable_securities: Liquid investments
        annual_operating_expense: Annual operating expenses

    Returns:
        Days cash on hand metrics

    Interpretation: Number of days the company can sustain operations
    using existing cash and liquid equivalents
    """
    daily_operating_expense = annual_operating_expense / Decimal('365')

    if daily_operating_expense == Decimal('0'):
        raise ValueError("Daily operating expense cannot be zero")

    dcoh = (cash + marketable_securities) / daily_operating_expense

    return DaysCashOnHand(
        cash=cash,
        marketable_securities=marketable_securities,
        daily_operating_expense=daily_operating_expense,
        dcoh=dcoh.quantize(Decimal('0.01')),
    )
```

## Trend Analysis

```python
import pandas as pd

def analyze_working_capital_trends(
    financial_data: pd.DataFrame,
) -> pd.DataFrame:
    """
    Analyze working capital trends over time.

    Args:
        financial_data: DataFrame with columns:
            - period_date
            - accounts_receivable
            - inventory
            - accounts_payable
            - revenue
            - cogs

    Returns:
        DataFrame with working capital metrics by period
    """
    trends = pd.DataFrame()

    trends['period'] = financial_data['period_date']
    trends['wcr'] = (
        financial_data['accounts_receivable'] +
        financial_data['inventory'] -
        financial_data['accounts_payable']
    )

    # Calculate metrics
    trends['dso'] = (
        financial_data['accounts_receivable'] /
        financial_data['revenue'] * 365
    )
    trends['dio'] = (
        financial_data['inventory'] /
        financial_data['cogs'] * 365
    )
    trends['dpo'] = (
        financial_data['accounts_payable'] /
        financial_data['cogs'] * 365
    )
    trends['ccc'] = trends['dso'] + trends['dio'] - trends['dpo']

    # Calculate period-over-period changes
    trends['wcr_change'] = trends['wcr'].diff()
    trends['ccc_change'] = trends['ccc'].diff()

    return trends
```

## Best Practices for FP&A

### 1. Establish Baseline Metrics

Track working capital metrics monthly and establish:
- Historical averages (12-month rolling)
- Seasonal patterns
- Industry benchmarks

### 2. Scenario Modeling

```python
def model_ccc_scenarios(
    base_dso: Decimal,
    base_dio: Decimal,
    base_dpo: Decimal,
) -> dict[str, Decimal]:
    """
    Model best-case, base-case, worst-case CCC scenarios.

    Returns:
        Dictionary with scenario CCCs
    """
    scenarios = {
        "best_case": calculate_cash_conversion_cycle(
            dso=base_dso * Decimal('0.9'),  # 10% improvement
            dio=base_dio * Decimal('0.9'),
            dpo=base_dpo * Decimal('1.1'),
        ).ccc,
        "base_case": calculate_cash_conversion_cycle(
            dso=base_dso,
            dio=base_dio,
            dpo=base_dpo,
        ).ccc,
        "worst_case": calculate_cash_conversion_cycle(
            dso=base_dso * Decimal('1.1'),  # 10% deterioration
            dio=base_dio * Decimal('1.1'),
            dpo=base_dpo * Decimal('0.9'),
        ).ccc,
    }

    return scenarios
```

### 3. Working Capital as Percentage of Sales

```python
def calculate_wcr_percentage(
    wcr: Decimal,
    revenue: Decimal,
) -> Decimal:
    """
    Calculate WCR as percentage of sales.

    Normalized metric accounts for business growth and enables
    meaningful comparisons across periods
    """
    if revenue == Decimal('0'):
        raise ValueError("Revenue cannot be zero")

    return (wcr / revenue * 100).quantize(Decimal('0.01'))
```

### 4. Monitor Component Changes

Track individual metric changes to identify drivers of working capital variability:

```python
@dataclass
class WorkingCapitalDrivers:
    """Working capital change drivers."""

    period: str
    dso_change: Decimal
    dio_change: Decimal
    dpo_change: Decimal
    primary_driver: str

def identify_ccc_drivers(
    current: CashConversionCycle,
    prior: CashConversionCycle,
) -> WorkingCapitalDrivers:
    """Identify primary drivers of CCC changes."""
    dso_change = current.dso - prior.dso
    dio_change = current.dio - prior.dio
    dpo_change = current.dpo - prior.dpo

    # Find largest absolute change
    changes = {
        "DSO": abs(dso_change),
        "DIO": abs(dio_change),
        "DPO": abs(dpo_change),
    }
    primary_driver = max(changes, key=changes.get)

    return WorkingCapitalDrivers(
        period="Current vs Prior",
        dso_change=dso_change,
        dio_change=dio_change,
        dpo_change=dpo_change,
        primary_driver=primary_driver,
    )
```

## Data Validation Best Practices

1. **Use Decimal types** - Avoid float precision errors
2. **Validate inputs** - Fail-fast on zero divisors
3. **Consistent periods** - Always use same time periods for comparisons
4. **Average balances** - Use (beginning + ending) / 2 for balance sheet items
5. **Document assumptions** - Clear comments on calculation methods

## Integration with ERP Systems

See [../integrations/netsuite.md](../integrations/netsuite.md) for extracting financial data from NetSuite for working capital analysis.
