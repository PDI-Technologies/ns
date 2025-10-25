# Payment Terms Optimization Workflow

Analyzing and optimizing payment terms for cash flow improvement and early payment discount capture.

## Overview

Payment terms optimization balances cash flow management with discount capture opportunities.

**Common Payment Terms:**
- **Net 30** - Payment due in 30 days (no discount)
- **Net 60** - Payment due in 60 days (no discount)
- **2/10 Net 30** - 2% discount if paid within 10 days, otherwise due in 30 days
- **1/15 Net 45** - 1% discount if paid within 15 days, otherwise due in 45 days

**Optimization Goals:**
- Capture early payment discounts when ROI > 15% APR
- Extend terms with non-discount vendors (improve cash flow)
- Negotiate better terms with high-volume vendors
- Balance working capital vs discount capture

**Typical Savings:** 0.5-2% of annual spend

## Workflow Steps

### Step 1: Analyze Current Terms Distribution

Understand current payment terms across vendor base.

```python
def analyze_payment_terms_distribution(vendors: list[Vendor]) -> dict:
    """
    Analyze distribution of payment terms.

    Args:
        vendors: List of vendors with terms

    Returns:
        Terms distribution analysis
    """
    terms_distribution = {}
    total_vendors = len(vendors)

    for vendor in vendors:
        terms = vendor.terms or 'Unknown'

        if terms not in terms_distribution:
            terms_distribution[terms] = {
                'vendor_count': 0,
                'vendor_list': []
            }

        terms_distribution[terms]['vendor_count'] += 1
        terms_distribution[terms]['vendor_list'].append(vendor.id)

    # Calculate percentages
    for terms in terms_distribution:
        terms_distribution[terms]['percent'] = (
            terms_distribution[terms]['vendor_count'] / total_vendors * 100
        ) if total_vendors > 0 else 0

    # Sort by vendor count
    sorted_terms = sorted(
        terms_distribution.items(),
        key=lambda x: x[1]['vendor_count'],
        reverse=True
    )

    return dict(sorted_terms)

# Example output:
# {
#   'Net 30': {'vendor_count': 450, 'percent': 45.0},
#   'Net 60': {'vendor_count': 200, 'percent': 20.0},
#   '2/10 Net 30': {'vendor_count': 150, 'percent': 15.0},
#   'Net 15': {'vendor_count': 100, 'percent': 10.0},
#   'Unknown': {'vendor_count': 100, 'percent': 10.0}
# }
```

### Step 2: Identify Discount Opportunities

Find vendors offering early payment discounts.

```python
import re
from dataclasses import dataclass

@dataclass
class DiscountOpportunity:
    """Early payment discount opportunity."""
    vendor_id: str
    vendor_name: str
    annual_spend: float
    terms: str
    discount_percent: float
    discount_days: int
    net_days: int
    annual_discount_amount: float
    effective_apr: float
    recommendation: str

def identify_discount_opportunities(
    vendors: list[Vendor],
    vendor_spend: dict[str, float]
) -> list[DiscountOpportunity]:
    """
    Identify early payment discount opportunities.

    Args:
        vendors: Vendor list with terms
        vendor_spend: Annual spend by vendor

    Returns:
        List of discount opportunities sorted by potential savings
    """
    opportunities = []

    for vendor in vendors:
        if not vendor.terms:
            continue

        # Parse discount terms
        discount_info = parse_discount_terms(vendor.terms)
        if not discount_info:
            continue  # No discount available

        annual_spend = vendor_spend.get(vendor.id, 0)
        annual_discount = annual_spend * discount_info['discount_percent']

        # Calculate effective APR
        days_early = discount_info['net_days'] - discount_info['discount_days']
        effective_apr = (
            discount_info['discount_percent'] /
            (1 - discount_info['discount_percent'])
        ) * (365 / days_early)

        # Recommendation based on cost of capital
        cost_of_capital = 0.10  # 10% assumed cost of capital
        recommendation = 'TAKE' if effective_apr > cost_of_capital else 'DECLINE'

        opportunities.append(DiscountOpportunity(
            vendor_id=vendor.id,
            vendor_name=vendor.company_name or vendor.entity_id,
            annual_spend=annual_spend,
            terms=vendor.terms,
            discount_percent=discount_info['discount_percent'] * 100,
            discount_days=discount_info['discount_days'],
            net_days=discount_info['net_days'],
            annual_discount_amount=annual_discount,
            effective_apr=effective_apr * 100,
            recommendation=recommendation
        ))

    # Sort by annual discount amount descending
    opportunities.sort(key=lambda o: o.annual_discount_amount, reverse=True)

    return opportunities

def parse_discount_terms(terms: str) -> dict | None:
    """
    Parse discount payment terms.

    Format: "X/Y Net Z" where:
    - X = discount percent
    - Y = discount days
    - Z = net days

    Examples:
        "2/10 Net 30" → 2% if paid in 10 days, else due in 30
    """
    match = re.match(r'(\d+(?:\.\d+)?)/(\d+)\s+Net\s+(\d+)', terms, re.IGNORECASE)

    if match:
        return {
            'discount_percent': float(match.group(1)) / 100,
            'discount_days': int(match.group(2)),
            'net_days': int(match.group(3))
        }

    return None
```

