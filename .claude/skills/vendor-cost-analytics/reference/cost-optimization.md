# Cost Optimization

Vendor consolidation savings calculation, payment terms negotiation, volume discounts, and price variance detection.

## Overview

Cost optimization identifies procurement savings opportunities through vendor consolidation, payment terms improvement, and contract compliance.

**Typical Savings Opportunities:**
- Vendor consolidation: 3-7% of addressable spend
- Payment terms optimization: 0.5-2% annual savings
- Volume discount capture: 2-5% on consolidated categories
- Contract compliance: 1-3% by enforcing contracted rates
- Maverick spend elimination: 5-15% on off-contract purchases

**Data Requirements:**
- Vendor master data (company name, payment terms, contracts)
- Transaction history (amounts, dates, categories)
- Contract data (rates, terms, volume commitments)
- Current pricing (unit prices, discounts)

## Vendor Consolidation Savings

### Calculation Method

Estimate savings from consolidating duplicate or similar vendors.

```python
from dataclasses import dataclass

@dataclass
class ConsolidationSavings:
    """Vendor consolidation savings analysis."""
    duplicate_vendor_count: int
    total_addressable_spend: float
    estimated_savings: float
    savings_percent: float
    volume_discount_potential: float
    overhead_reduction: float

def calculate_consolidation_savings(
    duplicate_pairs: list[DuplicatePair],
    vendor_spend: dict[str, float],
    baseline_discount: float = 0.03  # 3% baseline
) -> ConsolidationSavings:
    """
    Calculate potential savings from vendor consolidation.

    Args:
        duplicate_pairs: List of duplicate vendor pairs
        vendor_spend: Vendor ID -> annual spend mapping
        baseline_discount: Assumed discount from consolidation (default 3%)

    Returns:
        ConsolidationSavings analysis
    """
    # Calculate addressable spend (spend with duplicate vendors)
    affected_vendors = set()
    for pair in duplicate_pairs:
        affected_vendors.add(pair.vendor_1_id)
        affected_vendors.add(pair.vendor_2_id)

    addressable_spend = sum(
        vendor_spend.get(vendor_id, 0)
        for vendor_id in affected_vendors
    )

    # Base savings: addressable spend * baseline discount
    base_savings = addressable_spend * baseline_discount

    # Volume discount tier benefits
    volume_discount = calculate_volume_discount_benefit(
        duplicate_pairs,
        vendor_spend
    )

    # Overhead reduction (processing costs)
    overhead_reduction = len(duplicate_pairs) * COST_PER_VENDOR_ANNUALLY  # ~$500-1000/vendor

    total_savings = base_savings + volume_discount + overhead_reduction

    return ConsolidationSavings(
        duplicate_vendor_count=len(affected_vendors),
        total_addressable_spend=addressable_spend,
        estimated_savings=total_savings,
        savings_percent=(total_savings / addressable_spend * 100) if addressable_spend > 0 else 0,
        volume_discount_potential=volume_discount,
        overhead_reduction=overhead_reduction
    )

def calculate_volume_discount_benefit(
    duplicate_pairs: list[DuplicatePair],
    vendor_spend: dict[str, float]
) -> float:
    """
    Calculate additional savings from volume discount tiers.

    Example: Two vendors with $50K each → Consolidate to $100K → Higher tier
    """
    additional_savings = 0

    for pair in duplicate_pairs:
        spend_1 = vendor_spend.get(pair.vendor_1_id, 0)
        spend_2 = vendor_spend.get(pair.vendor_2_id, 0)
        combined_spend = spend_1 + spend_2

        # Discount tiers (example thresholds)
        old_discount = get_tier_discount(spend_1) + get_tier_discount(spend_2)
        new_discount = get_tier_discount(combined_spend)

        # Additional discount from consolidation
        discount_improvement = new_discount - old_discount
        additional_savings += combined_spend * discount_improvement

    return additional_savings

def get_tier_discount(annual_spend: float) -> float:
    """Get discount tier based on annual spend."""
    if annual_spend >= 500000:
        return 0.10  # 10% for $500K+
    elif annual_spend >= 250000:
        return 0.07  # 7% for $250K+
    elif annual_spend >= 100000:
        return 0.05  # 5% for $100K+
    elif annual_spend >= 50000:
        return 0.03  # 3% for $50K+
    else:
        return 0.00  # No discount

# Constants
COST_PER_VENDOR_ANNUALLY = 750  # Administrative overhead per vendor
```

