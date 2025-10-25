# Vendor Segmentation

Kraljic Portfolio Purchasing Model for strategic vendor segmentation based on Profit Impact and Supply Risk.

## Overview

Vendor segmentation enables differentiated procurement strategies based on vendor importance and supply market complexity.

**Kraljic Matrix (1983):**
- **Developed by:** Peter Kraljic, Harvard Business Review
- **Dimensions:** Profit Impact (spend volume) vs Supply Risk (market complexity)
- **Outcome:** Four vendor categories requiring different management approaches
- **Business Impact:** Focus resources on strategic vendors, automate low-value categories

**Application:**
- Prioritize vendor relationship management
- Tailor negotiation strategies by segment
- Allocate procurement resources efficiently
- Identify consolidation vs diversification opportunities

**Source:** Based on Perplexity research on Kraljic Portfolio Purchasing Model

## Four Vendor Categories

### 1. Strategic Vendors (High Impact, High Risk)

**Characteristics:**
- High annual spend
- Few alternative suppliers available
- Critical to operations
- Complex products/services
- Long lead times
- Specialized requirements

**Procurement Strategy:**
- Develop strategic partnerships
- Long-term contracts with SLAs
- Collaborative innovation
- Risk mitigation planning
- Executive-level relationships
- Joint business planning

**Examples:**
- Key raw material suppliers
- Proprietary technology vendors
- Single-source manufacturers
- Critical service providers

### 2. Leverage Vendors (High Impact, Low Risk)

**Characteristics:**
- High annual spend
- Many alternative suppliers available
- Competitive market
- Standardized products/services
- Price transparency

**Procurement Strategy:**
- Aggressive negotiation
- Competitive bidding
- Volume consolidation for discounts
- Short-term contracts
- Substitute product exploration
- Multi-sourcing when beneficial

**Examples:**
- Office supplies
- Standard components
- Commodity materials
- Freight/logistics

### 3. Bottleneck Vendors (Low Impact, High Risk)

**Characteristics:**
- Low annual spend
- Limited supplier options
- Specialized items
- Long lead times or low availability
- Switching costs high

**Procurement Strategy:**
- Ensure supply continuity
- Maintain safety stock
- Develop backup suppliers
- Long-term relationships
- Consider volume commitments for priority
- Monitor market for alternatives

**Examples:**
- Specialized spare parts
- Niche service providers
- Regulated items
- Custom tooling

### 4. Non-Critical Vendors (Low Impact, Low Risk)

**Characteristics:**
- Low annual spend
- Many suppliers available
- Standardized products
- Easy to switch vendors
- Administrative burden

**Procurement Strategy:**
- Standardize and automate procurement
- Consolidate vendors to reduce overhead
- Use purchasing cards or catalogs
- Minimize administrative effort
- Consider elimination or substitution

**Examples:**
- Cleaning supplies
- General maintenance
- Low-value services
- Miscellaneous items

## Implementation

### Classification Algorithm

