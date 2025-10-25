# Vendor Consolidation Workflow

Step-by-step process for consolidating duplicate vendors and capturing savings.

## Overview

Vendor consolidation reduces vendor count, captures volume discounts, and lowers administrative overhead.

**Typical Consolidation Project:**
- Timeline: 3-6 months
- Scope: 5-15% of vendor base
- Savings: 3-7% of addressable spend
- Effort: 2-4 FTE weeks (analysis, validation, execution, monitoring)

**Success Metrics:**
- Vendor count reduction: 10-30%
- Spend consolidation: $500K-$5M+
- Realized savings: 3-7%
- Process efficiency: 20-40% fewer invoices processed

## Workflow Steps

### Step 1: Identify Duplicate Vendors

Run duplicate detection analysis to identify consolidation candidates.

```python
from vendor_analysis.analysis.duplicates import detect_duplicate_vendors

# Run duplicate detection
duplicate_pairs = detect_duplicate_vendors(
    session=db_session,
    settings=app_settings,
    threshold=0.85  # Moderate threshold
)

# Categorize by confidence
high_confidence = [d for d in duplicate_pairs if d.similarity_score >= 0.95]
medium_confidence = [d for d in duplicate_pairs if 0.85 <= d.similarity_score < 0.95]
low_confidence = [d for d in duplicate_pairs if d.similarity_score < 0.85]

print(f"High confidence: {len(high_confidence)} pairs")
print(f"Medium confidence: {len(medium_confidence)} pairs")
print(f"Low confidence: {len(low_confidence)} pairs")
```

**Prioritization:**
- Start with high-confidence duplicates (>0.95 similarity)
- Focus on high-spend vendors first (Pareto principle)
- Quick wins: Same name variants ("ABC Corp" vs "ABC Corporation")

### Step 2: Analyze Spend Impact

Calculate spend across duplicate pairs to estimate consolidation value.

```python
def analyze_consolidation_impact(
    duplicate_pairs: list[DuplicatePair],
    vendor_spend: dict[str, float],
    transactions: list[Transaction]
) -> list[dict]:
    """
    Analyze financial impact of consolidation.

    Args:
        duplicate_pairs: Detected duplicates
        vendor_spend: Annual spend by vendor
        transactions: Transaction history

    Returns:
        Consolidation analysis by pair
    """
    analysis = []

    for pair in duplicate_pairs:
        spend_1 = vendor_spend.get(pair.vendor_1_id, 0)
        spend_2 = vendor_spend.get(pair.vendor_2_id, 0)
        combined_spend = spend_1 + spend_2

        # Get transaction counts
        txn_1 = len([t for t in transactions if t.vendor_id == pair.vendor_1_id])
        txn_2 = len([t for t in transactions if t.vendor_id == pair.vendor_2_id])

        # Estimate savings (3% baseline + volume discount)
        baseline_savings = combined_spend * 0.03
        volume_discount = calculate_volume_tier_benefit(spend_1, spend_2)
        overhead_savings = 750  # Administrative cost per vendor annually

        total_savings = baseline_savings + volume_discount + overhead_savings

        analysis.append({
            'vendor_1_id': pair.vendor_1_id,
            'vendor_1_name': pair.vendor_1_name,
            'vendor_1_spend': spend_1,
            'vendor_1_transactions': txn_1,
            'vendor_2_id': pair.vendor_2_id,
            'vendor_2_name': pair.vendor_2_name,
            'vendor_2_spend': spend_2,
            'vendor_2_transactions': txn_2,
            'combined_spend': combined_spend,
            'estimated_savings': total_savings,
            'similarity': pair.similarity_score,
            'priority': total_savings * pair.similarity_score  # Weighted priority
        })

    # Sort by priority descending
    analysis.sort(key=lambda a: a['priority'], reverse=True)

    return analysis

def calculate_volume_tier_benefit(spend_1: float, spend_2: float) -> float:
    """Calculate additional discount from volume consolidation."""
    # Simple tier model
    def get_discount(spend):
        if spend >= 500000: return 0.10
        if spend >= 250000: return 0.07
        if spend >= 100000: return 0.05
        if spend >= 50000: return 0.03
        return 0.00

    combined_spend = spend_1 + spend_2
    old_discount = spend_1 * get_discount(spend_1) + spend_2 * get_discount(spend_2)
    new_discount = combined_spend * get_discount(combined_spend)

    return new_discount - old_discount
```