## Payment Terms Optimization

### Early Payment Discount Analysis

Calculate ROI of taking early payment discounts (e.g., "2/10 Net 30").

```python
@dataclass
class PaymentTermsAnalysis:
    """Payment terms optimization analysis."""
    current_average_dpo: float  # Days payable outstanding
    discount_opportunities: list[dict]
    annual_discount_capture: float
    effective_interest_rate: float
    cash_flow_impact: float

def analyze_payment_terms(
    vendors: list[Vendor],
    annual_spend_by_vendor: dict[str, float]
) -> PaymentTermsAnalysis:
    """
    Analyze payment terms optimization opportunities.

    Args:
        vendors: List of vendor records with terms
        annual_spend_by_vendor: Vendor ID -> annual spend

    Returns:
        Payment terms analysis
    """
    discount_opportunities = []
    total_discount_capture = 0

    for vendor in vendors:
        if not vendor.terms:
            continue

        # Parse terms (e.g., "2/10 Net 30")
        discount_info = parse_payment_terms(vendor.terms)
        if not discount_info:
            continue

        annual_spend = annual_spend_by_vendor.get(vendor.id, 0)

        # Calculate annual discount available
        discount_amount = annual_spend * discount_info['discount_percent']

        # Calculate effective interest rate
        days_early = discount_info['net_days'] - discount_info['discount_days']
        annual_rate = (discount_info['discount_percent'] / (1 - discount_info['discount_percent'])) * (365 / days_early)

        discount_opportunities.append({
            'vendor_id': vendor.id,
            'vendor_name': vendor.company_name,
            'annual_spend': annual_spend,
            'terms': vendor.terms,
            'discount_amount': discount_amount,
            'effective_rate': annual_rate * 100,  # As percentage
            'recommendation': 'TAKE' if annual_rate > 0.15 else 'EVALUATE'  # >15% APR = take
        })

        total_discount_capture += discount_amount

    # Calculate current DPO
    current_dpo = calculate_current_dpo(vendors, annual_spend_by_vendor)

    return PaymentTermsAnalysis(
        current_average_dpo=current_dpo,
        discount_opportunities=discount_opportunities,
        annual_discount_capture=total_discount_capture,
        effective_interest_rate=0,  # Weighted average
        cash_flow_impact=-total_discount_capture  # Negative = cash outflow
    )

def parse_payment_terms(terms_string: str) -> dict | None:
    """
    Parse payment terms string.

    Examples:
        "2/10 Net 30" → 2% discount if paid in 10 days, else due in 30 days
        "Net 30" → No discount, due in 30 days
    """
    import re

    # Match discount terms: "2/10 Net 30"
    match = re.match(r'(\d+)/(\d+)\s+Net\s+(\d+)', terms_string, re.IGNORECASE)
    if match:
        return {
            'discount_percent': float(match.group(1)) / 100,
            'discount_days': int(match.group(2)),
            'net_days': int(match.group(3))
        }

    return None

def calculate_current_dpo(
    vendors: list[Vendor],
    annual_spend: dict[str, float]
) -> float:
    """Calculate weighted average days payable outstanding."""
    total_spend = sum(annual_spend.values())
    weighted_dpo = 0

    for vendor in vendors:
        vendor_spend = annual_spend.get(vendor.id, 0)
        weight = vendor_spend / total_spend if total_spend > 0 else 0

        # Extract net days from terms
        dpo = extract_net_days(vendor.terms) or 30  # Default 30
        weighted_dpo += dpo * weight

    return weighted_dpo

def extract_net_days(terms_string: str | None) -> int | None:
    """Extract net days from payment terms."""
    if not terms_string:
        return None

    import re
    match = re.search(r'Net\s+(\d+)', terms_string, re.IGNORECASE)
    return int(match.group(1)) if match else None
```

