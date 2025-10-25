# Custom Field Analysis for Vendor Cost Analytics

Workflows for discovering, analyzing, and leveraging NetSuite custom vendor fields in cost analytics.

## Overview

Custom vendor fields (custentity_*) often contain critical business metadata that enhances vendor cost analysis beyond standard fields.

**Common valuable custom fields:**
- Regional coding (custentity_region, custentity_territory)
- Payment preferences (custentity_payment_method, custentity_payment_terms)
- Risk classification (custentity_credit_rating, custentity_risk_level)
- Strategic categorization (custentity_vendor_tier, custentity_strategic_vendor)
- Diversity attributes (custentity_minority_owned, custentity_small_business)

**Analytics applications:**
- Spend segmentation by region/territory
- Payment term optimization
- Risk-based vendor consolidation
- Strategic vendor identification
- Diversity spend reporting

---

## Workflow 1: Custom Field Discovery

### List All Custom Fields

```python
from vendor_analysis.db.query_helpers import CustomFieldQuery

def discover_custom_fields(session):
    """Discover all custom fields in vendor data

    Returns:
        Dict mapping field names to vendor counts
    """
    fields = CustomFieldQuery.list_all_custom_fields(session)

    # Sort by popularity
    sorted_fields = sorted(fields.items(), key=lambda x: x[1], reverse=True)

    print("Custom Vendor Fields:")
    print("=" * 80)
    for field_name, count in sorted_fields:
        percentage = (count / total_vendors) * 100
        print(f"{field_name:40} {count:5} vendors ({percentage:5.1f}%)")

    return fields

# Example output:
# custentity_region                        5000 vendors (100.0%)
# custentity_payment_method                4800 vendors ( 96.0%)
# custentity_credit_rating                 4500 vendors ( 90.0%)
# custentity_vendor_tier                   3000 vendors ( 60.0%)
# custentity_old_field                      100 vendors (  2.0%)  ← Deprecated?
```

**Reference:** `/opt/ns/apps/vendor-analysis/src/vendor_analysis/db/query_helpers.py`

### Field Population Analysis

```python
def analyze_field_population(session):
    """Analyze custom field completeness"""
    fields = CustomFieldQuery.list_all_custom_fields(session)
    total_vendors = session.query(VendorRecord).count()

    # Categorize by population
    well_populated = {}  # > 90%
    partial = {}         # 50-90%
    sparse = {}          # < 50%

    for field_name, count in fields.items():
        percentage = (count / total_vendors) * 100

        if percentage >= 90:
            well_populated[field_name] = percentage
        elif percentage >= 50:
            partial[field_name] = percentage
        else:
            sparse[field_name] = percentage

    return {
        "well_populated": well_populated,
        "partial": partial,
        "sparse": sparse
    }
```

**Use case:** Identify which custom fields are reliable for analytics

---

## Workflow 2: Spend Segmentation by Custom Fields

### Regional Spend Analysis

```python
def analyze_spend_by_region(session):
    """Analyze vendor spend by region custom field

    Returns:
        DataFrame with spend by region
    """
    import pandas as pd

    # Query vendors with region custom field
    query = """
        SELECT
            v.id,
            v.company_name,
            v.custom_fields->'custentity_region'->>'value' as region,
            SUM(t.amount) as total_spend
        FROM vendors v
        JOIN transactions t ON t.vendor_id = v.id
        WHERE v.custom_fields->'custentity_region'->>'deprecated' = 'false'
        GROUP BY v.id, v.company_name, region
    """

    df = pd.read_sql(query, session.connection())

    # Aggregate by region
    regional_spend = df.groupby('region').agg({
        'total_spend': 'sum',
        'id': 'count'
    }).rename(columns={'id': 'vendor_count'})

    return regional_spend.sort_values('total_spend', ascending=False)
```

### Payment Method Analysis

```python
def analyze_by_payment_method(session):
    """Analyze spend and vendor count by payment method"""

    vendors = session.query(VendorRecord).all()

    # Extract payment methods from custom fields
    payment_methods = {}

    for vendor in vendors:
        if not vendor.custom_fields:
            continue

        payment = vendor.custom_fields.get('custentity_payment_method', {}).get('value')
        if not payment:
            continue

        if payment not in payment_methods:
            payment_methods[payment] = {"vendors": [], "total_spend": 0}

        payment_methods[payment]["vendors"].append(vendor.id)

    # Calculate spend per payment method
    for method, data in payment_methods.items():
        spend = session.query(func.sum(TransactionRecord.amount)).filter(
            TransactionRecord.vendor_id.in_(data["vendors"])
        ).scalar() or 0

        data["total_spend"] = spend
        data["vendor_count"] = len(data["vendors"])
        del data["vendors"]  # Don't need IDs in output

    return payment_methods

# Example output:
# {
#   "ACH": {"vendor_count": 2500, "total_spend": 12500000},
#   "Check": {"vendor_count": 1500, "total_spend": 3200000},
#   "Wire": {"vendor_count": 500, "total_spend": 8500000},
# }
```

---

## Workflow 3: Enhanced Duplicate Detection

Use custom fields to improve duplicate vendor detection.

### Include Custom Identifiers