### Step 3: Validate Duplicates

Manual review to confirm true duplicates vs legitimate separate entities.

**Validation Checklist:**
- [ ] Same legal entity? (check tax ID, business registration)
- [ ] Same physical location? (check address)
- [ ] Same contact person? (check email, phone)
- [ ] Same services/products? (check purchase history)
- [ ] Active contracts with both? (review contract terms)
- [ ] Different divisions intentional? (check with stakeholders)

**Decision Matrix:**

| Evidence | Same Entity | Different Entity |
|----------|-------------|------------------|
| Same tax ID | Yes | Investigate |
| Same address + phone | Likely yes | Verify |
| Same email domain | Possible | Check further |
| Different cities | Investigate | Likely no |
| Different contracts | Investigate | Likely no |

**Validation Output:**
- **MERGE** - Confirmed duplicate, proceed with consolidation
- **KEEP_SEPARATE** - Different entities, do not merge
- **INVESTIGATE** - Need more information

### Step 4: Calculate Savings

Generate detailed savings estimate for executive approval.

```python
@dataclass
class ConsolidationBusinessCase:
    """Business case for vendor consolidation."""
    duplicate_pairs_identified: int
    pairs_confirmed_for_merge: int
    total_addressable_spend: float
    one_time_costs: float
    annual_savings: float
    payback_period_months: float
    three_year_npv: float

def build_consolidation_business_case(
    confirmed_merges: list[dict],
    one_time_cost_per_vendor: float = 2000  # Onboarding, system updates, etc.
) -> ConsolidationBusinessCase:
    """
    Build financial business case for consolidation.

    Args:
        confirmed_merges: List of confirmed duplicate pairs to merge
        one_time_cost_per_vendor: One-time cost to execute merger

    Returns:
        Business case with ROI analysis
    """
    total_spend = sum(m['combined_spend'] for m in confirmed_merges)
    annual_savings = sum(m['estimated_savings'] for m in confirmed_merges)
    one_time_costs = len(confirmed_merges) * one_time_cost_per_vendor

    # Payback period
    payback_months = (one_time_costs / annual_savings * 12) if annual_savings > 0 else 999

    # 3-year NPV (simple calculation, 10% discount rate)
    year_1 = annual_savings - one_time_costs
    year_2 = annual_savings / 1.10
    year_3 = annual_savings / (1.10 ** 2)
    three_year_npv = year_1 + year_2 + year_3

    return ConsolidationBusinessCase(
        duplicate_pairs_identified=len(confirmed_merges),
        pairs_confirmed_for_merge=len(confirmed_merges),
        total_addressable_spend=total_spend,
        one_time_costs=one_time_costs,
        annual_savings=annual_savings,
        payback_period_months=payback_months,
        three_year_npv=three_year_npv
    )
```

### Step 5: Execute Consolidation

Consolidate vendor records and update transaction history.

**Execution Checklist:**
1. **Select master vendor** (keep vendor with more transactions or better data quality)
2. **Notify stakeholders** (AP team, procurement, business users)
3. **Update ERP master data** (mark duplicate as inactive, add alias)
4. **Transfer outstanding balances** (if applicable)
5. **Update contracts** (consolidate under master vendor)
6. **Communicate to vendor** (provide single remittance address, AP contact)
7. **Update payment files** (bank account, payment terms)
8. **Monitor first 90 days** (ensure no payment disruptions)

