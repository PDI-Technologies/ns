---
name: financial-analytics
description: Comprehensive financial data analysis including vendor spend, revenue analysis, cost forecasting, budget variance, working capital metrics, and financial KPI calculations. Use for building financial dashboards, analyzing P&L data, cash flow analysis, financial forecasting, ratio analysis, or any finance/accounting analytics. Covers time series analysis, variance analysis, financial modeling, and enterprise financial reporting.
---

# Financial Analytics

Comprehensive financial data analysis and reporting for enterprise applications.

## Contents

- [When to Use This Skill](#when-to-use-this-skill)
- [Quick Start](#quick-start)
- [Core Analytics Domains](#core-analytics-domains)
  - [Vendor & Cost Analytics](#vendor--cost-analytics) - [reference/vendor-analytics.md](reference/vendor-analytics.md)
  - [Revenue Analytics](#revenue-analytics) - [reference/revenue-analytics.md](reference/revenue-analytics.md)
  - [Budget & Planning](#budget--planning) - [reference/budget-variance.md](reference/budget-variance.md)
  - [Cash Flow Analysis](#cash-flow-analysis) - [reference/cash-flow.md](reference/cash-flow.md)
  - [Financial Ratios](#financial-ratios) - [reference/financial-ratios.md](reference/financial-ratios.md)
- [Time Series Analysis](#time-series-analysis)
- [Forecasting Methods](#forecasting-methods) - [reference/forecasting.md](reference/forecasting.md)
- [Financial Metrics & KPIs](#financial-metrics--kpis)
- [Variance Analysis](#variance-analysis)
- [Data Aggregation Patterns](#data-aggregation-patterns)
- [Dashboard Design Patterns](#dashboard-design-patterns)
- [Integration with ERP Systems](#integration-with-erp-systems)
  - [NetSuite](#netsuite) - [integrations/netsuite.md](integrations/netsuite.md)
  - [Salesforce](#salesforce) - [integrations/salesforce.md](integrations/salesforce.md)
  - [Database Queries](#database-queries) - [integrations/databases.md](integrations/databases.md)
- [Visualization Libraries](#visualization-libraries)
- [Complete Examples](#complete-examples)
  - [Cost Analysis CLI](#cost-analysis-cli) - [examples/cost-analysis-cli.md](examples/cost-analysis-cli.md)
  - [Financial Dashboard](#financial-dashboard-application) - [examples/financial-dashboard.md](examples/financial-dashboard.md)
- [Best Practices](#best-practices)
- [Financial Reporting Standards](#financial-reporting-standards)
- [Advanced Topics](#advanced-topics)
  - [Scenario Analysis](#scenario-analysis) - [reference/scenario-analysis.md](reference/scenario-analysis.md)
  - [Anomaly Detection](#anomaly-detection) - [reference/anomaly-detection.md](reference/anomaly-detection.md)

## When to Use This Skill

Use this skill for:
- **Vendor/Cost Analysis**: Spend analysis, vendor consolidation, cost optimization
- **Revenue Analysis**: Sales trends, revenue recognition, forecasting
- **Budget & Variance**: Budget vs actual, variance analysis, reforecasting
- **Cash Flow**: Working capital, DSO/DPO/DIO, cash conversion cycle
- **Financial Modeling**: Forecasting, scenario analysis, sensitivity analysis
- **KPI Dashboards**: Financial metrics, executive reporting, operational metrics
- **P&L Analysis**: Revenue, COGS, operating expenses, margin analysis

## Quick Start

### Revenue Trend Analysis
```python
import pandas as pd

def analyze_revenue_trends(transactions: pd.DataFrame, period: str = 'M') -> pd.DataFrame:
    """Calculate revenue trends by period."""
    transactions['date'] = pd.to_datetime(transactions['transaction_date'])

    trends = transactions.groupby(pd.Grouper(key='date', freq=period)).agg({
        'revenue': 'sum',
        'transaction_id': 'count'
    }).rename(columns={'transaction_id': 'transaction_count'})

    # Calculate growth rates
    trends['revenue_growth'] = trends['revenue'].pct_change()
    trends['avg_transaction_value'] = trends['revenue'] / trends['transaction_count']

    return trends
```

### Budget Variance Analysis
```python
def calculate_variance(actual: float, budget: float) -> dict:
    """Calculate variance metrics."""
    variance = actual - budget
    variance_pct = (variance / budget * 100) if budget != 0 else 0

    return {
        'actual': actual,
        'budget': budget,
        'variance': variance,
        'variance_pct': variance_pct,
        'status': 'favorable' if variance > 0 else 'unfavorable'
    }
```

## Core Analytics Domains

### Vendor & Cost Analytics
→ **See**: [reference/vendor-analytics.md](reference/vendor-analytics.md)

Topics:
- Vendor spend analysis (Pareto, segmentation)
- Duplicate vendor detection
- Cost optimization strategies
- Payment terms analysis
- Maverick spend detection

**Note**: For deep vendor analytics, use the `vendor-cost-analytics` skill (specialized)

### Revenue Analytics
→ **See**: [reference/revenue-analytics.md](reference/revenue-analytics.md)

Topics:
- Revenue recognition patterns
- Sales trend analysis
- Customer lifetime value (CLV)
- Churn analysis
- Revenue forecasting
- Product mix analysis

### Budget & Planning
→ **See**: [reference/budget-variance.md](reference/budget-variance.md)

Topics:
- Budget vs actual variance
- Flexible budgeting
- Rolling forecasts
- Scenario planning
- Reforecasting methodologies

### Cash Flow Analysis
→ **See**: [reference/cash-flow.md](reference/cash-flow.md)

Metrics:
- Days Sales Outstanding (DSO)
- Days Payable Outstanding (DPO)
- Days Inventory Outstanding (DIO)
- Cash Conversion Cycle (CCC)
- Working capital trends
- Free cash flow

### Financial Ratios
→ **See**: [reference/financial-ratios.md](reference/financial-ratios.md)

Categories:
- Liquidity ratios (current, quick, cash)
- Profitability ratios (gross margin, operating margin, ROA, ROE)
- Efficiency ratios (asset turnover, inventory turnover)
- Leverage ratios (debt-to-equity, interest coverage)

## Time Series Analysis

### Moving Averages
```python
def calculate_moving_averages(data: pd.Series, windows: list[int]) -> pd.DataFrame:
    """Calculate multiple moving averages."""
    result = pd.DataFrame({'actual': data})

    for window in windows:
        result[f'MA{window}'] = data.rolling(window=window).mean()

    return result
```

### Exponential Smoothing
```python
def exponential_smoothing(data: pd.Series, alpha: float = 0.3) -> pd.Series:
    """Apply exponential smoothing for forecasting."""
    result = [data.iloc[0]]  # Start with first value

    for i in range(1, len(data)):
        smoothed = alpha * data.iloc[i] + (1 - alpha) * result[-1]
        result.append(smoothed)

    return pd.Series(result, index=data.index)
```

### Seasonality Detection
```python
from statsmodels.tsa.seasonal import seasonal_decompose

def analyze_seasonality(data: pd.Series, period: int = 12):
    """Decompose time series into trend, seasonal, residual."""
    decomposition = seasonal_decompose(data, model='additive', period=period)

    return {
        'trend': decomposition.trend,
        'seasonal': decomposition.seasonal,
        'residual': decomposition.resid,
        'original': data
    }
```

## Forecasting Methods

→ **See**: [reference/forecasting.md](reference/forecasting.md)

Methods covered:
- Simple moving average
- Exponential smoothing (simple, double, triple)
- Linear regression
- ARIMA models
- Prophet (Facebook's forecasting library)
- Ensemble methods

## Financial Metrics & KPIs

### Profitability Metrics
- **Gross Margin**: (Revenue - COGS) / Revenue
- **Operating Margin**: Operating Income / Revenue
- **Net Margin**: Net Income / Revenue
- **EBITDA**: Earnings before interest, taxes, depreciation, amortization
- **ROA**: Net Income / Total Assets
- **ROE**: Net Income / Shareholder Equity

### Growth Metrics
- **Revenue Growth**: (Current - Prior) / Prior
- **YoY Growth**: Year-over-year change
- **CAGR**: Compound annual growth rate
- **Quarter-over-Quarter**: QoQ growth rate

### Efficiency Metrics
- **Asset Turnover**: Revenue / Average Total Assets
- **Inventory Turnover**: COGS / Average Inventory
- **Receivables Turnover**: Revenue / Average AR
- **Payables Turnover**: COGS / Average AP

### Implementation
```python
def calculate_financial_ratios(financials: dict) -> dict:
    """Calculate standard financial ratios."""
    return {
        'gross_margin': (financials['revenue'] - financials['cogs']) / financials['revenue'],
        'operating_margin': financials['operating_income'] / financials['revenue'],
        'net_margin': financials['net_income'] / financials['revenue'],
        'roa': financials['net_income'] / financials['total_assets'],
        'roe': financials['net_income'] / financials['equity'],
        'current_ratio': financials['current_assets'] / financials['current_liabilities'],
        'quick_ratio': (financials['current_assets'] - financials['inventory']) / financials['current_liabilities'],
        'debt_to_equity': financials['total_debt'] / financials['equity'],
    }
```

## Variance Analysis

### Types of Variance

1. **Price Variance**: (Actual Price - Standard Price) × Actual Quantity
2. **Volume Variance**: (Actual Quantity - Budgeted Quantity) × Standard Price
3. **Mix Variance**: Impact of product/customer mix changes

### Implementation
```python
@dataclass
class VarianceAnalysis:
    actual: float
    budget: float
    variance: float
    variance_pct: float
    threshold_breach: bool
    explanation: str

def analyze_variance(
    actual: float,
    budget: float,
    threshold_pct: float = 5.0,
    favorable_direction: str = 'positive'  # or 'negative'
) -> VarianceAnalysis:
    """Comprehensive variance analysis."""
    variance = actual - budget
    variance_pct = (variance / budget * 100) if budget != 0 else 0

    threshold_breach = abs(variance_pct) > threshold_pct

    # Determine if favorable
    is_favorable = (
        (variance > 0 and favorable_direction == 'positive') or
        (variance < 0 and favorable_direction == 'negative')
    )

    explanation = f"{'Favorable' if is_favorable else 'Unfavorable'} variance of {variance_pct:.1f}%"

    return VarianceAnalysis(
        actual=actual,
        budget=budget,
        variance=variance,
        variance_pct=variance_pct,
        threshold_breach=threshold_breach,
        explanation=explanation
    )
```

## Data Aggregation Patterns

### Dimensional Rollups
```python
def rollup_financials(
    data: pd.DataFrame,
    dimensions: list[str],
    metrics: list[str]
) -> pd.DataFrame:
    """Aggregate financial data by dimensions."""
    return data.groupby(dimensions)[metrics].sum()

# Example: Revenue by product and region
revenue_by_product_region = rollup_financials(
    sales_data,
    dimensions=['product', 'region'],
    metrics=['revenue', 'quantity']
)
```

### Period Comparisons
```python
def period_over_period(
    data: pd.DataFrame,
    date_column: str,
    metric: str,
    current_period: str,
    prior_period: str
) -> dict:
    """Compare two periods."""
    current = data[data[date_column].between(*current_period)][metric].sum()
    prior = data[data[date_column].between(*prior_period)][metric].sum()

    return {
        'current': current,
        'prior': prior,
        'change': current - prior,
        'change_pct': ((current - prior) / prior * 100) if prior != 0 else 0
    }
```

## Dashboard Design Patterns

### Executive Financial Dashboard

**Key Components**:
1. **Headline Metrics** (cards)
   - Revenue (current period)
   - Revenue growth %
   - Gross margin %
   - Operating margin %

2. **Trend Charts**
   - Revenue trend (12 months)
   - Expense trend by category
   - Margin trend

3. **Variance Tables**
   - Budget vs actual by department
   - Top variances (red/green highlighting)

4. **Actionable Insights**
   - Variance explanations
   - Recommendations
   - Alerts for threshold breaches

### Operational Finance Dashboard

**Components**:
1. **Working Capital**
   - DSO trend
   - DPO trend
   - Inventory days
   - Cash conversion cycle

2. **AP/AR Aging**
   - Aging buckets (0-30, 31-60, 61-90, 90+)
   - Overdue amounts
   - Collection priorities

3. **Cost Analysis**
   - Top expense categories
   - Cost per unit trends
   - Budget variance by GL account

## Integration with ERP Systems

### NetSuite
→ **See**: [integrations/netsuite.md](integrations/netsuite.md)

Extract financial data:
- General Ledger transactions
- Vendor bills and payments
- Customer invoices and payments
- Budget vs actuals reports

### Salesforce
→ **See**: [integrations/salesforce.md](integrations/salesforce.md)

Revenue data:
- Opportunity pipeline
- Closed won revenue
- Product revenue breakdown
- Sales forecasts

### Database Queries
→ **See**: [integrations/databases.md](integrations/databases.md)

Common patterns:
- Extract from data warehouse
- Join financial and operational data
- Aggregate for reporting
- Handle multi-currency

## Visualization Libraries

### Python
- **matplotlib/seaborn**: Static charts, reports
- **plotly**: Interactive dashboards
- **pandas plotting**: Quick exploratory visualizations

### React/JavaScript
- **recharts**: React charts library
- **shadcn/ui charts**: Chart components with shadcn
- **nivo**: Rich interactive charts
- **d3.js**: Custom visualizations

## Complete Examples

### Financial Dashboard Application
→ **See**: [examples/financial-dashboard.md](examples/financial-dashboard.md)

Full implementation:
- React PWA with shadcn/ui
- Financial metrics API
- Real-time data sync
- Interactive charts

### Cost Analysis CLI
→ **See**: [examples/cost-analysis-cli.md](examples/cost-analysis-cli.md)

Complete CLI application:
- Data extraction
- Analysis pipeline
- Report generation
- Excel export

## Best Practices

### Data Validation
- Verify date ranges are valid
- Check for negative values where inappropriate
- Validate currency consistency
- Ensure no division by zero
- Confirm period alignment (apples to apples)

### Performance
- Use database aggregation (don't pull all rows)
- Cache calculated metrics
- Index date columns
- Partition large tables by period

### Accuracy
- Use decimal types for financial calculations (avoid float)
- Round consistently (2 decimals for currency)
- Document assumptions
- Validate totals and subtotals match
- Audit trail for calculations

### Fail-Fast Financial Applications
- No default values for critical metrics
- Fail if required data missing
- Validate data types strictly
- Log all calculations for audit
- No silent error swallowing

## Financial Reporting Standards

### Period Closing
- Month-end close processes
- Accruals and deferrals
- Reconciliations
- Financial statement preparation

### Compliance
- GAAP principles
- IFRS standards
- SOX compliance (audit trails)
- Multi-currency reporting

## Advanced Topics

### Scenario Analysis
→ **See**: [reference/scenario-analysis.md](reference/scenario-analysis.md)

Model multiple futures:
- Best case / worst case / expected
- Sensitivity analysis
- Monte Carlo simulation

### Anomaly Detection
→ **See**: [reference/anomaly-detection.md](reference/anomaly-detection.md)

Identify unusual patterns:
- Statistical outliers (Z-score, IQR)
- Benford's Law (fraud detection)
- Control charts
- Threshold alerts

---

*Use this skill for comprehensive financial analysis, reporting, and dashboard development across all financial domains.*
