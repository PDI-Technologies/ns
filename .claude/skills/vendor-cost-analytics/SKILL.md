---
name: vendor-cost-analytics
description: Analyzes vendor spend, detects duplicates, identifies cost optimization opportunities, and provides procurement analytics methodologies. Use when analyzing vendor costs, consolidating suppliers, detecting duplicate vendors, optimizing payment terms, or building spend analytics dashboards. Covers fuzzy matching algorithms, Pareto analysis, spend segmentation, price variance detection, and vendor risk scoring.
---

# Vendor Cost Analytics

Specialized knowledge for vendor spend analysis, supplier consolidation, and procurement cost optimization.

## When to Use This Skill

Trigger this skill for:
- Vendor spend analysis and reporting
- Duplicate vendor detection
- Supplier consolidation opportunities
- Payment terms optimization
- Maverick spend identification
- Vendor master data cleansing
- Procurement analytics dashboards
- Cost trend analysis and forecasting

## Quick Start

### Basic Vendor Spend Analysis

```python
# Analyze top vendors by spend
def analyze_top_vendors(transactions: list[Transaction], top_n: int = 10):
    """Group by vendor, sum spend, sort descending."""
    vendor_totals = {}
    for txn in transactions:
        vendor_totals[txn.vendor_id] = vendor_totals.get(txn.vendor_id, 0) + txn.amount

    sorted_vendors = sorted(vendor_totals.items(), key=lambda x: x[1], reverse=True)
    return sorted_vendors[:top_n]
```

### Duplicate Vendor Detection

```python
from difflib import SequenceMatcher

def calculate_similarity(name1: str, name2: str) -> float:
    """Fuzzy string matching using SequenceMatcher."""
    return SequenceMatcher(None, name1.lower(), name2.lower()).ratio()

def find_duplicates(vendors: list[Vendor], threshold: float = 0.85):
    """Find vendor pairs with similarity >= threshold."""
    duplicates = []
    for i, v1 in enumerate(vendors):
        for v2 in vendors[i+1:]:
            sim = calculate_similarity(v1.name, v2.name)
            if sim >= threshold:
                duplicates.append((v1, v2, sim))
    return duplicates
```

## Core Analytics Methodologies

### Spend Analysis
→ **See**: [reference/spend-analysis.md](reference/spend-analysis.md)

Topics:
- Pareto analysis (80/20 rule)
- Spend segmentation (strategic, leverage, bottleneck, non-critical)
- Category spend analysis
- Vendor concentration risk

### Duplicate Detection
→ **See**: [reference/duplicate-detection.md](reference/duplicate-detection.md)

Algorithms:
- Fuzzy string matching (Levenshtein, SequenceMatcher)
- Token-based matching
- Phonetic matching (Soundex, Metaphone)
- Address normalization
- Tax ID validation

### Cost Optimization
→ **See**: [reference/cost-optimization.md](reference/cost-optimization.md)

Strategies:
- Vendor consolidation
- Payment terms negotiation
- Volume discounts
- Contract compliance
- Price variance detection

### Data Quality
→ **See**: [reference/data-quality.md](reference/data-quality.md)

Patterns:
- Vendor master data cleansing
- Address standardization
- Duplicate merge strategies
- Data validation rules

## Workflows

### Vendor Consolidation Analysis
→ **See**: [workflows/consolidation.md](workflows/consolidation.md)

Steps:
1. Identify duplicate vendors
2. Analyze spend across duplicates
3. Calculate consolidation savings
4. Generate merge recommendations

### Spend Dashboard Creation
→ **See**: [workflows/dashboard.md](workflows/dashboard.md)

Components:
- Top vendors by spend
- Spend by category
- Spend trends over time
- Maverick spend alerts
- Vendor concentration metrics

### Payment Terms Optimization
→ **See**: [workflows/payment-terms.md](workflows/payment-terms.md)

Analysis:
- Current terms distribution
- Early payment discount opportunities
- Cash flow impact modeling
- Terms negotiation targets

## Metrics and KPIs

### Key Metrics
- **Total Addressable Spend**: Sum of all vendor spend
- **Vendor Concentration**: % spend with top N vendors
- **Maverick Spend**: Spend outside contracts
- **Duplicate Rate**: % vendors that are duplicates
- **Average Payment Days**: Days payable outstanding (DPO)
- **Vendor Count**: Active vendor count
- **Spend per Vendor**: Average spend per vendor

### Benchmarks
- **Top 20% vendors**: Typically represent 80% of spend (Pareto)
- **Duplicate rate**: 5-15% in most organizations
- **Vendor consolidation savings**: 3-7% of addressable spend
- **Payment terms optimization**: 0.5-2% annual savings

## Integration Patterns

### ERP Data Extraction
**NetSuite**: See [integrations/netsuite.md](integrations/netsuite.md)
**SAP**: See [integrations/sap.md](integrations/sap.md)
**Oracle**: See [integrations/oracle.md](integrations/oracle.md)

### Visualization
**React Dashboard**: Use vendor spend charts, tables, filters
**Excel Reports**: Pivot tables, conditional formatting
**BI Tools**: Tableau, Power BI, Looker integrations

## Examples

### Complete Analysis Pipeline
→ **See**: [examples/full-pipeline.md](examples/full-pipeline.md)

End-to-end example:
1. Extract vendor data from ERP
2. Cleanse and standardize
3. Detect duplicates
4. Analyze spend patterns
5. Generate recommendations
6. Create executive dashboard

### Real-World Scenarios
→ **See**: [examples/scenarios.md](examples/scenarios.md)

- Reducing vendor count from 5,000 to 2,000
- Identifying $2M in consolidation savings
- Cleaning vendor master data (50% duplicate rate)
- Optimizing payment terms for cash flow

## Tools and Libraries

### Python
- **pandas**: Data manipulation and analysis
- **difflib**: String similarity (SequenceMatcher)
- **fuzzywuzzy**: Fuzzy string matching
- **sqlalchemy**: Database operations
- **numpy**: Numerical operations

### Visualization
- **matplotlib/seaborn**: Static charts
- **plotly**: Interactive dashboards
- **recharts**: React charts
- **shadcn/ui**: React components

## Reference Documentation

Complete documentation organized by topic:

- **Spend Analysis**: [reference/spend-analysis.md](reference/spend-analysis.md)
- **Duplicate Detection**: [reference/duplicate-detection.md](reference/duplicate-detection.md)
- **Cost Optimization**: [reference/cost-optimization.md](reference/cost-optimization.md)
- **Data Quality**: [reference/data-quality.md](reference/data-quality.md)
- **Payment Terms**: [reference/payment-terms.md](reference/payment-terms.md)
- **Vendor Segmentation**: [reference/vendor-segmentation.md](reference/vendor-segmentation.md)

## Best Practices

1. **Start with data quality** - Clean vendor master data first
2. **Use multiple matching algorithms** - Fuzzy + phonetic + address
3. **Set conservative thresholds** - 0.85+ for duplicate detection
4. **Validate savings** - Model before recommending consolidation
5. **Consider operational impact** - Not all duplicates should merge
6. **Track metrics over time** - Benchmark progress monthly
7. **Automate repetitive analysis** - Schedule regular reports

## Fail-Fast Considerations

When building vendor analytics applications:
- Validate data schema before analysis
- Fail if required fields missing (vendor ID, amount, date)
- No default thresholds - require explicit configuration
- Log all data quality issues
- Raise on currency mismatches without conversion rates

---

*This skill provides vendor cost analytics expertise for procurement optimization, spend analysis, and supplier consolidation.*