## Price Variance Detection

### Identify Off-Contract Pricing

Detect transactions where pricing exceeds contracted rates.

```python
@dataclass
class PriceVariance:
    """Price variance for a transaction."""
    transaction_id: str
    vendor_id: str
    vendor_name: str
    item_id: str
    contracted_price: float
    actual_price: float
    variance_amount: float
    variance_percent: float

def detect_price_variances(
    transactions: list[Transaction],
    contracted_rates: dict[tuple[str, str], float],  # (vendor_id, item_id) -> rate
    tolerance: float = 0.05  # 5% tolerance
) -> list[PriceVariance]:
    """
    Identify transactions exceeding contracted rates.

    Args:
        transactions: List of purchase transactions
        contracted_rates: Mapping of (vendor_id, item_id) to contracted price
        tolerance: Acceptable variance (0.05 = 5%)

    Returns:
        List of price variances
    """
    variances = []

    for txn in transactions:
        contract_key = (txn.vendor_id, txn.item_id)

        if contract_key not in contracted_rates:
            continue  # No contract for this item/vendor

        contracted_price = contracted_rates[contract_key]
        actual_price = txn.unit_price

        # Calculate variance
        variance_amount = actual_price - contracted_price
        variance_percent = variance_amount / contracted_price if contracted_price > 0 else 0

        # Flag if exceeds tolerance
        if variance_percent > tolerance:
            variances.append(PriceVariance(
                transaction_id=txn.id,
                vendor_id=txn.vendor_id,
                vendor_name=txn.vendor_name,
                item_id=txn.item_id,
                contracted_price=contracted_price,
                actual_price=actual_price,
                variance_amount=variance_amount,
                variance_percent=variance_percent
            ))

    # Sort by variance amount descending (biggest issues first)
    variances.sort(key=lambda v: v.variance_amount, reverse=True)

    return variances
```

## Volume Discount Analysis

### Calculate Unrealized Volume Discounts

Identify missed savings from not meeting volume commitments.

```python
def analyze_volume_discount_opportunity(
    vendor_spend: dict[str, float],
    vendor_contracts: dict[str, VendorContract]
) -> list[dict]:
    """
    Identify volume discount opportunities.

    Args:
        vendor_spend: Vendor ID -> annual spend
        vendor_contracts: Vendor ID -> contract details

    Returns:
        List of volume discount opportunities
    """
    opportunities = []

    for vendor_id, annual_spend in vendor_spend.items():
        contract = vendor_contracts.get(vendor_id)
        if not contract or not contract.volume_tiers:
            continue

        # Find current tier
        current_tier = get_current_tier(annual_spend, contract.volume_tiers)

        # Find next tier
        next_tier = get_next_tier(annual_spend, contract.volume_tiers)

        if next_tier:
            additional_spend_needed = next_tier['threshold'] - annual_spend
            discount_improvement = next_tier['discount'] - current_tier['discount']
            annual_savings = next_tier['threshold'] * discount_improvement

            # ROI of reaching next tier
            roi = annual_savings / additional_spend_needed if additional_spend_needed > 0 else 0

            opportunities.append({
                'vendor_id': vendor_id,
                'current_spend': annual_spend,
                'current_discount': current_tier['discount'] * 100,
                'next_tier_threshold': next_tier['threshold'],
                'next_tier_discount': next_tier['discount'] * 100,
                'additional_spend_needed': additional_spend_needed,
                'annual_savings': annual_savings,
                'roi': roi * 100,
                'recommendation': 'PURSUE' if roi > 0.20 else 'MONITOR'  # >20% ROI
            })

    # Sort by annual savings potential
    opportunities.sort(key=lambda o: o['annual_savings'], reverse=True)

    return opportunities

def get_current_tier(spend: float, tiers: list[dict]) -> dict:
    """Get current volume discount tier."""
    applicable_tier = tiers[0]  # Lowest tier

    for tier in sorted(tiers, key=lambda t: t['threshold']):
        if spend >= tier['threshold']:
            applicable_tier = tier
        else:
            break

    return applicable_tier

def get_next_tier(spend: float, tiers: list[dict]) -> dict | None:
    """Get next available volume discount tier."""
    for tier in sorted(tiers, key=lambda t: t['threshold']):
        if tier['threshold'] > spend:
            return tier

    return None  # Already at highest tier
```

