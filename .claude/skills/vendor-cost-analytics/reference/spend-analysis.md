# Vendor Spend Analysis

## Pareto Analysis (80/20 Rule)

### Concept
80% of spend typically comes from 20% of vendors. Identify these critical vendors.

### Implementation
```python
def pareto_analysis(vendor_spend: dict[str, float]) -> dict:
    """Calculate Pareto distribution of vendor spend."""
    sorted_vendors = sorted(vendor_spend.items(), key=lambda x: x[1], reverse=True)
    total_spend = sum(vendor_spend.values())

    cumulative_spend = 0
    pareto_vendors = []

    for vendor_id, spend in sorted_vendors:
        cumulative_spend += spend
        cumulative_pct = (cumulative_spend / total_spend) * 100

        pareto_vendors.append({
            'vendor_id': vendor_id,
            'spend': spend,
            'cumulative_pct': cumulative_pct
        })

        if cumulative_pct >= 80:
            break

    return {
        'critical_vendors': pareto_vendors,
        'vendor_count': len(pareto_vendors),
        'total_vendors': len(vendor_spend),
        'concentration': f"{len(pareto_vendors)/len(vendor_spend)*100:.1f}%"
    }
```

### Interpretation
- High concentration (< 10% of vendors = 80% spend): Good - focus on fewer relationships
- Low concentration (> 30% of vendors = 80% spend): Fragmented - consolidation opportunity

## Spend Segmentation (Kraljic Matrix)

### Four Categories

1. **Strategic** (High value, High complexity)
   - Critical to operations
   - Few alternatives
   - Strategic partnerships needed

2. **Leverage** (High value, Low complexity)
   - Many suppliers available
   - Negotiate aggressively
   - Consolidate for volume discounts

3. **Bottleneck** (Low value, High complexity)
   - Specialized items
   - Limited suppliers
   - Ensure supply continuity

4. **Non-Critical** (Low value, Low complexity)
   - Commodities
   - Automate procurement
   - Consider consolidation

### Classification Algorithm
```python
def segment_vendors(vendors: list[Vendor], median_spend: float) -> dict:
    """Segment vendors using Kraljic matrix."""
    segments = {'strategic': [], 'leverage': [], 'bottleneck': [], 'non_critical': []}

    for vendor in vendors:
        is_high_value = vendor.annual_spend >= median_spend
        is_high_complexity = vendor.product_complexity_score >= 5  # 1-10 scale

        if is_high_value and is_high_complexity:
            segments['strategic'].append(vendor)
        elif is_high_value and not is_high_complexity:
            segments['leverage'].append(vendor)
        elif not is_high_value and is_high_complexity:
            segments['bottleneck'].append(vendor)
        else:
            segments['non_critical'].append(vendor)

    return segments
```

## Spend Trends

### Time Series Analysis
```python
import pandas as pd

def analyze_spend_trends(transactions: pd.DataFrame, months: int = 12) -> pd.DataFrame:
    """Calculate monthly spend trends."""
    # Ensure datetime
    transactions['date'] = pd.to_datetime(transactions['transaction_date'])

    # Group by month and vendor
    monthly = transactions.groupby([
        pd.Grouper(key='date', freq='ME'),
        'vendor_id'
    ])['amount'].sum().reset_index()

    # Calculate trend metrics
    trends = monthly.groupby('vendor_id').agg({
        'amount': ['mean', 'std', 'min', 'max']
    })

    trends['volatility'] = trends[('amount', 'std')] / trends[('amount', 'mean')]
    trends['trend'] = calculate_linear_trend(monthly)  # Linear regression

    return trends
```

### Identifying Anomalies
- **Spike detection**: Spend > 2 standard deviations above mean
- **Drop detection**: Spend < 0.5 of average (potential supplier switch)
- **Seasonality**: Use seasonal decomposition for recurring patterns

## Category Spend Analysis

### Categorization
Group vendors by:
- Product/service category
- Geography
- Business unit
- Contract status (under contract vs maverick)

