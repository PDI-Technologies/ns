# Financial Ratios

Comprehensive financial ratio analysis covering liquidity, profitability, efficiency, and leverage metrics for enterprise financial reporting.

## Contents

- [Overview](#overview)
- [Ratio Categories](#ratio-categories)
  - [Liquidity Ratios](#liquidity-ratios)
  - [Profitability Ratios](#profitability-ratios)
  - [Efficiency Ratios](#efficiency-ratios)
  - [Leverage Ratios](#leverage-ratios)
- [DuPont Analysis](#dupont-analysis)
- [Growth Metrics](#growth-metrics)
- [Comprehensive Ratio Analysis](#comprehensive-ratio-analysis)
- [Ratio Trend Analysis](#ratio-trend-analysis)
- [Best Practices](#best-practices)
  - [Data Validation](#data-validation)
  - [Use Decimal Types](#use-decimal-types)
  - [Average Balance Sheet Items](#average-balance-sheet-items)

## Overview

Financial ratios transform raw financial statement data into actionable metrics that reveal company performance, financial health, and operational efficiency. This guide covers industry-standard ratio calculations with production-ready Python implementations.

## Ratio Categories

### Liquidity Ratios

Liquidity ratios measure a company's ability to meet short-term obligations using current assets.

```python
from dataclasses import dataclass
from decimal import Decimal

@dataclass
class LiquidityRatios:
    """Liquidity ratio metrics."""

    current_ratio: Decimal
    quick_ratio: Decimal
    cash_ratio: Decimal
    working_capital: Decimal

def calculate_liquidity_ratios(
    current_assets: Decimal,
    current_liabilities: Decimal,
    inventory: Decimal,
    prepaid_expenses: Decimal,
    cash: Decimal,
    marketable_securities: Decimal,
) -> LiquidityRatios:
    """
    Calculate liquidity ratios.

    Formulas:
    - Current Ratio = Current Assets / Current Liabilities
    - Quick Ratio = (Current Assets - Inventory - Prepaid) / Current Liabilities
    - Cash Ratio = (Cash + Marketable Securities) / Current Liabilities
    - Working Capital = Current Assets - Current Liabilities

    Benchmarks:
    - Current Ratio: >= 1.0x (adequate), >= 2.0x (strong)
    - Quick Ratio: >= 1.0x (adequate), >= 1.5x (strong)
    - Cash Ratio: >= 0.5x (adequate), >= 1.0x (strong)
    """
    if current_liabilities == Decimal('0'):
        raise ValueError("Current liabilities cannot be zero")

    current_ratio = current_assets / current_liabilities

    quick_assets = current_assets - inventory - prepaid_expenses
    quick_ratio = quick_assets / current_liabilities

    cash_ratio = (cash + marketable_securities) / current_liabilities

    working_capital = current_assets - current_liabilities

    return LiquidityRatios(
        current_ratio=current_ratio.quantize(Decimal('0.01')),
        quick_ratio=quick_ratio.quantize(Decimal('0.01')),
        cash_ratio=cash_ratio.quantize(Decimal('0.01')),
        working_capital=working_capital,
    )
```

### Profitability Ratios

Profitability ratios measure how efficiently a company generates profit from its operations.

```python
@dataclass
class ProfitabilityRatios:
    """Profitability ratio metrics."""

    gross_margin: Decimal
    operating_margin: Decimal
    net_margin: Decimal
    ebitda_margin: Decimal
    roa: Decimal
    roe: Decimal
    roic: Decimal

def calculate_profitability_ratios(
    revenue: Decimal,
    cogs: Decimal,
    operating_income: Decimal,
    net_income: Decimal,
    interest: Decimal,
    tax: Decimal,
    depreciation: Decimal,
    amortization: Decimal,
    total_assets: Decimal,
    total_equity: Decimal,
    invested_capital: Decimal,
) -> ProfitabilityRatios:
    """
    Calculate profitability ratios.

    Formulas:
    - Gross Margin = (Revenue - COGS) / Revenue
    - Operating Margin = Operating Income / Revenue
    - Net Margin = Net Income / Revenue
    - EBITDA Margin = (Net Income + Interest + Tax + Depr + Amort) / Revenue
    - ROA = Net Income / Total Assets
    - ROE = Net Income / Total Equity
    - ROIC = Net Operating Profit After Tax / Invested Capital

    Benchmarks (industry-dependent):
    - Gross Margin: 20-40% (manufacturing), 50-80% (software)
    - Operating Margin: 10-20% (good), > 20% (excellent)
    - Net Margin: 5-10% (adequate), > 15% (strong)
    - ROA: > 5% (adequate), > 10% (strong)
    - ROE: > 10% (adequate), > 15% (strong)
    """
    if revenue == Decimal('0'):
        raise ValueError("Revenue cannot be zero for margin calculations")
    if total_assets == Decimal('0'):
        raise ValueError("Total assets cannot be zero for ROA")
    if total_equity == Decimal('0'):
        raise ValueError("Total equity cannot be zero for ROE")

    gross_margin = ((revenue - cogs) / revenue) * 100
    operating_margin = (operating_income / revenue) * 100
    net_margin = (net_income / revenue) * 100

    ebitda = net_income + interest + tax + depreciation + amortization
    ebitda_margin = (ebitda / revenue) * 100

    roa = (net_income / total_assets) * 100
    roe = (net_income / total_equity) * 100

    # ROIC = NOPAT / Invested Capital
    nopat = operating_income * (Decimal('1') - (tax / (net_income + tax)))
    roic = (nopat / invested_capital) * 100 if invested_capital > 0 else Decimal('0')

    return ProfitabilityRatios(
        gross_margin=gross_margin.quantize(Decimal('0.01')),
        operating_margin=operating_margin.quantize(Decimal('0.01')),
        net_margin=net_margin.quantize(Decimal('0.01')),
        ebitda_margin=ebitda_margin.quantize(Decimal('0.01')),
        roa=roa.quantize(Decimal('0.01')),
        roe=roe.quantize(Decimal('0.01')),
        roic=roic.quantize(Decimal('0.01')),
    )
```

### Efficiency Ratios

Efficiency ratios measure how effectively a company uses its assets and manages operations.

```python
@dataclass
class EfficiencyRatios:
    """Efficiency ratio metrics."""

    asset_turnover: Decimal
    inventory_turnover: Decimal
    receivables_turnover: Decimal
    payables_turnover: Decimal
    days_inventory: Decimal
    days_receivables: Decimal
    days_payables: Decimal

def calculate_efficiency_ratios(
    revenue: Decimal,
    cogs: Decimal,
    total_assets: Decimal,
    avg_inventory: Decimal,
    avg_receivables: Decimal,
    avg_payables: Decimal,
) -> EfficiencyRatios:
    """
    Calculate efficiency ratios.

    Formulas:
    - Asset Turnover = Revenue / Average Total Assets
    - Inventory Turnover = COGS / Average Inventory
    - Receivables Turnover = Revenue / Average Receivables
    - Payables Turnover = COGS / Average Payables
    - Days Inventory = 365 / Inventory Turnover
    - Days Receivables = 365 / Receivables Turnover
    - Days Payables = 365 / Payables Turnover

    Benchmarks:
    - Asset Turnover: > 1.0x (adequate), > 2.0x (efficient)
    - Inventory Turnover: 4-6x (manufacturing), 8-12x (retail)
    - Receivables Turnover: 6-12x (typical for 30-60 day terms)
    """
    if total_assets == Decimal('0'):
        raise ValueError("Total assets cannot be zero")

    asset_turnover = revenue / total_assets

    inventory_turnover = cogs / avg_inventory if avg_inventory > 0 else Decimal('0')
    receivables_turnover = revenue / avg_receivables if avg_receivables > 0 else Decimal('0')
    payables_turnover = cogs / avg_payables if avg_payables > 0 else Decimal('0')

    days_inventory = Decimal('365') / inventory_turnover if inventory_turnover > 0 else Decimal('0')
    days_receivables = Decimal('365') / receivables_turnover if receivables_turnover > 0 else Decimal('0')
    days_payables = Decimal('365') / payables_turnover if payables_turnover > 0 else Decimal('0')

    return EfficiencyRatios(
        asset_turnover=asset_turnover.quantize(Decimal('0.01')),
        inventory_turnover=inventory_turnover.quantize(Decimal('0.01')),
        receivables_turnover=receivables_turnover.quantize(Decimal('0.01')),
        payables_turnover=payables_turnover.quantize(Decimal('0.01')),
        days_inventory=days_inventory.quantize(Decimal('0.01')),
        days_receivables=days_receivables.quantize(Decimal('0.01')),
        days_payables=days_payables.quantize(Decimal('0.01')),
    )
```

### Leverage Ratios

Leverage ratios measure financial risk and capital structure.

```python
@dataclass
class LeverageRatios:
    """Leverage ratio metrics."""

    debt_to_equity: Decimal
    debt_to_assets: Decimal
    equity_multiplier: Decimal
    interest_coverage: Decimal
    debt_service_coverage: Decimal

def calculate_leverage_ratios(
    total_debt: Decimal,
    total_equity: Decimal,
    total_assets: Decimal,
    operating_income: Decimal,
    interest_expense: Decimal,
    principal_payment: Decimal,
) -> LeverageRatios:
    """
    Calculate leverage ratios.

    Formulas:
    - Debt-to-Equity = Total Debt / Total Equity
    - Debt-to-Assets = Total Debt / Total Assets
    - Equity Multiplier = Total Assets / Total Equity
    - Interest Coverage = Operating Income / Interest Expense
    - Debt Service Coverage = Operating Income / (Interest + Principal)

    Benchmarks:
    - Debt-to-Equity: < 1.0x (conservative), < 2.0x (moderate)
    - Interest Coverage: > 2.5x (adequate), > 5.0x (strong)
    - Debt Service Coverage: > 1.25x (adequate), > 2.0x (strong)
    """
    if total_equity == Decimal('0'):
        raise ValueError("Total equity cannot be zero")
    if total_assets == Decimal('0'):
        raise ValueError("Total assets cannot be zero")

    debt_to_equity = total_debt / total_equity
    debt_to_assets = total_debt / total_assets
    equity_multiplier = total_assets / total_equity

    interest_coverage = (
        operating_income / interest_expense
        if interest_expense > 0
        else Decimal('999.99')  # Effectively infinite if no interest
    )

    debt_service = interest_expense + principal_payment
    debt_service_coverage = (
        operating_income / debt_service
        if debt_service > 0
        else Decimal('999.99')
    )

    return LeverageRatios(
        debt_to_equity=debt_to_equity.quantize(Decimal('0.01')),
        debt_to_assets=debt_to_assets.quantize(Decimal('0.01')),
        equity_multiplier=equity_multiplier.quantize(Decimal('0.01')),
        interest_coverage=interest_coverage.quantize(Decimal('0.01')),
        debt_service_coverage=debt_service_coverage.quantize(Decimal('0.01')),
    )
```

## Growth Metrics

```python
@dataclass
class GrowthMetrics:
    """Growth rate metrics."""

    revenue_growth: Decimal
    yoy_growth: Decimal
    cagr: Decimal
    qoq_growth: Decimal

def calculate_revenue_growth(
    current_revenue: Decimal,
    prior_revenue: Decimal,
) -> Decimal:
    """
    Calculate revenue growth rate.

    Formula: Growth = (Current - Prior) / Prior × 100
    """
    if prior_revenue == Decimal('0'):
        raise ValueError("Prior revenue cannot be zero")

    growth = ((current_revenue - prior_revenue) / prior_revenue) * 100
    return growth.quantize(Decimal('0.01'))

def calculate_cagr(
    beginning_value: Decimal,
    ending_value: Decimal,
    num_periods: int,
) -> Decimal:
    """
    Calculate Compound Annual Growth Rate.

    Formula: CAGR = (Ending Value / Beginning Value)^(1/n) - 1

    Args:
        beginning_value: Starting value
        ending_value: Ending value
        num_periods: Number of years

    Returns:
        CAGR percentage
    """
    if beginning_value == Decimal('0'):
        raise ValueError("Beginning value cannot be zero")
    if num_periods <= 0:
        raise ValueError("Number of periods must be positive")

    # Convert to float for exponent, then back to Decimal
    ratio = float(ending_value / beginning_value)
    exponent = 1.0 / num_periods
    cagr = (Decimal(str(ratio ** exponent)) - Decimal('1')) * 100

    return cagr.quantize(Decimal('0.01'))
```

## DuPont Analysis

DuPont analysis decomposes ROE into components to identify performance drivers.

```python
@dataclass
class DuPontAnalysis:
    """DuPont ROE decomposition."""

    net_margin: Decimal
    asset_turnover: Decimal
    equity_multiplier: Decimal
    roe: Decimal

def calculate_dupont_roe(
    net_income: Decimal,
    revenue: Decimal,
    total_assets: Decimal,
    total_equity: Decimal,
) -> DuPontAnalysis:
    """
    Decompose ROE using DuPont formula.

    Formula: ROE = Net Margin × Asset Turnover × Equity Multiplier
           = (Net Income / Revenue) × (Revenue / Assets) × (Assets / Equity)

    This decomposition reveals whether ROE comes from:
    - Profitability (net margin)
    - Efficiency (asset turnover)
    - Leverage (equity multiplier)
    """
    if revenue == Decimal('0') or total_assets == Decimal('0') or total_equity == Decimal('0'):
        raise ValueError("Revenue, assets, and equity must be non-zero")

    net_margin = (net_income / revenue) * 100
    asset_turnover = revenue / total_assets
    equity_multiplier = total_assets / total_equity

    # ROE = components multiplied
    roe = (net_margin / 100) * asset_turnover * equity_multiplier * 100

    return DuPontAnalysis(
        net_margin=net_margin.quantize(Decimal('0.01')),
        asset_turnover=asset_turnover.quantize(Decimal('0.01')),
        equity_multiplier=equity_multiplier.quantize(Decimal('0.01')),
        roe=roe.quantize(Decimal('0.01')),
    )
```

## Comprehensive Ratio Analysis

```python
@dataclass
class FinancialRatioSuite:
    """Complete financial ratio analysis."""

    liquidity: LiquidityRatios
    profitability: ProfitabilityRatios
    efficiency: EfficiencyRatios
    leverage: LeverageRatios
    dupont: DuPontAnalysis

def analyze_financial_ratios(financials: dict) -> FinancialRatioSuite:
    """
    Calculate complete suite of financial ratios.

    Args:
        financials: Dictionary with all required financial statement data

    Returns:
        Comprehensive ratio analysis

    Required keys in financials dict:
    - Balance Sheet: current_assets, current_liabilities, inventory,
      cash, marketable_securities, total_assets, total_equity, total_debt
    - Income Statement: revenue, cogs, operating_income, net_income,
      interest, tax, depreciation, amortization
    - Averages: avg_inventory, avg_receivables, avg_payables
    """
    liquidity = calculate_liquidity_ratios(
        current_assets=Decimal(str(financials['current_assets'])),
        current_liabilities=Decimal(str(financials['current_liabilities'])),
        inventory=Decimal(str(financials['inventory'])),
        prepaid_expenses=Decimal(str(financials.get('prepaid_expenses', 0))),
        cash=Decimal(str(financials['cash'])),
        marketable_securities=Decimal(str(financials.get('marketable_securities', 0))),
    )

    profitability = calculate_profitability_ratios(
        revenue=Decimal(str(financials['revenue'])),
        cogs=Decimal(str(financials['cogs'])),
        operating_income=Decimal(str(financials['operating_income'])),
        net_income=Decimal(str(financials['net_income'])),
        interest=Decimal(str(financials['interest'])),
        tax=Decimal(str(financials['tax'])),
        depreciation=Decimal(str(financials['depreciation'])),
        amortization=Decimal(str(financials['amortization'])),
        total_assets=Decimal(str(financials['total_assets'])),
        total_equity=Decimal(str(financials['total_equity'])),
        invested_capital=Decimal(str(financials.get('invested_capital', financials['total_equity']))),
    )

    efficiency = calculate_efficiency_ratios(
        revenue=Decimal(str(financials['revenue'])),
        cogs=Decimal(str(financials['cogs'])),
        total_assets=Decimal(str(financials['total_assets'])),
        avg_inventory=Decimal(str(financials['avg_inventory'])),
        avg_receivables=Decimal(str(financials['avg_receivables'])),
        avg_payables=Decimal(str(financials['avg_payables'])),
    )

    leverage = calculate_leverage_ratios(
        total_debt=Decimal(str(financials['total_debt'])),
        total_equity=Decimal(str(financials['total_equity'])),
        total_assets=Decimal(str(financials['total_assets'])),
        operating_income=Decimal(str(financials['operating_income'])),
        interest_expense=Decimal(str(financials['interest'])),
        principal_payment=Decimal(str(financials.get('principal_payment', 0))),
    )

    dupont = calculate_dupont_roe(
        net_income=Decimal(str(financials['net_income'])),
        revenue=Decimal(str(financials['revenue'])),
        total_assets=Decimal(str(financials['total_assets'])),
        total_equity=Decimal(str(financials['total_equity'])),
    )

    return FinancialRatioSuite(
        liquidity=liquidity,
        profitability=profitability,
        efficiency=efficiency,
        leverage=leverage,
        dupont=dupont,
    )
```

## Ratio Trend Analysis

```python
import pandas as pd

def analyze_ratio_trends(
    financial_history: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate ratio trends over multiple periods.

    Args:
        financial_history: DataFrame with financial data by period

    Returns:
        DataFrame with calculated ratios by period
    """
    trends = pd.DataFrame()

    trends['period'] = financial_history['period']

    # Liquidity
    trends['current_ratio'] = (
        financial_history['current_assets'] /
        financial_history['current_liabilities']
    )

    # Profitability
    trends['gross_margin'] = (
        (financial_history['revenue'] - financial_history['cogs']) /
        financial_history['revenue'] * 100
    )
    trends['operating_margin'] = (
        financial_history['operating_income'] /
        financial_history['revenue'] * 100
    )
    trends['net_margin'] = (
        financial_history['net_income'] /
        financial_history['revenue'] * 100
    )

    # Efficiency
    trends['asset_turnover'] = (
        financial_history['revenue'] /
        financial_history['total_assets']
    )

    # Leverage
    trends['debt_to_equity'] = (
        financial_history['total_debt'] /
        financial_history['total_equity']
    )

    return trends
```

## Best Practices

### Data Validation

```python
def validate_financial_data(financials: dict) -> None:
    """
    Validate financial data before ratio calculation.

    Raises:
        ValueError: If data fails validation
    """
    required_fields = [
        'revenue', 'cogs', 'operating_income', 'net_income',
        'current_assets', 'current_liabilities', 'total_assets',
        'total_equity', 'total_debt'
    ]

    for field in required_fields:
        if field not in financials:
            raise ValueError(f"Missing required field: {field}")

        if financials[field] < 0 and field not in ['net_income', 'operating_income']:
            raise ValueError(f"{field} cannot be negative: {financials[field]}")
```

### Use Decimal Types

```python
# CORRECT: Use Decimal for all financial calculations
from decimal import Decimal

gross_margin = ((Decimal('1000000') - Decimal('600000')) / Decimal('1000000')) * 100
# Result: Decimal('40.00')

# INCORRECT: Float introduces precision errors
gross_margin = ((1000000.0 - 600000.0) / 1000000.0) * 100
# Result: 39.99999999999999 (precision loss)
```

### Average Balance Sheet Items

```python
def calculate_average_balance(beginning: Decimal, ending: Decimal) -> Decimal:
    """Calculate average balance for balance sheet items."""
    return (beginning + ending) / Decimal('2')

# Example: Average inventory for inventory turnover
avg_inventory = calculate_average_balance(
    beginning=Decimal('300000'),
    ending=Decimal('350000')
)
# Result: Decimal('325000.00')
```

## Integration with ERP Systems

See [../integrations/netsuite.md](../integrations/netsuite.md) for extracting financial statement data from NetSuite for ratio analysis.