## Contract Compliance Checking

### Enforce Contracted Rates

Identify purchases outside established contracts.

```python
def check_contract_compliance(
    transactions: list[Transaction],
    approved_vendors: set[str],
    contracted_items: dict[str, str],  # item_id -> vendor_id
    contracted_rates: dict[tuple[str, str], float]  # (vendor, item) -> rate
) -> dict:
    """
    Check transaction compliance with contracts.

    Args:
        transactions: Purchase transactions
        approved_vendors: Set of approved vendor IDs
        contracted_items: Items that should be purchased from specific vendors
        contracted_rates: Contracted pricing

    Returns:
        Compliance analysis
    """
    compliance = {
        'compliant': [],
        'off_vendor': [],  # Bought from wrong vendor
        'off_contract': [],  # No contract exists
        'price_variance': [],  # Exceeds contracted price
        'total_compliant_spend': 0,
        'total_non_compliant_spend': 0
    }

    for txn in transactions:
        # Check 1: Vendor approval
        if txn.vendor_id not in approved_vendors:
            compliance['off_vendor'].append(txn)
            compliance['total_non_compliant_spend'] += txn.amount
            continue

        # Check 2: Item should be from specific vendor
        if txn.item_id in contracted_items:
            contracted_vendor = contracted_items[txn.item_id]
            if txn.vendor_id != contracted_vendor:
                compliance['off_vendor'].append(txn)
                compliance['total_non_compliant_spend'] += txn.amount
                continue

        # Check 3: Price compliance
        contract_key = (txn.vendor_id, txn.item_id)
        if contract_key in contracted_rates:
            contracted_price = contracted_rates[contract_key]
            if txn.unit_price > contracted_price * 1.05:  # 5% tolerance
                compliance['price_variance'].append(txn)
                compliance['total_non_compliant_spend'] += txn.amount
                continue
        else:
            # No contract for this item
            compliance['off_contract'].append(txn)
            compliance['total_non_compliant_spend'] += txn.amount
            continue

        # Compliant transaction
        compliance['compliant'].append(txn)
        compliance['total_compliant_spend'] += txn.amount

    return compliance
```

## Maverick Spend Identification

### Detect Off-Contract Purchases

Identify spend outside approved vendors and contracts.

```python
def calculate_maverick_spend(
    total_spend: float,
    compliant_spend: float
) -> dict:
    """
    Calculate maverick spend metrics.

    Maverick spend = purchases outside established contracts or approved vendors.

    Args:
        total_spend: Total procurement spend
        compliant_spend: Spend with approved vendors at contracted rates

    Returns:
        Maverick spend analysis
    """
    maverick_spend = total_spend - compliant_spend
    maverick_rate = (maverick_spend / total_spend * 100) if total_spend > 0 else 0

    # Estimate savings opportunity (assume 10% savings on maverick spend if brought under contract)
    estimated_savings = maverick_spend * 0.10

    return {
        'total_spend': total_spend,
        'compliant_spend': compliant_spend,
        'maverick_spend': maverick_spend,
        'maverick_rate': maverick_rate,
        'estimated_savings': estimated_savings,
        'benchmark': get_maverick_benchmark(maverick_rate)
    }

def get_maverick_benchmark(maverick_rate: float) -> str:
    """Benchmark maverick spend rate."""
    if maverick_rate < 5:
        return 'EXCELLENT'
    elif maverick_rate < 15:
        return 'GOOD'
    elif maverick_rate < 30:
        return 'NEEDS_IMPROVEMENT'
    else:
        return 'CRITICAL'
```