**System Updates:**
```python
def execute_vendor_merge(
    master_vendor_id: str,
    duplicate_vendor_id: str,
    db_session
):
    """
    Execute vendor merge in local database.

    Note: This is for local analytics database only.
    ERP updates must be done manually to prevent data corruption.
    """
    # Mark duplicate as merged
    db_session.execute(
        update(VendorRecord)
        .where(VendorRecord.id == duplicate_vendor_id)
        .values(
            is_inactive=True,
            merged_into=master_vendor_id,
            merge_date=datetime.now()
        )
    )

    # Reassign transactions (for analytics purposes)
    db_session.execute(
        update(TransactionRecord)
        .where(TransactionRecord.vendor_id == duplicate_vendor_id)
        .values(vendor_id=master_vendor_id)
    )

    db_session.commit()

    print(f"Merged vendor {duplicate_vendor_id} into {master_vendor_id}")
```

### Step 6: Track Savings

Monitor actual savings vs estimates.

```python
@dataclass
class ConsolidationResults:
    """Consolidation project results."""
    vendors_merged: int
    estimated_savings: float
    actual_savings: float
    savings_variance: float
    invoice_count_reduction: int
    payment_processing_improvement: float

def track_consolidation_results(
    baseline_period: tuple[datetime, datetime],
    post_consolidation_period: tuple[datetime, datetime],
    merged_vendor_ids: list[str]
) -> ConsolidationResults:
    """
    Track actual vs estimated savings.

    Args:
        baseline_period: Pre-consolidation period for comparison
        post_consolidation_period: Post-consolidation period
        merged_vendor_ids: List of vendor IDs that were consolidated

    Returns:
        Consolidation results analysis
    """
    # Calculate baseline metrics
    baseline_spend = calculate_spend_for_vendors(merged_vendor_ids, baseline_period)
    baseline_invoice_count = count_invoices_for_vendors(merged_vendor_ids, baseline_period)

    # Calculate post-consolidation metrics
    post_spend = calculate_spend_for_vendors(merged_vendor_ids, post_consolidation_period)
    post_invoice_count = count_invoices_for_vendors(merged_vendor_ids, post_consolidation_period)

    # Calculate savings
    actual_savings = baseline_spend - post_spend
    invoice_reduction = baseline_invoice_count - post_invoice_count

    return ConsolidationResults(
        vendors_merged=len(merged_vendor_ids),
        estimated_savings=0,  # From business case
        actual_savings=actual_savings,
        savings_variance=0,  # actual - estimated
        invoice_count_reduction=invoice_reduction,
        payment_processing_improvement=invoice_reduction * COST_PER_INVOICE  # ~$10-15 per invoice
    )
```

## Best Practices

### Planning Phase
- Start with high-confidence duplicates (>0.95 similarity)
- Focus on top 100 vendors first (80% of spend)
- Get stakeholder buy-in before execution
- Plan for 3-6 month project timeline
- Allocate dedicated project resources

### Validation Phase
- Manual review of all proposed mergers
- Verify with business users (not just data)
- Check contracts and commitments
- Consider operational impact (AP processing, purchasing)
- Document merge decisions and rationale

### Execution Phase
- Pilot with 5-10 vendors first
- Monitor for issues (payment delays, order errors)
- Communicate clearly to all stakeholders
- Execute in batches (not all at once)
- Maintain audit trail of all mergers

### Monitoring Phase
- Track savings monthly (first 12 months)
- Monitor service levels and quality
- Solicit feedback from AP and procurement
- Report results to executives quarterly
- Adjust future consolidation based on learnings

## Common Pitfalls

**Avoid These Mistakes:**
- Merging vendors without stakeholder validation
- Assuming all duplicates should be consolidated
- Ignoring contractual obligations
- Not communicating with vendors
- Failing to track actual savings
- Consolidating too quickly (causes operational disruption)

**Success Factors:**
- Strong executive sponsorship
- Cross-functional team (procurement, AP, IT)
- Clear communication plan
- Phased execution approach
- Continuous monitoring and adjustment

## Related Documentation

- **[Duplicate Detection](../reference/duplicate-detection.md)** - Fuzzy matching algorithms
- **[Cost Optimization](../reference/cost-optimization.md)** - Savings calculation
- **[Spend Analysis](../reference/spend-analysis.md)** - Impact analysis

---

*Generic vendor consolidation workflow applicable to any procurement organization*