### Analysis
```python
def category_breakdown(transactions: list[Transaction]) -> dict:
    """Break down spend by category."""
    categories = {}

    for txn in transactions:
        cat = txn.category or 'Uncategorized'
        if cat not in categories:
            categories[cat] = {
                'spend': 0,
                'vendor_count': set(),
                'transaction_count': 0
            }

        categories[cat]['spend'] += txn.amount
        categories[cat]['vendor_count'].add(txn.vendor_id)
        categories[cat]['transaction_count'] += 1

    # Convert sets to counts
    for cat in categories:
        categories[cat]['vendor_count'] = len(categories[cat]['vendor_count'])

    return categories
```

## Vendor Concentration Risk

### Metrics
- **HHI (Herfindahl-Hirschman Index)**: Sum of squared market shares
- **Top 5 Concentration**: % spend with top 5 vendors
- **Single Vendor Dependency**: Any vendor > 25% of spend

### Implementation
```python
def calculate_hhi(vendor_spend: dict[str, float]) -> float:
    """Calculate Herfindahl-Hirschman Index."""
    total_spend = sum(vendor_spend.values())
    market_shares = [(spend / total_spend) for spend in vendor_spend.values()]
    hhi = sum(share ** 2 for share in market_shares) * 10000
    return hhi

# Interpretation:
# HHI < 1500: Low concentration (competitive)
# HHI 1500-2500: Moderate concentration
# HHI > 2500: High concentration (risky)
```

## Maverick Spend Detection

**Definition**: Purchases outside of established contracts or approved vendors.

### Detection Methods
1. **Contract Coverage**: Identify vendors without contracts
2. **Off-catalog Purchases**: Items not in approved catalog
3. **Unauthorized Vendors**: Vendors not in approved list
4. **Price Variance**: Paying more than contracted rates

### Implementation
```python
def detect_maverick_spend(
    transactions: list[Transaction],
    approved_vendors: set[str],
    contracted_rates: dict[str, float]
) -> list[Transaction]:
    """Find maverick spend transactions."""
    maverick = []

    for txn in transactions:
        # Check vendor approval
        if txn.vendor_id not in approved_vendors:
            maverick.append(txn)
            continue

        # Check price variance
        if txn.item_id in contracted_rates:
            contracted_price = contracted_rates[txn.item_id]
            variance = (txn.unit_price - contracted_price) / contracted_price
            if variance > 0.05:  # 5% over contract
                maverick.append(txn)

    return maverick
```

## Advanced Topics

### Spend Forecasting
→ **See**: [reference/forecasting.md](reference/forecasting.md)

Methods:
- Moving averages
- Exponential smoothing
- Linear regression
- Seasonal ARIMA

### Vendor Scorecarding
→ **See**: [reference/vendor-scoring.md](reference/vendor-scoring.md)

Dimensions:
- Cost competitiveness
- Quality metrics
- Delivery performance
- Payment terms
- Risk factors

### Currency Normalization
→ **See**: [reference/currency.md](reference/currency.md)

Handling multi-currency spend:
- Exchange rate sources
- Rate date matching
- Historical vs current rates
- Reporting currency selection

## Visualization Recommendations

### Key Charts

**Pareto Chart**: Cumulative spend by vendor (bar + line)
**Treemap**: Hierarchical spend visualization
**Trend Lines**: Monthly spend over time
**Scatter Plot**: Spend vs transaction count (identify consolidation opportunities)
**Heat Map**: Spend by category and time period

### Dashboard Layout

**Executive View**:
- Total spend (current period)
- Top 10 vendors table
- Spend trend chart (12 months)
- Key metrics cards (vendor count, avg spend, maverick %)

**Operational View**:
- Detailed vendor list with filters
- Duplicate vendor alerts
- Price variance exceptions
- Contract expiration notices

## Data Requirements

### Minimum Required Fields
- Vendor ID (unique identifier)
- Vendor name
- Transaction amount
- Transaction date

### Recommended Fields
- Currency
- Category/commodity code
- Business unit
- Contract reference
- Payment terms
- Item/SKU
- Unit price and quantity

### Data Quality Checks
- No null vendor IDs
- Positive amounts (negative = credit memos, handle separately)
- Valid dates (not future dates)
- Currency codes (ISO 4217)
- Vendor names not empty

## Implementation Example

See [examples/vendor-analytics-cli.md](examples/vendor-analytics-cli.md) for complete CLI application implementing:
- Data sync from NetSuite
- Local PostgreSQL storage
- Spend analysis
- Duplicate detection
- Rich terminal output

---

*Use this skill when building vendor management systems, procurement analytics, or spend optimization tools.*