### Step 3: Calculate Cash Flow Impact

Model cash flow impact of taking discounts vs extending terms.

```python
def calculate_cash_flow_impact(
    current_dpo: float,
    proposed_dpo: float,
    annual_spend: float
) -> dict:
    """
    Calculate cash flow impact of changing payment terms.

    Args:
        current_dpo: Current days payable outstanding
        proposed_dpo: Proposed DPO after term changes
        annual_spend: Total annual procurement spend

    Returns:
        Cash flow analysis
    """
    daily_spend = annual_spend / 365

    current_payables = current_dpo * daily_spend
    proposed_payables = proposed_dpo * daily_spend

    cash_flow_change = proposed_payables - current_payables

    return {
        'current_dpo': current_dpo,
        'proposed_dpo': proposed_dpo,
        'dpo_change_days': proposed_dpo - current_dpo,
        'current_payables_balance': current_payables,
        'proposed_payables_balance': proposed_payables,
        'cash_flow_impact': cash_flow_change,
        'impact_description': 'Cash released' if cash_flow_change < 0 else 'Cash required'
    }

# Example:
# Current DPO: 45 days
# Proposed DPO: 30 days (taking early discounts)
# Annual spend: $10M
# Result: Need $410K additional working capital
#         But saving $150K annually in discounts
#         Net benefit if discount rate > cost of capital
```

### Step 4: Negotiate Terms

Target vendors for payment terms improvement.

**Negotiation Targets:**

```python
def identify_negotiation_targets(
    vendors: list[Vendor],
    vendor_spend: dict[str, float],
    vendor_segments: dict[str, str]  # Vendor ID -> Kraljic segment
) -> list[dict]:
    """
    Identify vendors for payment terms negotiation.

    Targets:
    - High spend leverage vendors (negotiate for discounts)
    - Strategic vendors (negotiate for extended terms)

    Args:
        vendors: Vendor list
        vendor_spend: Annual spend by vendor
        vendor_segments: Kraljic segmentation

    Returns:
        Negotiation targets prioritized by potential impact
    """
    targets = []

    for vendor in vendors:
        annual_spend = vendor_spend.get(vendor.id, 0)
        segment = vendor_segments.get(vendor.id, 'NON_CRITICAL')
        current_terms = vendor.terms or 'Net 30'

        # Leverage vendors: Negotiate for discounts
        if segment == 'LEVERAGE' and annual_spend > 100000:
            if '/' not in current_terms:  # No discount currently
                potential_discount = annual_spend * 0.02  # Assume 2% achievable
                targets.append({
                    'vendor_id': vendor.id,
                    'vendor_name': vendor.company_name,
                    'annual_spend': annual_spend,
                    'segment': segment,
                    'current_terms': current_terms,
                    'proposed_terms': '2/10 Net 30',
                    'potential_savings': potential_discount,
                    'negotiation_priority': 'HIGH'
                })

        # Strategic vendors: Extend terms for cash flow
        if segment == 'STRATEGIC' and annual_spend > 500000:
            current_days = extract_net_days(current_terms) or 30
            if current_days < 60:
                proposed_days = 60
                cash_flow_benefit = annual_spend / 365 * (proposed_days - current_days)
                targets.append({
                    'vendor_id': vendor.id,
                    'vendor_name': vendor.company_name,
                    'annual_spend': annual_spend,
                    'segment': segment,
                    'current_terms': current_terms,
                    'proposed_terms': f'Net {proposed_days}',
                    'cash_flow_benefit': cash_flow_benefit,
                    'negotiation_priority': 'MEDIUM'
                })

    # Sort by priority and potential benefit
    targets.sort(key=lambda t: t.get('potential_savings', 0) + t.get('cash_flow_benefit', 0), reverse=True)

    return targets

def extract_net_days(terms: str | None) -> int | None:
    """Extract net days from payment terms."""
    if not terms:
        return None

    match = re.search(r'Net\s+(\d+)', terms, re.IGNORECASE)
    return int(match.group(1)) if match else None
```