```python
from difflib import SequenceMatcher

def find_duplicates_with_custom_fields(session, threshold=0.85):
    """Enhanced duplicate detection using custom fields

    Args:
        threshold: Similarity threshold (0-1)

    Returns:
        List of potential duplicate pairs
    """
    vendors = session.query(VendorRecord).filter_by(is_inactive=False).all()

    duplicates = []

    for i, vendor1 in enumerate(vendors):
        for vendor2 in vendors[i+1:]:
            # Name similarity
            name_sim = SequenceMatcher(
                None,
                vendor1.company_name.lower(),
                vendor2.company_name.lower()
            ).ratio()

            if name_sim < threshold:
                continue  # Names not similar enough

            # Check custom field matches
            custom_matches = compare_custom_fields(
                vendor1.custom_fields,
                vendor2.custom_fields
            )

            # Higher confidence if custom fields match
            if custom_matches > 0:
                duplicates.append({
                    "vendor1_id": vendor1.id,
                    "vendor2_id": vendor2.id,
                    "vendor1_name": vendor1.company_name,
                    "vendor2_name": vendor2.company_name,
                    "name_similarity": name_sim,
                    "custom_field_matches": custom_matches,
                    "confidence": min(name_sim + (custom_matches * 0.1), 1.0)
                })

    return duplicates

def compare_custom_fields(fields1, fields2):
    """Count matching custom field values

    Returns:
        Number of matching fields
    """
    if not fields1 or not fields2:
        return 0

    matches = 0
    for field in fields1:
        if field in fields2:
            val1 = fields1[field].get('value')
            val2 = fields2[field].get('value')
            if val1 and val2 and val1 == val2:
                matches += 1

    return matches
```

**Benefits:**
- Higher confidence duplicate detection
- Use region, account manager, etc. as signals
- Reduce false positives

---

## Workflow 4: Strategic Vendor Identification

### Identify High-Value Vendors Using Custom Fields

```python
def identify_strategic_vendors(session):
    """Identify strategic vendors using custom fields and spend

    Strategic indicators:
    - High spend volume
    - Marked as strategic (custentity_vendor_tier)
    - High credit rating (custentity_credit_rating)
    - Long relationship (first_seen)
    """
    import pandas as pd

    query = """
        SELECT
            v.id,
            v.company_name,
            v.balance,
            v.custom_fields->'custentity_vendor_tier'->>'value' as tier,
            v.custom_fields->'custentity_credit_rating'->>'value' as rating,
            v.custom_fields->'custentity_strategic_vendor'->>'value' as strategic,
            SUM(t.amount) as total_spend,
            COUNT(t.id) as transaction_count
        FROM vendors v
        LEFT JOIN transactions t ON t.vendor_id = v.id
        GROUP BY v.id, v.company_name, v.balance, tier, rating, strategic
    """

    df = pd.read_sql(query, session.connection())

    # Score vendors
    df['strategic_score'] = 0

    # High spend
    df.loc[df['total_spend'] > df['total_spend'].quantile(0.9), 'strategic_score'] += 3

    # High tier
    df.loc[df['tier'].isin(['Tier 1', 'Strategic']), 'strategic_score'] += 2

    # High credit rating
    df.loc[df['rating'].isin(['A+', 'A']), 'strategic_score'] += 1

    # Explicitly marked strategic
    df.loc[df['strategic'] == 'true', 'strategic_score'] += 2

    # Return high-scoring vendors
    strategic = df[df['strategic_score'] >= 4].sort_values('total_spend', ascending=False)

    return strategic[['id', 'company_name', 'total_spend', 'tier', 'rating', 'strategic_score']]
```

---

## Workflow 5: Diversity Spend Reporting

```python
def diversity_spend_report(session):
    """Generate diversity spend report using custom fields"""

    diversity_fields = [
        'custentity_minority_owned',
        'custentity_woman_owned',
        'custentity_veteran_owned',
        'custentity_small_business'
    ]

    report = {}

    for field in diversity_fields:
        # Query vendors with this diversity classification
        vendors = CustomFieldQuery.get_vendor_by_custom_field(
            session, field, 'true'
        )

        vendor_ids = [v.id for v in vendors]

        # Calculate total spend
        total_spend = session.query(func.sum(TransactionRecord.amount)).filter(
            TransactionRecord.vendor_id.in_(vendor_ids)
        ).scalar() or 0

        report[field] = {
            "vendor_count": len(vendors),
            "total_spend": total_spend
        }

    return report

# Example output:
# {
#   "custentity_minority_owned": {"vendor_count": 150, "total_spend": 2500000},
#   "custentity_woman_owned": {"vendor_count": 80, "total_spend": 1200000},
#   "custentity_veteran_owned": {"vendor_count": 45, "total_spend": 800000},
#   "custentity_small_business": {"vendor_count": 200, "total_spend": 3500000}
# }
```

---

## Related Patterns

**This Skill:**
- [integrations/netsuite.md](../integrations/netsuite.md#custom-vendor-fields) - NetSuite custom field basics
- [reference/data-quality.md](../reference/data-quality.md) - Custom field quality checks

**NetSuite Developer Skill:**
- `patterns/custom-fields.md` - Field classification and discovery

**Python CLI Engineering Skill:**
- `patterns/postgresql-jsonb.md` - JSONB query patterns

**Reference Implementation:**
- `/opt/ns/apps/vendor-analysis/src/vendor_analysis/db/query_helpers.py` - Custom field queries
- `/opt/ns/apps/vendor-analysis/src/vendor_analysis/analysis/vendors.py` - Vendor analytics

---

## Summary

**Key Points:**

1. **Discover custom fields** - Use list_all_custom_fields() to see what's available
2. **Check field population** - Analyze completeness before relying on fields
3. **Segment spend** - Group by region, payment method, vendor tier
4. **Enhance duplicate detection** - Use custom identifiers for matching
5. **Strategic identification** - Combine spend with custom field metadata
6. **Diversity reporting** - Leverage diversity classification fields

**Custom fields often contain the most valuable vendor metadata for advanced analytics beyond basic spend analysis.**
