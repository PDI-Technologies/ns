# Financial Forecasting

Comprehensive forecasting methodologies for revenue, expenses, cash flow, and financial statement projections.

## Contents

- [Overview](#overview)
- [Forecasting Methods](#forecasting-methods)
  - [Simple Moving Average](#simple-moving-average)
  - [Weighted Moving Average](#weighted-moving-average)
  - [Exponential Smoothing](#exponential-smoothing)
  - [Double Exponential Smoothing](#double-exponential-smoothing-holts-method)
  - [Linear Regression Forecasting](#linear-regression-forecasting)
  - [Seasonal Decomposition](#seasonal-decomposition-and-forecasting)
- [Revenue Forecasting](#revenue-forecasting)
  - [Bottom-Up Revenue Forecast](#bottom-up-revenue-forecast)
  - [Top-Down Revenue Forecast](#top-down-revenue-forecast)
- [Expense Forecasting](#expense-forecasting)
  - [Fixed and Variable Cost Model](#fixed-and-variable-cost-model)
  - [Department Budget Forecasting](#department-budget-forecasting)
- [Cash Flow Forecasting](#cash-flow-forecasting)
  - [Direct Method](#direct-method-cash-flow-forecast)
  - [13-Week Cash Flow Forecast](#13-week-cash-flow-forecast)
- [Scenario Planning](#scenario-planning)
  - [Best/Base/Worst Case](#bestbaseworst-case-scenarios)
  - [Monte Carlo Simulation](#monte-carlo-simulation)
- [Forecast Accuracy Metrics](#forecast-accuracy-metrics)
- [Best Practices](#best-practices)

## Overview

Financial forecasting uses historical data, statistical models, and business intelligence to predict future financial performance. This guide covers practical forecasting techniques used in FP&A (Financial Planning and Analysis).

## Forecasting Methods

### Simple Moving Average

```python
from decimal import Decimal
import pandas as pd

def simple_moving_average(
    data: pd.Series,
    window: int,
) -> pd.Series:
    """
    Calculate simple moving average forecast.

    Args:
        data: Historical time series data
        window: Number of periods to average

    Returns:
        Moving average series

    Best for: Smoothing short-term fluctuations
    """
    return data.rolling(window=window).mean()

# Example
historical_revenue = pd.Series([100000, 105000, 110000, 108000, 115000, 120000])
forecast = simple_moving_average(historical_revenue, window=3)
# Last value (120000) forecasted from average of (108000, 115000, 120000)
```

### Weighted Moving Average

```python
def weighted_moving_average(
    data: pd.Series,
    weights: list[float],
) -> pd.Series:
    """
    Calculate weighted moving average with more emphasis on recent periods.

    Args:
        data: Historical time series data
        weights: Weights for each period (must sum to 1.0)

    Returns:
        Weighted moving average series

    Best for: When recent data is more relevant than older data
    """
    if abs(sum(weights) - 1.0) > 0.001:
        raise ValueError("Weights must sum to 1.0")

    window = len(weights)
    result = []

    for i in range(len(data)):
        if i < window - 1:
            result.append(None)
        else:
            weighted_sum = sum(
                data.iloc[i - window + 1 + j] * weights[j]
                for j in range(window)
            )
            result.append(weighted_sum)

    return pd.Series(result, index=data.index)

# Example: More weight on recent months
weights = [0.1, 0.2, 0.3, 0.4]  # Sum = 1.0, heaviest weight on most recent
forecast = weighted_moving_average(historical_revenue, weights)
```

### Exponential Smoothing

```python
def exponential_smoothing(
    data: pd.Series,
    alpha: float = 0.3,
) -> pd.Series:
    """
    Apply exponential smoothing for forecasting.

    Formula: Forecast[t] = alpha * Actual[t-1] + (1 - alpha) * Forecast[t-1]

    Args:
        data: Historical time series data
        alpha: Smoothing parameter (0 to 1)
               - Higher alpha: More responsive to recent changes
               - Lower alpha: More smoothing

    Returns:
        Smoothed forecast series

    Best for: Short-term forecasting with trend
    """
    if not 0 <= alpha <= 1:
        raise ValueError("Alpha must be between 0 and 1")

    result = [data.iloc[0]]  # Start with first actual value

    for i in range(1, len(data)):
        smoothed = alpha * data.iloc[i] + (1 - alpha) * result[-1]
        result.append(smoothed)

    return pd.Series(result, index=data.index)
```

### Double Exponential Smoothing (Holt's Method)

```python
from dataclasses import dataclass

@dataclass
class HoltForecast:
    """Holt's double exponential smoothing forecast."""

    level: list[float]
    trend: list[float]
    forecast: list[float]

def double_exponential_smoothing(
    data: pd.Series,
    alpha: float = 0.3,
    beta: float = 0.1,
    periods_ahead: int = 1,
) -> HoltForecast:
    """
    Holt's double exponential smoothing for data with trend.

    Args:
        data: Historical time series data
        alpha: Level smoothing parameter
        beta: Trend smoothing parameter
        periods_ahead: Number of periods to forecast

    Returns:
        Forecast with level and trend components

    Best for: Data with linear trend but no seasonality
    """
    level = [data.iloc[0]]
    trend = [data.iloc[1] - data.iloc[0]]
    forecast = [level[0] + trend[0]]

    for i in range(1, len(data)):
        # Update level
        new_level = alpha * data.iloc[i] + (1 - alpha) * (level[-1] + trend[-1])
        level.append(new_level)

        # Update trend
        new_trend = beta * (level[-1] - level[-2]) + (1 - beta) * trend[-1]
        trend.append(new_trend)

        # Forecast
        new_forecast = level[-1] + trend[-1] * periods_ahead
        forecast.append(new_forecast)

    return HoltForecast(
        level=level,
        trend=trend,
        forecast=forecast,
    )
```

### Linear Regression Forecasting

```python
from sklearn.linear_model import LinearRegression
import numpy as np

def linear_regression_forecast(
    data: pd.Series,
    periods_ahead: int = 3,
) -> tuple[pd.Series, dict]:
    """
    Forecast using linear regression.

    Args:
        data: Historical time series data
        periods_ahead: Number of future periods to forecast

    Returns:
        Tuple of (forecast series, model stats)

    Best for: Data with clear linear trend
    """
    # Prepare data
    X = np.array(range(len(data))).reshape(-1, 1)
    y = data.values

    # Fit model
    model = LinearRegression()
    model.fit(X, y)

    # Forecast
    future_X = np.array(range(len(data), len(data) + periods_ahead)).reshape(-1, 1)
    forecast = model.predict(future_X)

    # Model statistics
    r_squared = model.score(X, y)
    stats = {
        'slope': model.coef_[0],
        'intercept': model.intercept_,
        'r_squared': r_squared,
    }

    forecast_index = pd.RangeIndex(
        start=len(data),
        stop=len(data) + periods_ahead
    )

    return pd.Series(forecast, index=forecast_index), stats
```

### Seasonal Decomposition and Forecasting

```python
from statsmodels.tsa.seasonal import seasonal_decompose

@dataclass
class SeasonalForecast:
    """Seasonal decomposition forecast."""

    trend: pd.Series
    seasonal: pd.Series
    residual: pd.Series
    forecast: pd.Series

def seasonal_forecast(
    data: pd.Series,
    period: int = 12,
    periods_ahead: int = 3,
) -> SeasonalForecast:
    """
    Forecast using seasonal decomposition.

    Args:
        data: Historical time series data
        period: Seasonal period (12 for monthly, 4 for quarterly)
        periods_ahead: Number of future periods

    Returns:
        Seasonal forecast components

    Best for: Data with clear seasonal patterns (e.g., retail sales)
    """
    # Decompose
    decomposition = seasonal_decompose(
        data,
        model='additive',
        period=period
    )

    # Extract components
    trend = decomposition.trend
    seasonal = decomposition.seasonal
    residual = decomposition.resid

    # Forecast trend using linear regression
    trend_clean = trend.dropna()
    X = np.array(range(len(trend_clean))).reshape(-1, 1)
    y = trend_clean.values

    model = LinearRegression()
    model.fit(X, y)

    future_X = np.array(
        range(len(data), len(data) + periods_ahead)
    ).reshape(-1, 1)
    trend_forecast = model.predict(future_X)

    # Apply seasonal pattern
    seasonal_pattern = seasonal[-period:].values
    seasonal_forecast_values = [
        seasonal_pattern[i % period]
        for i in range(periods_ahead)
    ]

    # Combine trend + seasonal
    forecast_values = trend_forecast + seasonal_forecast_values

    forecast_index = pd.RangeIndex(
        start=len(data),
        stop=len(data) + periods_ahead
    )

    return SeasonalForecast(
        trend=trend,
        seasonal=seasonal,
        residual=residual,
        forecast=pd.Series(forecast_values, index=forecast_index),
    )
```

## Revenue Forecasting

### Bottom-Up Revenue Forecast

```python
from decimal import Decimal

@dataclass
class RevenueDrivers:
    """Revenue forecast drivers."""

    num_customers: int
    avg_order_value: Decimal
    orders_per_customer: Decimal
    conversion_rate: Decimal

def bottom_up_revenue_forecast(
    drivers: RevenueDrivers,
) -> Decimal:
    """
    Calculate revenue using bottom-up driver-based approach.

    Formula: Revenue = Customers × Orders/Customer × Avg Order Value

    Best Practice: Base forecast on operational metrics
    """
    revenue = (
        Decimal(str(drivers.num_customers)) *
        drivers.orders_per_customer *
        drivers.avg_order_value
    )

    return revenue.quantize(Decimal('0.01'))

# Example
drivers = RevenueDrivers(
    num_customers=1000,
    avg_order_value=Decimal('250.00'),
    orders_per_customer=Decimal('4.5'),
    conversion_rate=Decimal('0.15'),  # 15%
)

forecasted_revenue = bottom_up_revenue_forecast(drivers)
# Result: 1000 × 4.5 × $250 = $1,125,000
```

### Top-Down Revenue Forecast

```python
def top_down_revenue_forecast(
    market_size: Decimal,
    market_share: Decimal,
) -> Decimal:
    """
    Calculate revenue using top-down market-based approach.

    Formula: Revenue = Total Market Size × Market Share %

    Args:
        market_size: Total addressable market (TAM)
        market_share: Expected market share (0.0 to 1.0)

    Returns:
        Forecasted revenue

    Best for: Market sizing exercises, strategic planning
    """
    if not 0 <= market_share <= 1:
        raise ValueError("Market share must be between 0 and 1")

    revenue = market_size * market_share
    return revenue.quantize(Decimal('0.01'))
```

## Expense Forecasting

### Fixed and Variable Cost Model

```python
@dataclass
class ExpenseForecast:
    """Expense forecast breakdown."""

    fixed_costs: Decimal
    variable_costs: Decimal
    total_costs: Decimal
    variable_cost_ratio: Decimal

def forecast_expenses(
    revenue: Decimal,
    fixed_costs: Decimal,
    variable_cost_percentage: Decimal,
) -> ExpenseForecast:
    """
    Forecast expenses using fixed + variable cost model.

    Formula: Total Costs = Fixed Costs + (Revenue × Variable %)

    Args:
        revenue: Forecasted revenue
        fixed_costs: Fixed operating costs (rent, salaries, etc.)
        variable_cost_percentage: Variable costs as % of revenue (COGS, commissions)

    Returns:
        Expense forecast breakdown
    """
    variable_costs = revenue * (variable_cost_percentage / Decimal('100'))
    total_costs = fixed_costs + variable_costs
    variable_ratio = variable_cost_percentage / Decimal('100')

    return ExpenseForecast(
        fixed_costs=fixed_costs,
        variable_costs=variable_costs,
        total_costs=total_costs,
        variable_cost_ratio=variable_ratio,
    )
```

### Department Budget Forecasting

```python
@dataclass
class DepartmentBudget:
    """Department budget forecast."""

    department: str
    headcount: int
    avg_salary: Decimal
    other_expenses: Decimal
    total_budget: Decimal

def forecast_department_budget(
    department: str,
    headcount: int,
    avg_salary: Decimal,
    benefits_rate: Decimal = Decimal('0.30'),  # 30% of salary
    other_expenses: Decimal = Decimal('0'),
) -> DepartmentBudget:
    """
    Forecast department budget based on headcount.

    Components:
    - Salaries: Headcount × Average Salary
    - Benefits: Salaries × Benefits Rate
    - Other: SaaS, travel, equipment, etc.
    """
    salaries = Decimal(str(headcount)) * avg_salary
    benefits = salaries * benefits_rate
    total_budget = salaries + benefits + other_expenses

    return DepartmentBudget(
        department=department,
        headcount=headcount,
        avg_salary=avg_salary,
        other_expenses=other_expenses,
        total_budget=total_budget.quantize(Decimal('0.01')),
    )
```

## Cash Flow Forecasting

### Direct Method Cash Flow Forecast

```python
@dataclass
class CashFlowForecast:
    """Cash flow forecast."""

    cash_inflows: Decimal
    cash_outflows: Decimal
    net_cash_flow: Decimal
    ending_cash: Decimal

def forecast_cash_flow(
    beginning_cash: Decimal,
    cash_receipts: Decimal,
    cash_disbursements: Decimal,
) -> CashFlowForecast:
    """
    Forecast cash flow using direct method.

    Formula: Ending Cash = Beginning Cash + Receipts - Disbursements

    Args:
        beginning_cash: Starting cash balance
        cash_receipts: Expected cash collections
        cash_disbursements: Expected cash payments

    Returns:
        Cash flow forecast
    """
    net_cash_flow = cash_receipts - cash_disbursements
    ending_cash = beginning_cash + net_cash_flow

    return CashFlowForecast(
        cash_inflows=cash_receipts,
        cash_outflows=cash_disbursements,
        net_cash_flow=net_cash_flow,
        ending_cash=ending_cash,
    )
```

### 13-Week Cash Flow Forecast

```python
import pandas as pd
from datetime import datetime, timedelta

def create_13_week_cash_forecast(
    starting_cash: Decimal,
    weekly_revenue: Decimal,
    collection_days: int = 45,  # DSO
    weekly_expenses: Decimal,
    payment_days: int = 30,  # DPO
) -> pd.DataFrame:
    """
    Create 13-week rolling cash flow forecast.

    Best Practice: Update weekly for near-term cash visibility

    Args:
        starting_cash: Beginning cash balance
        weekly_revenue: Expected weekly revenue
        collection_days: Days to collect AR
        weekly_expenses: Expected weekly expenses
        payment_days: Days to pay AP

    Returns:
        DataFrame with 13-week cash forecast
    """
    weeks = []
    current_date = datetime.now()
    cash_balance = starting_cash

    for week in range(13):
        week_date = current_date + timedelta(weeks=week)

        # Simplified: Assume collections and payments happen with lag
        collections_weeks_ago = week - (collection_days // 7)
        payments_weeks_ago = week - (payment_days // 7)

        collections = weekly_revenue if collections_weeks_ago >= 0 else Decimal('0')
        payments = weekly_expenses if payments_weeks_ago >= 0 else Decimal('0')

        cash_flow = collections - payments
        cash_balance += cash_flow

        weeks.append({
            'week': week + 1,
            'week_ending': week_date.strftime('%Y-%m-%d'),
            'collections': float(collections),
            'payments': float(payments),
            'net_cash_flow': float(cash_flow),
            'ending_cash': float(cash_balance),
        })

    return pd.DataFrame(weeks)
```

## Scenario Planning

### Best/Base/Worst Case Scenarios

```python
@dataclass
class ScenarioForecast:
    """Multi-scenario forecast."""

    best_case: Decimal
    base_case: Decimal
    worst_case: Decimal

def create_scenario_forecasts(
    base_revenue: Decimal,
    upside_factor: Decimal = Decimal('1.15'),  # 15% upside
    downside_factor: Decimal = Decimal('0.85'),  # 15% downside
) -> ScenarioForecast:
    """
    Create best/base/worst case revenue scenarios.

    Best for: Risk assessment and contingency planning
    """
    return ScenarioForecast(
        best_case=(base_revenue * upside_factor).quantize(Decimal('0.01')),
        base_case=base_revenue,
        worst_case=(base_revenue * downside_factor).quantize(Decimal('0.01')),
    )
```

### Monte Carlo Simulation

```python
import numpy as np

def monte_carlo_revenue_forecast(
    mean_revenue: float,
    std_dev: float,
    simulations: int = 1000,
) -> dict:
    """
    Run Monte Carlo simulation for revenue forecast.

    Args:
        mean_revenue: Expected revenue
        std_dev: Revenue standard deviation
        simulations: Number of simulation runs

    Returns:
        Dictionary with percentile forecasts

    Best for: Probabilistic forecasting with uncertainty
    """
    # Run simulations
    simulated_revenues = np.random.normal(mean_revenue, std_dev, simulations)

    # Calculate percentiles
    return {
        'p10': np.percentile(simulated_revenues, 10),  # Pessimistic
        'p50': np.percentile(simulated_revenues, 50),  # Median
        'p90': np.percentile(simulated_revenues, 90),  # Optimistic
        'mean': np.mean(simulated_revenues),
        'std_dev': np.std(simulated_revenues),
    }
```

## Forecast Accuracy Metrics

### Mean Absolute Percentage Error (MAPE)

```python
def calculate_mape(
    actuals: pd.Series,
    forecasts: pd.Series,
) -> Decimal:
    """
    Calculate Mean Absolute Percentage Error.

    Formula: MAPE = (1/n) × Σ |Actual - Forecast| / Actual × 100

    Lower is better: < 10% (excellent), 10-20% (good), > 20% (poor)
    """
    if len(actuals) != len(forecasts):
        raise ValueError("Actuals and forecasts must have same length")

    percentage_errors = abs((actuals - forecasts) / actuals) * 100
    mape = percentage_errors.mean()

    return Decimal(str(mape)).quantize(Decimal('0.01'))
```

### Forecast Bias

```python
def calculate_forecast_bias(
    actuals: pd.Series,
    forecasts: pd.Series,
) -> Decimal:
    """
    Calculate forecast bias (tendency to over/under forecast).

    Formula: Bias = Σ(Forecast - Actual) / Σ Actual × 100

    Positive bias: Over-forecasting
    Negative bias: Under-forecasting
    """
    total_error = (forecasts - actuals).sum()
    total_actual = actuals.sum()

    bias = (total_error / total_actual * 100) if total_actual != 0 else 0

    return Decimal(str(bias)).quantize(Decimal('0.01'))
```

## Best Practices

### 1. Use Multiple Methods

Combine multiple forecasting techniques and average results:

```python
def ensemble_forecast(
    data: pd.Series,
    periods_ahead: int = 3,
) -> Decimal:
    """
    Ensemble forecast using multiple methods.

    Combines moving average, exponential smoothing, and linear regression
    """
    # Method 1: Moving average
    ma = simple_moving_average(data, window=3).iloc[-1]

    # Method 2: Exponential smoothing
    es = exponential_smoothing(data, alpha=0.3).iloc[-1]

    # Method 3: Linear regression
    lr_forecast, _ = linear_regression_forecast(data, periods_ahead=1)
    lr = lr_forecast.iloc[0]

    # Average all methods
    ensemble = (ma + es + lr) / 3

    return Decimal(str(ensemble)).quantize(Decimal('0.01'))
```

### 2. Update Forecasts Regularly

- Monthly forecasts: Update weekly
- Quarterly forecasts: Update monthly
- Annual forecasts: Update quarterly

### 3. Document Assumptions

```python
@dataclass
class ForecastAssumptions:
    """Document forecast assumptions."""

    method: str
    date_created: datetime
    created_by: str
    key_assumptions: list[str]
    data_source: str
    confidence_level: str  # 'high', 'medium', 'low'
```

### 4. Validate Against History

Always back-test forecasts against historical actuals to measure accuracy.

## Integration with ERP Systems

See [../integrations/netsuite.md](../integrations/netsuite.md) for extracting historical financial data from NetSuite for forecasting.
