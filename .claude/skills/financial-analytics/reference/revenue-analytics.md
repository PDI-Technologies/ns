# Revenue Analytics

Comprehensive revenue analysis including revenue recognition patterns, sales trend analysis, customer lifetime value, churn analysis, and product mix analysis.

## Contents

- [Overview](#overview)
- [Revenue Recognition Patterns](#revenue-recognition-patterns)
  - [ASC 606 / IFRS 15](#asc-606--ifrs-15-revenue-recognition)
- [Sales Trend Analysis](#sales-trend-analysis)
  - [Revenue Growth Metrics](#revenue-growth-metrics)
  - [Revenue Concentration Analysis](#revenue-concentration-analysis)
- [Customer Lifetime Value (CLV)](#customer-lifetime-value-clv)
  - [CLV Calculation](#clv-calculation)
  - [Cohort Analysis](#cohort-analysis)
- [Churn Analysis](#churn-analysis)
  - [Customer Churn Rate](#customer-churn-rate)
  - [Revenue Churn (MRR/ARR)](#revenue-churn-mrrarr)
- [Product Mix Analysis](#product-mix-analysis)
- [SaaS Metrics](#saas-metrics)
  - [ARR/MRR Calculation](#arrmrr-calculation)
  - [Customer Acquisition Cost (CAC)](#customer-acquisition-cost-cac)
- [Best Practices](#best-practices)

## Overview

Revenue analytics transforms sales data into actionable insights about growth drivers, customer behavior, and revenue quality. This guide covers production-ready revenue analysis patterns for FP&A and finance teams.

## Revenue Recognition Patterns

### ASC 606 / IFRS 15 Revenue Recognition

```python
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from enum import Enum

class RecognitionMethod(Enum):
    """Revenue recognition methods."""

    POINT_IN_TIME = "point_in_time"  # Goods sold
    OVER_TIME = "over_time"          # Services, subscriptions

@dataclass
class RevenueRecognition:
    """Revenue recognition calculation."""

    contract_value: Decimal
    recognition_method: RecognitionMethod
    start_date: datetime
    end_date: datetime
    recognized_revenue: Decimal
    deferred_revenue: Decimal

def calculate_revenue_recognition(
    contract_value: Decimal,
    recognition_method: RecognitionMethod,
    start_date: datetime,
    current_date: datetime,
    end_date: datetime,
) -> RevenueRecognition:
    """
    Calculate revenue recognition using ASC 606 / IFRS 15 principles.

    Args:
        contract_value: Total contract value
        recognition_method: Point-in-time or over-time
        start_date: Contract start date
        current_date: Current reporting date
        end_date: Contract end date

    Returns:
        Revenue recognition split

    Best Practice: Recognize revenue over time for subscriptions,
    point-in-time for product sales
    """
    if recognition_method == RecognitionMethod.POINT_IN_TIME:
        # Recognize all revenue at delivery
        recognized = contract_value
        deferred = Decimal('0')
    else:
        # Recognize proportionally over contract period
        total_days = (end_date - start_date).days
        elapsed_days = (current_date - start_date).days

        if elapsed_days <= 0:
            recognized = Decimal('0')
        elif elapsed_days >= total_days:
            recognized = contract_value
        else:
            recognized = contract_value * (Decimal(str(elapsed_days)) / Decimal(str(total_days)))

        deferred = contract_value - recognized

    return RevenueRecognition(
        contract_value=contract_value,
        recognition_method=recognition_method,
        start_date=start_date,
        end_date=end_date,
        recognized_revenue=recognized.quantize(Decimal('0.01')),
        deferred_revenue=deferred.quantize(Decimal('0.01')),
    )
```

## Sales Trend Analysis

### Revenue Growth Metrics

```python
import pandas as pd

def analyze_revenue_trends(
    revenue_data: pd.DataFrame,
    period_column: str = 'period',
    revenue_column: str = 'revenue',
) -> pd.DataFrame:
    """
    Analyze revenue trends with growth metrics.

    Args:
        revenue_data: DataFrame with period and revenue columns
        period_column: Name of period column
        revenue_column: Name of revenue column

    Returns:
        DataFrame with trend metrics
    """
    trends = revenue_data.copy()

    # Period-over-period growth
    trends['revenue_prior'] = trends[revenue_column].shift(1)
    trends['growth_amount'] = trends[revenue_column] - trends['revenue_prior']
    trends['growth_pct'] = (trends['growth_amount'] / trends['revenue_prior'] * 100)

    # Moving averages for smoothing
    trends['ma_3_period'] = trends[revenue_column].rolling(window=3).mean()
    trends['ma_6_period'] = trends[revenue_column].rolling(window=6).mean()

    # Year-over-year comparison
    trends['revenue_yoy'] = trends[revenue_column].shift(12)  # For monthly data
    trends['yoy_growth_pct'] = (
        (trends[revenue_column] - trends['revenue_yoy']) / trends['revenue_yoy'] * 100
    )

    return trends
```

### Revenue Concentration Analysis

```python
@dataclass
class RevenueConcentration:
    """Revenue concentration metrics."""

    total_customers: int
    total_revenue: Decimal
    top_10_customers: int
    top_10_revenue: Decimal
    top_10_percentage: Decimal
    concentration_risk: str  # 'high', 'medium', 'low'

def analyze_revenue_concentration(
    customer_revenue: list[Decimal],
) -> RevenueConcentration:
    """
    Analyze customer revenue concentration risk.

    High concentration (> 50% from top 10 customers) indicates risk.

    Args:
        customer_revenue: List of revenue amounts per customer (sorted desc)

    Returns:
        Revenue concentration analysis
    """
    total_customers = len(customer_revenue)
    total_revenue = sum(customer_revenue)

    # Top 10 customers (or fewer if less than 10 customers)
    top_n = min(10, total_customers)
    top_revenue = sum(customer_revenue[:top_n])
    top_percentage = (top_revenue / total_revenue * 100) if total_revenue > 0 else Decimal('0')

    # Classify risk
    if top_percentage > 50:
        risk = 'high'
    elif top_percentage > 30:
        risk = 'medium'
    else:
        risk = 'low'

    return RevenueConcentration(
        total_customers=total_customers,
        total_revenue=total_revenue,
        top_10_customers=top_n,
        top_10_revenue=top_revenue,
        top_10_percentage=top_percentage.quantize(Decimal('0.01')),
        concentration_risk=risk,
    )
```

## Customer Lifetime Value (CLV)

### CLV Calculation

```python
@dataclass
class CustomerLifetimeValue:
    """Customer lifetime value metrics."""

    avg_purchase_value: Decimal
    purchase_frequency: Decimal
    customer_lifespan_years: Decimal
    clv: Decimal
    customer_acquisition_cost: Decimal
    ltv_to_cac_ratio: Decimal

def calculate_clv(
    avg_purchase_value: Decimal,
    purchases_per_year: Decimal,
    customer_lifespan_years: Decimal,
    gross_margin_pct: Decimal,
    discount_rate: Decimal = Decimal('0.10'),  # 10% discount rate
    customer_acquisition_cost: Decimal | None = None,
) -> CustomerLifetimeValue:
    """
    Calculate Customer Lifetime Value.

    Formula: CLV = (Avg Purchase Value × Purchase Frequency × Lifespan × Margin) / (1 + Discount Rate)

    Args:
        avg_purchase_value: Average value per purchase
        purchases_per_year: Annual purchase frequency
        customer_lifespan_years: Expected customer lifespan
        gross_margin_pct: Gross margin percentage
        discount_rate: Discount rate for NPV calculation
        customer_acquisition_cost: Optional CAC for LTV:CAC ratio

    Returns:
        CLV metrics

    Benchmark: LTV:CAC ratio should be >= 3:1
    """
    annual_value = avg_purchase_value * purchases_per_year
    lifetime_value = annual_value * customer_lifespan_years * (gross_margin_pct / Decimal('100'))

    # Apply discount rate
    clv = lifetime_value / (Decimal('1') + discount_rate)

    # Calculate LTV:CAC ratio if CAC provided
    ltv_cac = clv / customer_acquisition_cost if customer_acquisition_cost else Decimal('0')

    return CustomerLifetimeValue(
        avg_purchase_value=avg_purchase_value,
        purchase_frequency=purchases_per_year,
        customer_lifespan_years=customer_lifespan_years,
        clv=clv.quantize(Decimal('0.01')),
        customer_acquisition_cost=customer_acquisition_cost or Decimal('0'),
        ltv_to_cac_ratio=ltv_cac.quantize(Decimal('0.01')),
    )
```

### Cohort Analysis

```python
def cohort_revenue_analysis(
    transactions: pd.DataFrame,
    cohort_column: str = 'signup_month',
    revenue_column: str = 'revenue',
) -> pd.DataFrame:
    """
    Analyze revenue by customer cohort.

    Args:
        transactions: DataFrame with customer transactions
        cohort_column: Column identifying customer cohort (e.g., signup month)
        revenue_column: Revenue column

    Returns:
        DataFrame with cohort revenue analysis
    """
    cohort_summary = transactions.groupby(cohort_column).agg({
        revenue_column: ['sum', 'mean', 'count'],
        'customer_id': 'nunique'
    })

    cohort_summary.columns = [
        'total_revenue',
        'avg_revenue_per_transaction',
        'transaction_count',
        'unique_customers'
    ]

    cohort_summary['avg_revenue_per_customer'] = (
        cohort_summary['total_revenue'] / cohort_summary['unique_customers']
    )

    return cohort_summary
```

## Churn Analysis

### Customer Churn Rate

```python
@dataclass
class ChurnMetrics:
    """Customer churn metrics."""

    beginning_customers: int
    churned_customers: int
    ending_customers: int
    new_customers: int
    churn_rate: Decimal
    retention_rate: Decimal
    net_retention_rate: Decimal

def calculate_churn(
    beginning_customers: int,
    ending_customers: int,
    new_customers: int,
) -> ChurnMetrics:
    """
    Calculate customer churn and retention metrics.

    Formulas:
    - Churn Rate = Churned Customers / Beginning Customers
    - Retention Rate = (Ending - New) / Beginning
    - Net Retention Rate = Ending / Beginning (includes new customers)

    Args:
        beginning_customers: Customers at period start
        ending_customers: Customers at period end
        new_customers: New customers acquired in period

    Returns:
        Churn metrics

    Benchmarks:
    - SaaS B2B: 5-7% annual churn (excellent), 10-15% (average)
    - SaaS B2C: 5-10% monthly churn (varies widely)
    """
    churned_customers = beginning_customers + new_customers - ending_customers

    churn_rate = (
        Decimal(str(churned_customers)) / Decimal(str(beginning_customers)) * 100
        if beginning_customers > 0
        else Decimal('0')
    )

    retention_rate = (
        (Decimal(str(ending_customers - new_customers)) / Decimal(str(beginning_customers))) * 100
        if beginning_customers > 0
        else Decimal('0')
    )

    net_retention_rate = (
        Decimal(str(ending_customers)) / Decimal(str(beginning_customers)) * 100
        if beginning_customers > 0
        else Decimal('0')
    )

    return ChurnMetrics(
        beginning_customers=beginning_customers,
        churned_customers=churned_customers,
        ending_customers=ending_customers,
        new_customers=new_customers,
        churn_rate=churn_rate.quantize(Decimal('0.01')),
        retention_rate=retention_rate.quantize(Decimal('0.01')),
        net_retention_rate=net_retention_rate.quantize(Decimal('0.01')),
    )
```

### Revenue Churn (MRR/ARR)

```python
@dataclass
class RevenueChurnMetrics:
    """Monthly/Annual Recurring Revenue churn."""

    beginning_mrr: Decimal
    churned_mrr: Decimal
    expansion_mrr: Decimal
    new_mrr: Decimal
    ending_mrr: Decimal
    gross_churn_rate: Decimal
    net_churn_rate: Decimal
    revenue_retention_rate: Decimal

def calculate_revenue_churn(
    beginning_mrr: Decimal,
    churned_mrr: Decimal,
    expansion_mrr: Decimal,
    new_mrr: Decimal,
) -> RevenueChurnMetrics:
    """
    Calculate revenue churn metrics for subscription businesses.

    Metrics:
    - Gross Churn Rate = Churned MRR / Beginning MRR
    - Net Churn Rate = (Churned MRR - Expansion MRR) / Beginning MRR
    - Revenue Retention = (Beginning MRR - Churned MRR + Expansion MRR) / Beginning MRR

    Best Practice: Negative net churn (expansion > churn) indicates healthy growth
    """
    ending_mrr = beginning_mrr - churned_mrr + expansion_mrr + new_mrr

    gross_churn_rate = (churned_mrr / beginning_mrr * 100) if beginning_mrr > 0 else Decimal('0')

    net_churn = churned_mrr - expansion_mrr
    net_churn_rate = (net_churn / beginning_mrr * 100) if beginning_mrr > 0 else Decimal('0')

    revenue_retention = (
        (beginning_mrr - churned_mrr + expansion_mrr) / beginning_mrr * 100
        if beginning_mrr > 0
        else Decimal('0')
    )

    return RevenueChurnMetrics(
        beginning_mrr=beginning_mrr,
        churned_mrr=churned_mrr,
        expansion_mrr=expansion_mrr,
        new_mrr=new_mrr,
        ending_mrr=ending_mrr,
        gross_churn_rate=gross_churn_rate.quantize(Decimal('0.01')),
        net_churn_rate=net_churn_rate.quantize(Decimal('0.01')),
        revenue_retention_rate=revenue_retention.quantize(Decimal('0.01')),
    )
```

## Product Mix Analysis

### Revenue by Product Category

```python
@dataclass
class ProductMixMetrics:
    """Product mix revenue analysis."""

    product_category: str
    revenue: Decimal
    revenue_pct: Decimal
    units_sold: int
    avg_price: Decimal

def analyze_product_mix(
    sales_data: pd.DataFrame,
    category_column: str = 'product_category',
    revenue_column: str = 'revenue',
    units_column: str = 'units',
) -> list[ProductMixMetrics]:
    """
    Analyze revenue mix by product category.

    Args:
        sales_data: DataFrame with sales data
        category_column: Product category column
        revenue_column: Revenue column
        units_column: Units sold column

    Returns:
        List of product mix metrics sorted by revenue
    """
    total_revenue = sales_data[revenue_column].sum()

    product_summary = sales_data.groupby(category_column).agg({
        revenue_column: 'sum',
        units_column: 'sum'
    }).reset_index()

    product_summary.columns = ['category', 'revenue', 'units']

    metrics: list[ProductMixMetrics] = []

    for _, row in product_summary.iterrows():
        revenue = Decimal(str(row['revenue']))
        units = int(row['units'])

        metrics.append(
            ProductMixMetrics(
                product_category=row['category'],
                revenue=revenue,
                revenue_pct=(revenue / Decimal(str(total_revenue)) * 100).quantize(Decimal('0.01')),
                units_sold=units,
                avg_price=(revenue / Decimal(str(units))).quantize(Decimal('0.01')) if units > 0 else Decimal('0'),
            )
        )

    # Sort by revenue descending
    metrics.sort(key=lambda x: x.revenue, reverse=True)

    return metrics
```

## SaaS Metrics

### ARR/MRR Calculation

```python
@dataclass
class ARRMetrics:
    """Annual Recurring Revenue metrics."""

    mrr: Decimal
    arr: Decimal
    new_arr: Decimal
    expansion_arr: Decimal
    churned_arr: Decimal
    net_new_arr: Decimal

def calculate_arr_metrics(
    monthly_recurring_revenue: Decimal,
    new_monthly_revenue: Decimal,
    expansion_monthly_revenue: Decimal,
    churned_monthly_revenue: Decimal,
) -> ARRMetrics:
    """
    Calculate SaaS ARR/MRR metrics.

    Formulas:
    - ARR = MRR × 12
    - Net New ARR = (New + Expansion - Churn) × 12
    """
    arr = monthly_recurring_revenue * Decimal('12')
    new_arr = new_monthly_revenue * Decimal('12')
    expansion_arr = expansion_monthly_revenue * Decimal('12')
    churned_arr = churned_monthly_revenue * Decimal('12')
    net_new_arr = new_arr + expansion_arr - churned_arr

    return ARRMetrics(
        mrr=monthly_recurring_revenue,
        arr=arr,
        new_arr=new_arr,
        expansion_arr=expansion_arr,
        churned_arr=churned_arr,
        net_new_arr=net_new_arr,
    )
```

### Customer Acquisition Cost (CAC)

```python
@dataclass
class CACMetrics:
    """Customer acquisition cost metrics."""

    total_sales_marketing_expense: Decimal
    new_customers_acquired: int
    cac: Decimal
    payback_period_months: Decimal | None

def calculate_cac(
    sales_expense: Decimal,
    marketing_expense: Decimal,
    new_customers: int,
    avg_monthly_revenue_per_customer: Decimal | None = None,
    gross_margin_pct: Decimal | None = None,
) -> CACMetrics:
    """
    Calculate Customer Acquisition Cost.

    Formula: CAC = (Sales Expense + Marketing Expense) / New Customers

    Optional: Calculate payback period if revenue and margin provided

    Benchmarks:
    - SaaS: CAC payback should be < 12 months
    - LTV:CAC ratio should be >= 3:1
    """
    total_expense = sales_expense + marketing_expense
    cac = total_expense / Decimal(str(new_customers)) if new_customers > 0 else Decimal('0')

    payback_period = None
    if avg_monthly_revenue_per_customer and gross_margin_pct:
        monthly_gross_profit = avg_monthly_revenue_per_customer * (gross_margin_pct / Decimal('100'))
        payback_period = (cac / monthly_gross_profit).quantize(Decimal('0.01')) if monthly_gross_profit > 0 else None

    return CACMetrics(
        total_sales_marketing_expense=total_expense,
        new_customers_acquired=new_customers,
        cac=cac.quantize(Decimal('0.01')),
        payback_period_months=payback_period,
    )
```

## Best Practices

### Data Validation

```python
def validate_revenue_data(revenue: Decimal, period: str) -> None:
    """
    Validate revenue data before analysis.

    Raises:
        ValueError: If data fails validation
    """
    if revenue < 0:
        raise ValueError(f"Revenue cannot be negative for period {period}: {revenue}")

    if revenue == Decimal('0'):
        # Warning, not error - legitimate zero revenue periods exist
        import warnings
        warnings.warn(f"Zero revenue recorded for period {period}")
```

### Use Decimal for Currency

```python
# CORRECT: Use Decimal for all revenue calculations
clv = Decimal('1000.00') * Decimal('12') * Decimal('3')
# Result: Decimal('36000.00')

# INCORRECT: Float introduces precision errors
clv = 1000.00 * 12 * 3
# May have precision issues
```

### Trend Smoothing

Use moving averages to smooth seasonal fluctuations:

```python
def smooth_revenue_trends(
    revenue_data: pd.Series,
    window: int = 3,
) -> pd.Series:
    """Smooth revenue trends with moving average."""
    return revenue_data.rolling(window=window, center=True).mean()
```

## Integration with ERP Systems

See [../integrations/netsuite.md](../integrations/netsuite.md) for extracting revenue and customer data from NetSuite for revenue analytics.