```python
from dataclasses import dataclass

@dataclass
class VendorSegment:
    """Vendor segmentation classification."""
    vendor_id: str
    vendor_name: str
    annual_spend: float
    supply_risk_score: float  # 1-10 scale
    segment: str  # STRATEGIC, LEVERAGE, BOTTLENECK, NON_CRITICAL
    procurement_strategy: str

def segment_vendors(
    vendors: list[Vendor],
    vendor_spend: dict[str, float],
    supply_risk_scores: dict[str, float],  # Vendor ID -> risk score (1-10)
    spend_threshold: float | None = None
) -> list[VendorSegment]:
    """
    Segment vendors using Kraljic matrix.

    Args:
        vendors: List of vendors
        vendor_spend: Annual spend by vendor
        supply_risk_scores: Supply risk assessment (1-10, where 10 = highest risk)
        spend_threshold: Spend threshold for high/low (None = use median)

    Returns:
        List of vendor segments
    """
    # Calculate threshold if not provided (use median)
    if spend_threshold is None:
        spend_values = list(vendor_spend.values())
        spend_threshold = calculate_median(spend_values)

    segments = []

    for vendor in vendors:
        annual_spend = vendor_spend.get(vendor.id, 0)
        risk_score = supply_risk_scores.get(vendor.id, 5)  # Default medium risk

        # Classify
        is_high_spend = annual_spend >= spend_threshold
        is_high_risk = risk_score >= 6  # Risk score 6+ = high risk

        if is_high_spend and is_high_risk:
            segment = 'STRATEGIC'
            strategy = 'Develop strategic partnership, long-term contracts, collaborative planning'
        elif is_high_spend and not is_high_risk:
            segment = 'LEVERAGE'
            strategy = 'Negotiate aggressively, competitive bidding, consolidate volume'
        elif not is_high_spend and is_high_risk:
            segment = 'BOTTLENECK'
            strategy = 'Ensure supply continuity, safety stock, develop backups'
        else:
            segment = 'NON_CRITICAL'
            strategy = 'Automate procurement, consolidate vendors, minimize effort'

        segments.append(VendorSegment(
            vendor_id=vendor.id,
            vendor_name=vendor.company_name or vendor.entity_id,
            annual_spend=annual_spend,
            supply_risk_score=risk_score,
            segment=segment,
            procurement_strategy=strategy
        ))

    return segments

def calculate_median(values: list[float]) -> float:
    """Calculate median value."""
    sorted_values = sorted(values)
    n = len(sorted_values)
    if n == 0:
        return 0
    if n % 2 == 0:
        return (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2
    else:
        return sorted_values[n//2]
```

### Supply Risk Assessment

Assign supply risk scores based on market factors.

```python
def calculate_supply_risk_score(vendor: Vendor, market_data: dict) -> float:
    """
    Calculate supply risk score (1-10 scale).

    Factors:
    - Number of alternative suppliers
    - Market concentration
    - Switching costs
    - Lead time
    - Product complexity
    - Geographic concentration
    - Financial stability

    Args:
        vendor: Vendor record
        market_data: Market analysis data

    Returns:
        Risk score (1 = low risk, 10 = high risk)
    """
    risk_factors = []

    # Factor 1: Alternative suppliers (40% weight)
    alternatives = market_data.get('alternative_count', 10)
    if alternatives < 2:
        risk_factors.append(10 * 0.4)  # Very high risk
    elif alternatives < 5:
        risk_factors.append(7 * 0.4)  # High risk
    elif alternatives < 10:
        risk_factors.append(4 * 0.4)  # Medium risk
    else:
        risk_factors.append(2 * 0.4)  # Low risk

    # Factor 2: Switching cost (30% weight)
    switching_cost = market_data.get('switching_cost', 'MEDIUM')
    switching_scores = {'LOW': 2, 'MEDIUM': 5, 'HIGH': 8, 'VERY_HIGH': 10}
    risk_factors.append(switching_scores.get(switching_cost, 5) * 0.3)

    # Factor 3: Lead time (20% weight)
    lead_time_days = market_data.get('lead_time_days', 30)
    if lead_time_days > 90:
        risk_factors.append(9 * 0.2)
    elif lead_time_days > 60:
        risk_factors.append(6 * 0.2)
    elif lead_time_days > 30:
        risk_factors.append(4 * 0.2)
    else:
        risk_factors.append(2 * 0.2)

    # Factor 4: Product complexity (10% weight)
    complexity = market_data.get('complexity', 'MEDIUM')
    complexity_scores = {'LOW': 2, 'MEDIUM': 5, 'HIGH': 8, 'VERY_HIGH': 10}
    risk_factors.append(complexity_scores.get(complexity, 5) * 0.1)

    return sum(risk_factors)
```

## Segmentation Analysis

### Distribution Across Quadrants