### Step 5: Track Outcomes

Monitor payment term optimization results.

```python
@dataclass
class PaymentTermsResults:
    """Payment terms optimization results."""
    discounts_captured: float
    discounts_missed: float
    capture_rate: float
    average_dpo: float
    cash_flow_impact: float
    working_capital_change: float

def track_payment_terms_results(
    transactions: list[Transaction],
    vendors: list[Vendor]
) -> PaymentTermsResults:
    """
    Track payment terms optimization results.

    Args:
        transactions: Transaction history with payment dates
        vendors: Vendor list with terms

    Returns:
        Payment terms performance metrics
    """
    discounts_captured = 0
    discounts_missed = 0

    for txn in transactions:
        vendor = find_vendor(vendors, txn.vendor_id)
        if not vendor or not vendor.terms:
            continue

        discount_info = parse_discount_terms(vendor.terms)
        if not discount_info:
            continue

        # Check if discount was taken
        days_to_payment = (txn.payment_date - txn.invoice_date).days if txn.payment_date else None

        if days_to_payment and days_to_payment <= discount_info['discount_days']:
            # Discount captured
            discount_amount = txn.amount * discount_info['discount_percent']
            discounts_captured += discount_amount
        else:
            # Discount missed
            discount_amount = txn.amount * discount_info['discount_percent']
            discounts_missed += discount_amount

    capture_rate = (
        discounts_captured / (discounts_captured + discounts_missed) * 100
    ) if (discounts_captured + discounts_missed) > 0 else 0

    return PaymentTermsResults(
        discounts_captured=discounts_captured,
        discounts_missed=discounts_missed,
        capture_rate=capture_rate,
        average_dpo=calculate_average_dpo(transactions),
        cash_flow_impact=0,  # Calculate based on DPO change
        working_capital_change=0  # Payables balance change
    )
```

## Best Practices

### Discount Capture Strategy
- Take discounts with effective APR > cost of capital (typically >10-15%)
- Automate payment scheduling to hit discount windows
- Monitor discount capture rate monthly (target >95%)
- Flag missed discounts for process improvement

### Terms Negotiation
- Target high-spend leverage vendors for discounts
- Negotiate extended terms with strategic vendors (improve cash flow)
- Consolidate spend to qualify for better terms
- Review terms annually with top 20 vendors

### Cash Flow Management
- Model working capital impact before changing terms
- Balance discount capture vs cash flow needs
- Set payment policies by vendor segment
- Monitor DPO trends monthly

### Performance Monitoring
- Track discount capture rate by vendor
- Measure average DPO monthly
- Calculate working capital tied up in payables
- Report terms optimization savings quarterly

## Related Documentation

- **[Cost Optimization](../reference/cost-optimization.md)** - Payment terms ROI calculation
- **[Spend Analysis](../reference/spend-analysis.md)** - Vendor spend for prioritization
- **[Vendor Segmentation](../reference/vendor-segmentation.md)** - Segment-based strategies

---

*Generic payment terms optimization workflow for working capital and discount management*
