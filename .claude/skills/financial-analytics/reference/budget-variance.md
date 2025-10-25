# Budget Variance Analysis

Comprehensive budget vs actual variance analysis, flexible budgeting, rolling forecasts, and reforecasting methodologies for FP&A teams.

## Contents

- [Overview](#overview)
- [Core Variance Metrics](#core-variance-metrics)
  - [Basic Variance Calculation](#basic-variance-calculation)
  - [Revenue Variance](#revenue-variance)
  - [Expense Variance](#expense-variance)
- [Multi-Dimensional Variance Analysis](#multi-dimensional-variance-analysis)
  - [Department Budget Variance](#department-budget-variance)
- [Price and Volume Variance](#price-and-volume-variance)
- [Flexible Budgeting](#flexible-budgeting)
- [Rolling Forecasts](#rolling-forecasts)
- [Reforecasting Methodology](#reforecasting-methodology)
- [Variance Reporting](#variance-reporting)
- [Trend Analysis](#trend-analysis)
- [Best Practices](#best-practices)

## Overview

Budget variance analysis compares actual financial results to budgeted expectations, identifying performance gaps and enabling corrective action. This guide covers industry-standard variance analysis techniques with production-ready implementations.

## Core Variance Metrics

### Basic Variance Calculation

```python
from dataclasses import dataclass
from decimal import Decimal

@dataclass
class VarianceMetrics:
    """Budget variance metrics."""

    actual: Decimal
    budget: Decimal
    variance: Decimal
    variance_pct: Decimal
    is_favorable: bool
    threshold_breach: bool
    explanation: str

def calculate_variance(
    actual: Decimal,
    budget: Decimal,
    threshold_pct: Decimal = Decimal('5.0'),
    favorable_direction: str = 'positive',  # or 'negative'
) -> VarianceMetrics:
    """
    Calculate budget variance with threshold checking.

    Args:
        actual: Actual amount
        budget: Budgeted amount
        threshold_pct: Variance threshold for investigation (default 5%)
        favorable_direction: 'positive' for revenue, 'negative' for costs

    Returns:
        Variance metrics with favorable/unfavorable classification

    Best Practice: Fail-fast on invalid inputs
    """
    if budget == Decimal('0'):
        raise ValueError("Budget cannot be zero for variance calculation")

    variance = actual - budget
    variance_pct = (variance / budget) * Decimal('100')

    # Determine if favorable based on direction
    if favorable_direction == 'positive':
        # For revenue: higher is better
        is_favorable = variance > 0
    else:
        # For costs: lower is better
        is_favorable = variance < 0

    # Check if variance exceeds investigation threshold
    threshold_breach = abs(variance_pct) > threshold_pct

    # Generate explanation
    direction = "over" if variance > 0 else "under"
    favorable_text = "Favorable" if is_favorable else "Unfavorable"
    explanation = f"{favorable_text} variance of {abs(variance_pct):.1f}% ({direction} budget by ${abs(variance):,.2f})"

    return VarianceMetrics(
        actual=actual,
        budget=budget,
        variance=variance,
        variance_pct=variance_pct.quantize(Decimal('0.01')),
        is_favorable=is_favorable,
        threshold_breach=threshold_breach,
        explanation=explanation,
    )
```

### Revenue Variance

```python
def analyze_revenue_variance(
    actual_revenue: Decimal,
    budgeted_revenue: Decimal,
    threshold: Decimal = Decimal('5.0'),
) -> VarianceMetrics:
    """
    Analyze revenue variance (positive variance is favorable).

    Example:
        Actual: $105,000, Budget: $100,000
        Variance: +$5,000 (+5.0%) - Favorable
    """
    return calculate_variance(
        actual=actual_revenue,
        budget=budgeted_revenue,
        threshold_pct=threshold,
        favorable_direction='positive',
    )
```

### Expense Variance

```python
def analyze_expense_variance(
    actual_expense: Decimal,
    budgeted_expense: Decimal,
    threshold: Decimal = Decimal('5.0'),
) -> VarianceMetrics:
    """
    Analyze expense variance (negative variance is favorable).

    Example:
        Actual: $45,000, Budget: $50,000
        Variance: -$5,000 (-10.0%) - Favorable (under budget)
    """
    return calculate_variance(
        actual=actual_expense,
        budget=budgeted_expense,
        threshold_pct=threshold,
        favorable_direction='negative',
    )
```

## Multi-Dimensional Variance Analysis

### Department Budget Variance

```python
from typing import TypedDict

class DepartmentBudget(TypedDict):
    """Department budget data."""
    department: str
    actual: Decimal
    budget: Decimal

@dataclass
class DepartmentVarianceReport:
    """Department variance report."""

    department: str
    variance_metrics: VarianceMetrics
    rank: int  # Rank by absolute variance

def analyze_department_variances(
    department_budgets: list[DepartmentBudget],
    threshold: Decimal = Decimal('5.0'),
) -> list[DepartmentVarianceReport]:
    """
    Analyze budget variances across all departments.

    Returns departments sorted by absolute variance (largest first)
    for prioritized investigation
    """
    reports: list[DepartmentVarianceReport] = []

    for dept in department_budgets:
        variance = analyze_expense_variance(
            actual_expense=dept['actual'],
            budgeted_expense=dept['budget'],
            threshold=threshold,
        )

        reports.append(
            DepartmentVarianceReport(
                department=dept['department'],
                variance_metrics=variance,
                rank=0,  # Will be set after sorting
            )
        )

    # Sort by absolute variance descending
    reports.sort(key=lambda x: abs(x.variance_metrics.variance), reverse=True)

    # Assign ranks
    for i, report in enumerate(reports, 1):
        report.rank = i

    return reports
```

## Price and Volume Variance

Decompose total variance into price and volume components.

```python
@dataclass
class PriceVolumeVariance:
    """Price and volume variance decomposition."""

    total_variance: Decimal
    price_variance: Decimal
    volume_variance: Decimal
    actual_price: Decimal
    actual_volume: Decimal
    budget_price: Decimal
    budget_volume: Decimal

def calculate_price_volume_variance(
    actual_price: Decimal,
    actual_volume: Decimal,
    budget_price: Decimal,
    budget_volume: Decimal,
) -> PriceVolumeVariance:
    """
    Decompose revenue variance into price and volume components.

    Formulas:
    - Price Variance = (Actual Price - Budget Price) × Actual Volume
    - Volume Variance = (Actual Volume - Budget Volume) × Budget Price
    - Total Variance = Actual Revenue - Budget Revenue

    Args:
        actual_price: Actual price per unit
        actual_volume: Actual units sold
        budget_price: Budgeted price per unit
        budget_volume: Budgeted units

    Returns:
        Price and volume variance breakdown

    Example:
        Actual: 1,100 units @ $105 = $115,500
        Budget: 1,000 units @ $100 = $100,000
        Total Variance: +$15,500

        Price Variance: ($105 - $100) × 1,100 = +$5,500
        Volume Variance: (1,100 - 1,000) × $100 = +$10,000
    """
    actual_revenue = actual_price * actual_volume
    budget_revenue = budget_price * budget_volume
    total_variance = actual_revenue - budget_revenue

    price_variance = (actual_price - budget_price) * actual_volume
    volume_variance = (actual_volume - budget_volume) * budget_price

    return PriceVolumeVariance(
        total_variance=total_variance,
        price_variance=price_variance,
        volume_variance=volume_variance,
        actual_price=actual_price,
        actual_volume=actual_volume,
        budget_price=budget_price,
        budget_volume=budget_volume,
    )
```

## Flexible Budgeting

Flexible budgets adjust for actual activity levels to provide meaningful variance analysis.

```python
@dataclass
class FlexibleBudget:
    """Flexible budget calculation."""

    static_budget: Decimal
    flexible_budget: Decimal
    actual: Decimal
    volume_variance: Decimal  # Static vs Flexible
    spending_variance: Decimal  # Flexible vs Actual

def calculate_flexible_budget(
    actual_volume: Decimal,
    budget_volume: Decimal,
    fixed_costs: Decimal,
    variable_cost_per_unit: Decimal,
    actual_costs: Decimal,
) -> FlexibleBudget:
    """
    Calculate flexible budget adjusting for actual volume.

    Formula: Flexible Budget = Fixed Costs + (Variable Rate × Actual Volume)

    This separates volume variance from spending variance:
    - Volume Variance: Due to different activity level than budgeted
    - Spending Variance: Due to different cost per unit than budgeted

    Args:
        actual_volume: Actual activity level (units, hours, etc.)
        budget_volume: Budgeted activity level
        fixed_costs: Fixed costs (don't change with volume)
        variable_cost_per_unit: Budgeted variable cost per unit
        actual_costs: Actual total costs incurred

    Returns:
        Flexible budget with variance decomposition
    """
    # Static budget (original)
    static_budget = fixed_costs + (variable_cost_per_unit * budget_volume)

    # Flexible budget (adjusted for actual volume)
    flexible_budget = fixed_costs + (variable_cost_per_unit * actual_volume)

    # Volume variance (static vs flexible)
    volume_variance = static_budget - flexible_budget

    # Spending variance (flexible vs actual)
    spending_variance = flexible_budget - actual_costs

    return FlexibleBudget(
        static_budget=static_budget,
        flexible_budget=flexible_budget,
        actual=actual_costs,
        volume_variance=volume_variance,
        spending_variance=spending_variance,
    )
```

## Rolling Forecasts

Rolling forecasts continuously update projections based on actual performance.

```python
import pandas as pd
from datetime import datetime

@dataclass
class RollingForecast:
    """Rolling forecast data."""

    forecast_date: datetime
    period: str
    original_budget: Decimal
    latest_forecast: Decimal
    actuals_ytd: Decimal
    forecast_remaining: Decimal
    variance_to_budget: Decimal

def create_rolling_forecast(
    period_data: pd.DataFrame,
    actuals_column: str = 'actuals',
    budget_column: str = 'budget',
) -> list[RollingForecast]:
    """
    Create rolling forecast updating for actual results.

    Pattern:
    - Q1-Q2: Use actuals
    - Q3-Q4: Use latest forecast
    - Compare full-year forecast to original budget

    Args:
        period_data: DataFrame with periods, actuals, budgets, forecasts
        actuals_column: Column name for actual results
        budget_column: Column name for original budget

    Returns:
        List of rolling forecast periods
    """
    rolling_forecasts: list[RollingForecast] = []

    for _, row in period_data.iterrows():
        period = row['period']
        actual = Decimal(str(row.get(actuals_column, 0)))
        budget = Decimal(str(row[budget_column]))
        forecast = Decimal(str(row.get('forecast', budget)))

        # Use actual if available, otherwise use forecast
        latest_forecast = actual if actual > 0 else forecast

        rolling_forecasts.append(
            RollingForecast(
                forecast_date=datetime.now(),
                period=period,
                original_budget=budget,
                latest_forecast=latest_forecast,
                actuals_ytd=actual,
                forecast_remaining=forecast if actual == 0 else Decimal('0'),
                variance_to_budget=latest_forecast - budget,
            )
        )

    return rolling_forecasts
```

## Reforecasting Methodology

```python
@dataclass
class ReforecastAnalysis:
    """Reforecast analysis."""

    original_budget: Decimal
    reforecast: Decimal
    actuals_ytd: Decimal
    remaining_periods: int
    avg_required_per_period: Decimal
    variance_to_budget: Decimal
    variance_pct: Decimal

def analyze_reforecast(
    original_annual_budget: Decimal,
    actuals_ytd: Decimal,
    periods_complete: int,
    periods_remaining: int,
    reforecast_remaining: Decimal | None = None,
) -> ReforecastAnalysis:
    """
    Analyze reforecast vs original budget.

    If reforecast_remaining not provided, calculate based on YTD run rate.

    Args:
        original_annual_budget: Original full-year budget
        actuals_ytd: Actual results year-to-date
        periods_complete: Number of periods completed
        periods_remaining: Number of periods remaining
        reforecast_remaining: Optional updated forecast for remaining periods

    Returns:
        Reforecast analysis with required run rate
    """
    if reforecast_remaining is None:
        # Use YTD run rate to forecast remaining
        ytd_average = actuals_ytd / Decimal(str(periods_complete)) if periods_complete > 0 else Decimal('0')
        reforecast_remaining = ytd_average * Decimal(str(periods_remaining))

    reforecast = actuals_ytd + reforecast_remaining
    variance_to_budget = reforecast - original_annual_budget
    variance_pct = (variance_to_budget / original_annual_budget * 100) if original_annual_budget > 0 else Decimal('0')

    avg_required = reforecast_remaining / Decimal(str(periods_remaining)) if periods_remaining > 0 else Decimal('0')

    return ReforecastAnalysis(
        original_budget=original_annual_budget,
        reforecast=reforecast,
        actuals_ytd=actuals_ytd,
        remaining_periods=periods_remaining,
        avg_required_per_period=avg_required.quantize(Decimal('0.01')),
        variance_to_budget=variance_to_budget,
        variance_pct=variance_pct.quantize(Decimal('0.01')),
    )
```

## Variance Reporting

### Executive Variance Summary

```python
from rich.console import Console
from rich.table import Table

def generate_variance_report(
    variances: list[DepartmentVarianceReport],
    threshold_only: bool = True,
) -> None:
    """
    Generate formatted variance report using Rich.

    Args:
        variances: List of department variance reports
        threshold_only: Show only variances exceeding threshold
    """
    console = Console()

    # Filter if requested
    if threshold_only:
        variances = [v for v in variances if v.variance_metrics.threshold_breach]

    if not variances:
        console.print("[yellow]No significant variances to report.")
        return

    table = Table(title="Budget Variance Report - Investigation Required")
    table.add_column("Rank", style="cyan", justify="right")
    table.add_column("Department", style="white")
    table.add_column("Budget", style="blue", justify="right")
    table.add_column("Actual", style="blue", justify="right")
    table.add_column("Variance", style="yellow", justify="right")
    table.add_column("Variance %", style="yellow", justify="right")
    table.add_column("Status", style="white")

    for report in variances:
        vm = report.variance_metrics

        # Color code variance
        variance_style = "green" if vm.is_favorable else "red"
        status_icon = "✓" if vm.is_favorable else "✗"

        table.add_row(
            str(report.rank),
            report.department,
            f"${vm.budget:,.2f}",
            f"${vm.actual:,.2f}",
            f"[{variance_style}]${abs(vm.variance):,.2f}[/{variance_style}]",
            f"[{variance_style}]{vm.variance_pct:+.1f}%[/{variance_style}]",
            f"[{variance_style}]{status_icon} {vm.explanation}[/{variance_style}]",
        )

    console.print(table)
```

## Trend Analysis

```python
def analyze_variance_trends(
    historical_data: pd.DataFrame,
) -> pd.DataFrame:
    """
    Analyze variance trends over multiple periods.

    Args:
        historical_data: DataFrame with columns: period, actual, budget

    Returns:
        DataFrame with variance trends
    """
    trends = historical_data.copy()

    trends['variance'] = trends['actual'] - trends['budget']
    trends['variance_pct'] = (trends['variance'] / trends['budget'] * 100)

    # Calculate rolling average variance
    trends['avg_variance_3mo'] = trends['variance'].rolling(window=3).mean()

    # Flag persistently unfavorable variances
    trends['unfavorable'] = trends['variance'] < 0  # For expenses
    trends['persistent_issue'] = (
        trends['unfavorable'].rolling(window=3).sum() == 3
    )

    return trends
```

## Best Practices

### 1. Establish Materiality Thresholds

```python
@dataclass
class VarianceThresholds:
    """Variance investigation thresholds."""

    percentage_threshold: Decimal = Decimal('5.0')  # 5%
    dollar_threshold: Decimal = Decimal('10000')  # $10k

def requires_investigation(
    variance: VarianceMetrics,
    thresholds: VarianceThresholds,
) -> bool:
    """
    Determine if variance requires investigation.

    Variance requires investigation if it exceeds EITHER threshold.
    """
    exceeds_percentage = abs(variance.variance_pct) > thresholds.percentage_threshold
    exceeds_dollar = abs(variance.variance) > thresholds.dollar_threshold

    return exceeds_percentage or exceeds_dollar
```

### 2. Document Variance Explanations

```python
@dataclass
class VarianceExplanation:
    """Documented variance explanation."""

    department: str
    period: str
    variance_amount: Decimal
    variance_pct: Decimal
    explanation: str
    corrective_action: str
    responsible_owner: str
    resolution_date: datetime | None
```

### 3. Use Decimal for Currency

```python
# CORRECT: Use Decimal for all financial variance calculations
variance = Decimal('105000.00') - Decimal('100000.00')
# Result: Decimal('5000.00')

# INCORRECT: Float introduces precision errors
variance = 105000.00 - 100000.00
# May have precision issues in calculations
```

### 4. Automate Variance Alerts

```python
def send_variance_alerts(
    variances: list[DepartmentVarianceReport],
    threshold: Decimal = Decimal('10.0'),
) -> list[str]:
    """
    Generate alerts for significant variances.

    Returns list of alert messages for distribution
    """
    alerts: list[str] = []

    for report in variances:
        vm = report.variance_metrics

        if abs(vm.variance_pct) > threshold:
            alert = (
                f"ALERT: {report.department} variance of {vm.variance_pct:+.1f}% "
                f"(${abs(vm.variance):,.2f}) exceeds {threshold}% threshold. "
                f"Status: {'Favorable' if vm.is_favorable else 'UNFAVORABLE'}. "
                f"Investigation required."
            )
            alerts.append(alert)

    return alerts
```

## Integration with ERP Systems

See [../integrations/netsuite.md](../integrations/netsuite.md) for extracting budget and actual data from NetSuite for variance analysis.