```python
def analyze_segmentation_distribution(segments: list[VendorSegment]) -> dict:
    """
    Analyze vendor and spend distribution across segments.

    Args:
        segments: List of vendor segments

    Returns:
        Distribution analysis
    """
    distribution = {
        'STRATEGIC': {'count': 0, 'spend': 0},
        'LEVERAGE': {'count': 0, 'spend': 0},
        'BOTTLENECK': {'count': 0, 'spend': 0},
        'NON_CRITICAL': {'count': 0, 'spend': 0}
    }

    total_vendors = len(segments)
    total_spend = sum(s.annual_spend for s in segments)

    for segment in segments:
        distribution[segment.segment]['count'] += 1
        distribution[segment.segment]['spend'] += segment.annual_spend

    # Calculate percentages
    for category in distribution:
        distribution[category]['vendor_pct'] = (
            distribution[category]['count'] / total_vendors * 100
        ) if total_vendors > 0 else 0

        distribution[category]['spend_pct'] = (
            distribution[category]['spend'] / total_spend * 100
        ) if total_spend > 0 else 0

    return {
        'distribution': distribution,
        'total_vendors': total_vendors,
        'total_spend': total_spend,
        'insights': generate_segmentation_insights(distribution)
    }

def generate_segmentation_insights(distribution: dict) -> list[str]:
    """Generate actionable insights from segmentation."""
    insights = []

    strategic_pct = distribution['STRATEGIC']['spend_pct']
    if strategic_pct > 60:
        insights.append(f'HIGH CONCENTRATION: {strategic_pct:.1f}% spend with strategic vendors - consider risk mitigation')

    non_critical_count = distribution['NON_CRITICAL']['count']
    if non_critical_count > 100:
        insights.append(f'CONSOLIDATION OPPORTUNITY: {non_critical_count} non-critical vendors - target for reduction')

    leverage_spend = distribution['LEVERAGE']['spend']
    if leverage_spend > 1000000:
        insights.append(f'NEGOTIATION OPPORTUNITY: ${leverage_spend:,.0f} with leverage vendors - aggressive bidding recommended')

    return insights
```

## Visualization

### Kraljic Matrix Chart

Recommended visualization for vendor segmentation:

```python
def prepare_kraljic_chart_data(segments: list[VendorSegment]) -> dict:
    """
    Prepare data for Kraljic matrix visualization.

    Returns data suitable for scatter plot:
    - X-axis: Supply Risk Score (1-10)
    - Y-axis: Annual Spend
    - Color: Segment category
    - Size: Bubble size by spend amount
    """
    chart_data = {
        'STRATEGIC': [],
        'LEVERAGE': [],
        'BOTTLENECK': [],
        'NON_CRITICAL': []
    }

    for segment in segments:
        chart_data[segment.segment].append({
            'x': segment.supply_risk_score,
            'y': segment.annual_spend,
            'vendor_name': segment.vendor_name,
            'size': segment.annual_spend / 1000  # Scale for bubble size
        })

    return chart_data
```

**Chart Specifications:**
- Type: Scatter plot with quadrants
- X-axis: Supply Risk (1-10)
- Y-axis: Annual Spend ($)
- Quadrant lines: X=6 (risk threshold), Y=median spend
- Colors: Strategic (red), Leverage (green), Bottleneck (yellow), Non-Critical (blue)
- Bubble size: Proportional to spend

## Best Practices

### Segmentation Process
1. **Calculate annual spend** by vendor (past 12 months)
2. **Assess supply risk** for each vendor (market analysis)
3. **Classify vendors** using Kraljic matrix
4. **Assign procurement strategies** by segment
5. **Review quarterly** and adjust classifications
6. **Track migrations** (vendors moving between segments)

### Risk Assessment
- Involve category managers in risk scoring
- Consider multiple risk factors (not just supplier count)
- Update risk scores when market conditions change
- Document risk assessment methodology
- Review strategic vendor risk annually

### Strategic Alignment
- Align procurement strategies with corporate goals
- Allocate resources proportionally (strategic vendors get most attention)
- Set KPIs by segment (e.g., strategic vendors: relationship score, leverage: cost reduction %)
- Report segmentation to executives quarterly

## Related Documentation

- **[Spend Analysis](spend-analysis.md)** - Calculate annual spend for segmentation
- **[Cost Optimization](cost-optimization.md)** - Apply strategies by segment
- **[Consolidation](../workflows/consolidation.md)** - Focus on non-critical vendors

---

*Based on: Perplexity research on Kraljic Portfolio Purchasing Model (1983), Profit Impact vs Supply Risk dimensions*
