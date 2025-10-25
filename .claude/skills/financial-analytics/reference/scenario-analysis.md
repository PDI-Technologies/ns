# Scenario Analysis

Model multiple future scenarios for financial planning, risk assessment, and strategic decision-making.

## Contents

- [Overview](#overview)
- [Scenario Types](#scenario-types)
  - [Best Case / Base Case / Worst Case](#best-case--base-case--worst-case)
- [Sensitivity Analysis](#sensitivity-analysis)
- [Monte Carlo Simulation](#monte-carlo-simulation)
- [Scenario Comparison Tables](#scenario-comparison-tables)
- [Economic Scenario Modeling](#economic-scenario-modeling)
- [Stress Testing](#stress-testing)
- [Visualization](#visualization)
- [Best Practices](#best-practices)

## Overview

Scenario analysis evaluates how different assumptions and external conditions affect financial outcomes. This technique helps finance teams prepare for uncertainty and make informed strategic decisions.

## Scenario Types

### Best Case / Base Case / Worst Case

The most common scenario framework for financial planning.

```python
from dataclasses import dataclass
from decimal import Decimal

@dataclass
class ScenarioAssumptions:
    """Assumptions for scenario modeling."""

    revenue_growth_rate: Decimal
    gross_margin_pct: Decimal
    operating_expense_growth: Decimal
    tax_rate: Decimal
    capital_expenditure: Decimal

@dataclass
class ScenarioResult:
    """Scenario financial results."""

    scenario_name: str
    revenue: Decimal
    gross_profit: Decimal
    operating_income: Decimal
    net_income: Decimal
    free_cash_flow: Decimal

def create_scenario_framework(
    base_revenue: Decimal,
    base_opex: Decimal,
) -> dict[str, ScenarioAssumptions]:
    """
    Create standard three-scenario framework.

    Args:
        base_revenue: Current revenue baseline
        base_opex: Current operating expenses

    Returns:
        Dictionary with best/base/worst case assumptions
    """
    return {
        "best_case": ScenarioAssumptions(
            revenue_growth_rate=Decimal('0.20'),  # 20% growth
            gross_margin_pct=Decimal('65.0'),
            operating_expense_growth=Decimal('0.10'),  # 10% opex growth
            tax_rate=Decimal('0.21'),
            capital_expenditure=Decimal('50000'),
        ),
        "base_case": ScenarioAssumptions(
            revenue_growth_rate=Decimal('0.15'),  # 15% growth
            gross_margin_pct=Decimal('60.0'),
            operating_expense_growth=Decimal('0.12'),
            tax_rate=Decimal('0.21'),
            capital_expenditure=Decimal('75000'),
        ),
        "worst_case": ScenarioAssumptions(
            revenue_growth_rate=Decimal('0.05'),  # 5% growth
            gross_margin_pct=Decimal('55.0'),
            operating_expense_growth=Decimal('0.15'),  # 15% opex growth
            tax_rate=Decimal('0.21'),
            capital_expenditure=Decimal('100000'),
        ),
    }

def calculate_scenario_outcome(
    base_revenue: Decimal,
    base_opex: Decimal,
    assumptions: ScenarioAssumptions,
) -> ScenarioResult:
    """
    Calculate financial outcomes for a scenario.

    Args:
        base_revenue: Starting revenue
        base_opex: Starting operating expenses
        assumptions: Scenario assumptions

    Returns:
        Projected financial results
    """
    # Project revenue
    revenue = base_revenue * (Decimal('1') + assumptions.revenue_growth_rate)

    # Calculate gross profit
    gross_profit = revenue * (assumptions.gross_margin_pct / Decimal('100'))
    cogs = revenue - gross_profit

    # Calculate operating expenses
    opex = base_opex * (Decimal('1') + assumptions.operating_expense_growth)

    # Calculate operating income
    operating_income = gross_profit - opex

    # Calculate net income
    tax = operating_income * assumptions.tax_rate
    net_income = operating_income - tax

    # Calculate free cash flow (simplified)
    free_cash_flow = net_income - assumptions.capital_expenditure

    return ScenarioResult(
        scenario_name="",
        revenue=revenue.quantize(Decimal('0.01')),
        gross_profit=gross_profit.quantize(Decimal('0.01')),
        operating_income=operating_income.quantize(Decimal('0.01')),
        net_income=net_income.quantize(Decimal('0.01')),
        free_cash_flow=free_cash_flow.quantize(Decimal('0.01')),
    )
```

### Example Usage

```python
base_revenue = Decimal('1000000')
base_opex = Decimal('400000')

scenarios = create_scenario_framework(base_revenue, base_opex)
results = {}

for scenario_name, assumptions in scenarios.items():
    result = calculate_scenario_outcome(base_revenue, base_opex, assumptions)
    result.scenario_name = scenario_name
    results[scenario_name] = result

# Compare scenarios
print(f"Best Case Net Income: ${results['best_case'].net_income:,.2f}")
print(f"Base Case Net Income: ${results['base_case'].net_income:,.2f}")
print(f"Worst Case Net Income: ${results['worst_case'].net_income:,.2f}")
```

## Sensitivity Analysis

Analyze how changes in individual variables affect outcomes.

```python
import pandas as pd
import numpy as np

def sensitivity_analysis(
    base_value: Decimal,
    variable_name: str,
    range_pct: Decimal = Decimal('0.20'),  # +/- 20%
    steps: int = 11,
) -> pd.DataFrame:
    """
    Perform sensitivity analysis on a single variable.

    Args:
        base_value: Base case value
        variable_name: Name of variable being tested
        range_pct: Percentage range to test (+/-)
        steps: Number of test points

    Returns:
        DataFrame with sensitivity results
    """
    # Create range of values
    min_value = base_value * (Decimal('1') - range_pct)
    max_value = base_value * (Decimal('1') + range_pct)

    values = np.linspace(float(min_value), float(max_value), steps)

    results = []
    for value in values:
        pct_change = ((value - float(base_value)) / float(base_value)) * 100
        results.append({
            variable_name: value,
            'pct_change_from_base': pct_change,
        })

    return pd.DataFrame(results)

def multi_variable_sensitivity(
    base_assumptions: dict,
    variables_to_test: list[str],
    calculate_outcome_func,
) -> dict[str, pd.DataFrame]:
    """
    Perform sensitivity analysis on multiple variables.

    Args:
        base_assumptions: Dictionary of base case assumptions
        variables_to_test: List of variable names to test
        calculate_outcome_func: Function that calculates outcome

    Returns:
        Dictionary mapping variable names to sensitivity DataFrames
    """
    results = {}

    for variable in variables_to_test:
        base_value = base_assumptions[variable]
        sensitivity_df = sensitivity_analysis(Decimal(str(base_value)), variable)

        # Calculate outcome for each sensitivity value
        outcomes = []
        for _, row in sensitivity_df.iterrows():
            modified_assumptions = base_assumptions.copy()
            modified_assumptions[variable] = row[variable]

            outcome = calculate_outcome_func(modified_assumptions)
            outcomes.append(outcome)

        sensitivity_df['outcome'] = outcomes
        results[variable] = sensitivity_df

    return results
```

## Monte Carlo Simulation

Probabilistic scenario analysis using random sampling.

```python
from dataclasses import dataclass

@dataclass
class MonteCarloAssumptions:
    """Probability distributions for Monte Carlo simulation."""

    revenue_mean: float
    revenue_std: float

    margin_mean: float
    margin_std: float

    opex_mean: float
    opex_std: float

def monte_carlo_simulation(
    assumptions: MonteCarloAssumptions,
    iterations: int = 10000,
    random_seed: int = 42,
) -> dict:
    """
    Run Monte Carlo simulation for financial projections.

    Args:
        assumptions: Probability distributions for variables
        iterations: Number of simulation runs
        random_seed: Random seed for reproducibility

    Returns:
        Dictionary with simulation results and statistics
    """
    np.random.seed(random_seed)

    # Generate random samples
    revenue_samples = np.random.normal(
        assumptions.revenue_mean,
        assumptions.revenue_std,
        iterations
    )

    margin_samples = np.random.normal(
        assumptions.margin_mean,
        assumptions.margin_std,
        iterations
    )

    opex_samples = np.random.normal(
        assumptions.opex_mean,
        assumptions.opex_std,
        iterations
    )

    # Calculate outcomes
    gross_profit = revenue_samples * (margin_samples / 100)
    net_income = gross_profit - opex_samples

    # Calculate statistics
    results = {
        'iterations': iterations,
        'net_income': {
            'mean': np.mean(net_income),
            'median': np.median(net_income),
            'std': np.std(net_income),
            'min': np.min(net_income),
            'max': np.max(net_income),
            'p10': np.percentile(net_income, 10),  # 10th percentile (pessimistic)
            'p25': np.percentile(net_income, 25),
            'p50': np.percentile(net_income, 50),  # Median
            'p75': np.percentile(net_income, 75),
            'p90': np.percentile(net_income, 90),  # 90th percentile (optimistic)
        },
        'probability_profitable': (net_income > 0).sum() / iterations * 100,
        'samples': net_income,  # Full distribution for plotting
    }

    return results
```

### Example: Revenue Projection with Uncertainty

```python
# Define probability distributions
assumptions = MonteCarloAssumptions(
    revenue_mean=1_000_000,  # $1M expected revenue
    revenue_std=150_000,     # $150k standard deviation

    margin_mean=60.0,        # 60% expected margin
    margin_std=5.0,          # 5% margin variability

    opex_mean=400_000,       # $400k expected opex
    opex_std=50_000,         # $50k opex variability
)

# Run simulation
results = monte_carlo_simulation(assumptions, iterations=10000)

print(f"Expected Net Income: ${results['net_income']['mean']:,.0f}")
print(f"10th Percentile (Pessimistic): ${results['net_income']['p10']:,.0f}")
print(f"50th Percentile (Median): ${results['net_income']['p50']:,.0f}")
print(f"90th Percentile (Optimistic): ${results['net_income']['p90']:,.0f}")
print(f"Probability of Profitability: {results['probability_profitable']:.1f}%")
```

## Scenario Comparison Tables

```python
from rich.console import Console
from rich.table import Table

def generate_scenario_comparison(
    scenarios: dict[str, ScenarioResult],
) -> None:
    """
    Generate formatted scenario comparison table.

    Args:
        scenarios: Dictionary mapping scenario names to results
    """
    console = Console()

    table = Table(title="Scenario Analysis Comparison")
    table.add_column("Metric", style="cyan")

    for scenario_name in scenarios.keys():
        table.add_column(scenario_name.replace('_', ' ').title(), style="white")

    # Revenue row
    revenue_row = ["Revenue"]
    for result in scenarios.values():
        revenue_row.append(f"${result.revenue:,.0f}")
    table.add_row(*revenue_row)

    # Gross profit row
    gp_row = ["Gross Profit"]
    for result in scenarios.values():
        gp_row.append(f"${result.gross_profit:,.0f}")
    table.add_row(*gp_row)

    # Operating income row
    oi_row = ["Operating Income"]
    for result in scenarios.values():
        oi_row.append(f"${result.operating_income:,.0f}")
    table.add_row(*oi_row)

    # Net income row
    ni_row = ["Net Income"]
    for result in scenarios.values():
        ni_row.append(f"${result.net_income:,.0f}")
    table.add_row(*ni_row)

    # Free cash flow row
    fcf_row = ["Free Cash Flow"]
    for result in scenarios.values():
        fcf_row.append(f"${result.free_cash_flow:,.0f}")
    table.add_row(*fcf_row)

    console.print(table)
```

## Economic Scenario Modeling

Model macro-economic conditions and their impact.

```python
@dataclass
class EconomicScenario:
    """Economic environment assumptions."""

    scenario_name: str
    gdp_growth: Decimal
    inflation_rate: Decimal
    interest_rate: Decimal
    unemployment_rate: Decimal

def create_economic_scenarios() -> dict[str, EconomicScenario]:
    """Create standard economic scenarios."""
    return {
        "recession": EconomicScenario(
            scenario_name="Recession",
            gdp_growth=Decimal('-2.0'),
            inflation_rate=Decimal('1.5'),
            interest_rate=Decimal('2.0'),
            unemployment_rate=Decimal('8.0'),
        ),
        "slow_growth": EconomicScenario(
            scenario_name="Slow Growth",
            gdp_growth=Decimal('1.5'),
            inflation_rate=Decimal('2.0'),
            interest_rate=Decimal('3.5'),
            unemployment_rate=Decimal('5.5'),
        ),
        "moderate_growth": EconomicScenario(
            scenario_name="Moderate Growth",
            gdp_growth=Decimal('3.0'),
            inflation_rate=Decimal('2.5'),
            interest_rate=Decimal('4.5'),
            unemployment_rate=Decimal('4.5'),
        ),
        "strong_growth": EconomicScenario(
            scenario_name="Strong Growth",
            gdp_growth=Decimal('5.0'),
            inflation_rate=Decimal('3.5'),
            interest_rate=Decimal('6.0'),
            unemployment_rate=Decimal('3.5'),
        ),
    }

def apply_economic_scenario_to_financials(
    base_financials: dict,
    economic_scenario: EconomicScenario,
) -> dict:
    """
    Adjust financial projections based on economic scenario.

    Args:
        base_financials: Base case financial projections
        economic_scenario: Economic environment assumptions

    Returns:
        Adjusted financial projections
    """
    adjusted = base_financials.copy()

    # Revenue adjusts with GDP
    revenue_adjustment = Decimal('1') + (economic_scenario.gdp_growth / Decimal('100'))
    adjusted['revenue'] = base_financials['revenue'] * revenue_adjustment

    # Costs increase with inflation
    cost_adjustment = Decimal('1') + (economic_scenario.inflation_rate / Decimal('100'))
    adjusted['cogs'] = base_financials['cogs'] * cost_adjustment
    adjusted['opex'] = base_financials['opex'] * cost_adjustment

    # Interest expense adjusts with rates
    adjusted['interest_expense'] = (
        base_financials.get('debt', Decimal('0')) *
        (economic_scenario.interest_rate / Decimal('100'))
    )

    return adjusted
```

## Stress Testing

Test financial resilience under extreme conditions.

```python
@dataclass
class StressTest:
    """Stress test scenario."""

    test_name: str
    revenue_shock_pct: Decimal
    cost_shock_pct: Decimal
    liquidity_drain: Decimal

def create_stress_tests() -> list[StressTest]:
    """Create standard stress test scenarios."""
    return [
        StressTest(
            test_name="Revenue Collapse",
            revenue_shock_pct=Decimal('-30.0'),  # 30% revenue drop
            cost_shock_pct=Decimal('0'),
            liquidity_drain=Decimal('0'),
        ),
        StressTest(
            test_name="Cost Spike",
            revenue_shock_pct=Decimal('0'),
            cost_shock_pct=Decimal('25.0'),  # 25% cost increase
            liquidity_drain=Decimal('0'),
        ),
        StressTest(
            test_name="Liquidity Crisis",
            revenue_shock_pct=Decimal('-15.0'),
            cost_shock_pct=Decimal('10.0'),
            liquidity_drain=Decimal('500000'),  # $500k cash drain
        ),
        StressTest(
            test_name="Perfect Storm",
            revenue_shock_pct=Decimal('-40.0'),
            cost_shock_pct=Decimal('30.0'),
            liquidity_drain=Decimal('1000000'),
        ),
    ]

def run_stress_test(
    base_financials: dict,
    stress_test: StressTest,
) -> dict:
    """
    Run stress test and assess impact.

    Returns:
        Dictionary with stressed financials and survival metrics
    """
    # Apply shocks
    revenue = base_financials['revenue'] * (
        Decimal('1') + stress_test.revenue_shock_pct / Decimal('100')
    )

    costs = (base_financials['cogs'] + base_financials['opex']) * (
        Decimal('1') + stress_test.cost_shock_pct / Decimal('100')
    )

    cash = base_financials.get('cash', Decimal('0')) - stress_test.liquidity_drain

    # Calculate survival metrics
    net_income = revenue - costs
    months_of_runway = (cash / costs * 12) if costs > 0 else Decimal('999')

    return {
        'test_name': stress_test.test_name,
        'revenue': revenue,
        'costs': costs,
        'net_income': net_income,
        'cash': cash,
        'months_runway': months_runway.quantize(Decimal('0.1')),
        'survives': cash > 0 and net_income > 0,
    }
```

## Visualization

```python
import matplotlib.pyplot as plt

def plot_scenario_comparison(scenarios: dict[str, ScenarioResult]):
    """Create visual comparison of scenarios."""
    scenario_names = list(scenarios.keys())
    metrics = ['revenue', 'gross_profit', 'operating_income', 'net_income']

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.flatten()

    for idx, metric in enumerate(metrics):
        values = [float(getattr(scenarios[name], metric)) for name in scenario_names]

        axes[idx].bar(scenario_names, values, color=['green', 'blue', 'red'])
        axes[idx].set_title(metric.replace('_', ' ').title())
        axes[idx].set_ylabel('Amount ($)')
        axes[idx].grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig('scenario_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()

def plot_monte_carlo_distribution(results: dict):
    """Visualize Monte Carlo simulation results."""
    samples = results['samples']

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Histogram
    ax1.hist(samples, bins=50, edgecolor='black', alpha=0.7)
    ax1.axvline(results['net_income']['mean'], color='red', linestyle='--', label='Mean')
    ax1.axvline(results['net_income']['p50'], color='green', linestyle='--', label='Median')
    ax1.axvline(0, color='black', linestyle='-', linewidth=2, label='Break-even')
    ax1.set_xlabel('Net Income ($)')
    ax1.set_ylabel('Frequency')
    ax1.set_title('Monte Carlo Distribution')
    ax1.legend()
    ax1.grid(alpha=0.3)

    # Cumulative probability
    sorted_samples = np.sort(samples)
    cumulative_prob = np.arange(1, len(sorted_samples) + 1) / len(sorted_samples) * 100

    ax2.plot(sorted_samples, cumulative_prob, linewidth=2)
    ax2.axhline(50, color='green', linestyle='--', alpha=0.5, label='50th Percentile')
    ax2.axhline(90, color='blue', linestyle='--', alpha=0.5, label='90th Percentile')
    ax2.axvline(0, color='black', linestyle='-', linewidth=2, label='Break-even')
    ax2.set_xlabel('Net Income ($)')
    ax2.set_ylabel('Cumulative Probability (%)')
    ax2.set_title('Cumulative Probability Distribution')
    ax2.legend()
    ax2.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig('monte_carlo_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
```

## Best Practices

### 1. Use Realistic Ranges

Base scenario ranges on historical volatility and industry benchmarks, not arbitrary percentages.

### 2. Document Assumptions

Always document the rationale behind each scenario's assumptions.

### 3. Test Key Drivers

Focus sensitivity analysis on variables that have the largest impact on outcomes.

### 4. Update Regularly

Refresh scenarios quarterly or when market conditions change significantly.

### 5. Communicate Probabilities

When presenting Monte Carlo results, clearly communicate that these are probabilistic estimates, not guarantees.

## Integration with Planning

Use scenario analysis to inform:
- Annual budget planning
- Strategic planning
- Capital allocation decisions
- Risk management strategies
- Board presentations