## Consolidation Prioritization

### Rank Consolidation Opportunities

Prioritize vendor consolidation by potential savings.

```python
@dataclass
class ConsolidationOpportunity:
    """Single vendor consolidation opportunity."""
    vendor_1_id: str
    vendor_1_name: str
    vendor_2_id: str
    vendor_2_name: str
    combined_spend: float
    estimated_savings: float
    confidence_score: float  # Duplicate detection confidence
    priority_score: float  # Overall priority

def prioritize_consolidation_opportunities(
    duplicate_pairs: list[DuplicatePair],
    vendor_spend: dict[str, float],
    vendor_names: dict[str, str]
) -> list[ConsolidationOpportunity]:
    """
    Rank consolidation opportunities by potential savings and confidence.

    Args:
        duplicate_pairs: Detected duplicate vendors
        vendor_spend: Annual spend by vendor
        vendor_names: Vendor ID to name mapping

    Returns:
        Sorted list of consolidation opportunities (highest priority first)
    """
    opportunities = []

    for pair in duplicate_pairs:
        spend_1 = vendor_spend.get(pair.vendor_1_id, 0)
        spend_2 = vendor_spend.get(pair.vendor_2_id, 0)
        combined_spend = spend_1 + spend_2

        # Estimate savings (3% baseline + volume discount benefit)
        base_savings = combined_spend * 0.03
        volume_benefit = calculate_volume_discount_benefit([pair], vendor_spend)
        total_savings = base_savings + volume_benefit

        # Priority score (savings * confidence)
        priority = total_savings * pair.similarity_score

        opportunities.append(ConsolidationOpportunity(
            vendor_1_id=pair.vendor_1_id,
            vendor_1_name=vendor_names.get(pair.vendor_1_id, 'Unknown'),
            vendor_2_id=pair.vendor_2_id,
            vendor_2_name=vendor_names.get(pair.vendor_2_id, 'Unknown'),
            combined_spend=combined_spend,
            estimated_savings=total_savings,
            confidence_score=pair.similarity_score,
            priority_score=priority
        ))

    # Sort by priority score descending
    opportunities.sort(key=lambda o: o.priority_score, reverse=True)

    return opportunities
```

## Best Practices

### Consolidation Execution
- Start with high-confidence duplicates (>0.90 similarity)
- Verify operational impact before merging
- Consider contract terms and relationships
- Consolidate in phases (don't merge all at once)
- Track actual savings vs estimates

### Payment Terms Strategy
- Take early payment discounts with effective APR >15%
- Negotiate extended terms with high-volume vendors
- Model cash flow impact before changing terms
- Monitor working capital metrics (DPO, cash conversion cycle)
- Balance discount capture vs. cash flow needs

### Price Variance Management
- Set tolerance thresholds (typically 5%)
- Investigate variances >$1000 or >10%
- Enforce contract compliance through approval workflows
- Renegotiate contracts when market prices drop
- Track variance trends over time

### Savings Validation
- Model savings before implementation
- Track actual savings post-consolidation
- Account for one-time costs (vendor onboarding, system changes)
- Monitor quality and service levels post-consolidation
- Report savings to stakeholders monthly

## Related Documentation

- **[Duplicate Detection](duplicate-detection.md)** - Fuzzy matching algorithms
- **[Spend Analysis](spend-analysis.md)** - Pareto analysis, vendor concentration
- **[Vendor Segmentation](vendor-segmentation.md)** - Kraljic matrix
- **[Consolidation Workflow](../workflows/consolidation.md)** - Step-by-step process

---

*Generic cost optimization formulas applicable to any procurement organization*
