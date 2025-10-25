---
name: vendor-cost-analytics
description: Analyzes vendor spend, detects duplicates, identifies cost optimization opportunities, and provides procurement analytics methodologies. Use when analyzing vendor costs, consolidating suppliers, detecting duplicate vendors, optimizing payment terms, or building spend analytics dashboards. Covers fuzzy matching algorithms, Pareto analysis, spend segmentation, price variance detection, and vendor risk scoring.
---

# Vendor Cost Analytics

Specialized knowledge for vendor spend analysis, supplier consolidation, and procurement cost optimization.

## When to Use This Skill

Trigger this skill for:
- Vendor spend analysis and reporting
- Duplicate vendor detection using fuzzy matching
- Supplier consolidation opportunities
- Payment terms optimization
- Maverick spend identification
- Vendor master data cleansing
- Procurement analytics dashboards
- Cost trend analysis and forecasting
- Vendor concentration risk assessment

## Core Methodologies

### Spend Analysis
**See**: [reference/spend-analysis.md](reference/spend-analysis.md)

Key techniques:
- Pareto analysis (80/20 rule for vendor concentration)
- Kraljic matrix for vendor segmentation (Strategic, Leverage, Bottleneck, Non-Critical)
- Spend by category, geography, business unit
- Vendor concentration risk (HHI index)
- Maverick spend detection

### Duplicate Detection
**See**: [reference/duplicate-detection.md](reference/duplicate-detection.md)

Algorithms covered:
- SequenceMatcher (Python difflib) - general-purpose fuzzy matching
- Levenshtein distance - character-level typo detection
- Token-based matching - handles word order differences
- Jaccard similarity - n-gram comparison
- Multi-factor matching - combines name, address, tax ID, email, phone
- Threshold selection (conservative: 0.90, moderate: 0.85, aggressive: 0.75)

### Cost Optimization
**See**: [reference/cost-optimization.md](reference/cost-optimization.md)

Strategies:
- Vendor consolidation savings calculation
- Payment terms negotiation (early payment discounts)
- Volume discount analysis
- Contract compliance checking
- Price variance detection

### Data Quality
**See**: [reference/data-quality.md](reference/data-quality.md)

Patterns:
- Vendor master data cleansing rules
- Address standardization and normalization
- Phone/email normalization
- Tax ID validation
- Data validation with fail-fast approach

### Vendor Segmentation
**See**: [reference/vendor-segmentation.md](reference/vendor-segmentation.md)

Frameworks:
- Kraljic Portfolio Purchasing Model (Profit Impact vs Supply Risk)
- Strategic vendor relationship management
- Spend distribution across quadrants
- Vendor rationalization strategies

### Custom Field Analytics
**See**: [workflows/custom-field-analysis.md](workflows/custom-field-analysis.md)

NetSuite custom vendor fields (custentity_*) provide rich metadata for advanced analytics:

**Discovery:**
- List all custom fields with population rates
- Identify deprecated fields (no longer syncing)
- Analyze field value consistency

**Segmentation:**
- Spend by region (custentity_region)
- Spend by payment method (custentity_payment_method)
- Risk-based analysis (custentity_credit_rating)
- Strategic vendor identification (custentity_vendor_tier)

**Quality Checks:**
- Field completeness analysis (population rates)
- Value consistency scoring
- Deprecated field detection

**Reference:** See [integrations/netsuite.md](integrations/netsuite.md#custom-vendor-fields) for field patterns and [reference/data-quality.md](reference/data-quality.md#custom-field-quality-checks) for quality checks

## Workflows

### Vendor Consolidation
**See**: [workflows/consolidation.md](workflows/consolidation.md)

Process:
1. Identify duplicate vendors using fuzzy matching
2. Analyze spend across potential duplicates
3. Calculate consolidation savings (volume discounts, reduced overhead)
4. Generate merge recommendations
5. Assess operational impact and risk

### Spend Dashboard Creation
**See**: [workflows/dashboard.md](workflows/dashboard.md)

Components:
- Top vendors by spend (ranking table)
- Spend trends over time (time series charts)
- Category breakdown (treemap or pie chart)
- Maverick spend alerts (exception reports)
- Vendor concentration metrics (HHI, top-N concentration)

### Payment Terms Optimization
**See**: [workflows/payment-terms.md](workflows/payment-terms.md)

Analysis:
- Current terms distribution (Net 30, Net 60, etc.)
- Early payment discount opportunities (2/10 Net 30 analysis)
- Cash flow impact modeling
- Terms negotiation targets by vendor segment

## Integration Patterns

### NetSuite Integration
**See**: [integrations/netsuite.md](integrations/netsuite.md)

Topics:
- SuiteTalk REST API for vendor data extraction
- SUITEQL queries for transaction data
- Pagination handling (offset/limit pattern)
- OAuth 2.0 authentication
- Read-only enforcement patterns

### PostgreSQL Storage
**See**: [integrations/postgresql.md](integrations/postgresql.md)

Topics:
- SQLAlchemy ORM schema design
- Vendor and transaction table structures
- Index optimization for analytics queries
- Data synchronization patterns

## Complete Examples

### Full Pipeline
**See**: [examples/full-pipeline.md](examples/full-pipeline.md)

End-to-end case study demonstrating:
1. Extract vendor data from ERP (NetSuite)
2. Store locally in PostgreSQL
3. Cleanse and standardize vendor names
4. Detect duplicates using fuzzy matching
5. Analyze spend patterns with Pandas
6. Generate executive recommendations
7. Create interactive dashboard

### Real-World Scenarios
**See**: [examples/scenarios.md](examples/scenarios.md)

Case studies:
- Reducing vendor count from 5,000 to 2,000 (60% reduction)
- Identifying $2M in consolidation savings (3-7% of addressable spend)
- Cleaning vendor master data with 50% duplicate rate
- Optimizing payment terms for improved cash flow (0.5-2% annual savings)

### Duplicate Algorithm Comparison
**See**: [examples/duplicate-algorithm-comparison.md](examples/duplicate-algorithm-comparison.md)

Topics:
- Performance benchmarks for SequenceMatcher, Levenshtein, Token-based
- Accuracy comparison on real vendor data
- When to use each algorithm
- Blocking strategies for O(n²) optimization

## Key Metrics & Benchmarks

### Essential KPIs
- **Total Addressable Spend**: Sum of all vendor spend
- **Vendor Concentration**: Percentage of spend with top N vendors (typically 80% with top 20%)
- **Maverick Spend**: Spend outside approved contracts or vendors
- **Duplicate Rate**: Percentage of vendors identified as duplicates (typical: 5-15%)
- **Average Payment Days (DPO)**: Days payable outstanding
- **Vendor Count**: Active vendor count
- **Spend per Vendor**: Average annual spend per vendor
- **HHI (Herfindahl-Hirschman Index)**: Vendor concentration risk (< 1500 competitive, > 2500 risky)

### Industry Benchmarks
- **Pareto Rule**: Top 20% of vendors represent 80% of spend
- **Duplicate Rate**: 5-15% in most organizations (50% in poorly managed systems)
- **Consolidation Savings**: 3-7% of addressable spend
- **Payment Terms Optimization**: 0.5-2% annual savings

## Tools & Libraries

### Python Ecosystem
- **pandas**: Data manipulation, aggregation, time series analysis
- **difflib**: String similarity (SequenceMatcher - Python standard library)
- **sqlalchemy**: Database ORM for PostgreSQL integration
- **numpy**: Numerical operations for calculations
- **pydantic**: Data validation at API boundaries

### Visualization
- **matplotlib/seaborn**: Static charts for reports
- **plotly**: Interactive dashboards
- **recharts**: React chart components
- **shadcn/ui**: React UI components for dashboards

## Best Practices

### Data Quality First
1. **Clean vendor master data before analysis** - Normalized names, standardized addresses
2. **Use multiple matching algorithms** - Combine fuzzy + phonetic + address + tax ID
3. **Set conservative thresholds initially** - Start with 0.85+ similarity for duplicates
4. **Validate savings before acting** - Model financial impact before vendor consolidation
5. **Consider operational impact** - Not all duplicates should merge (different divisions, contracts)
6. **Track metrics over time** - Monitor duplicate rate, spend concentration monthly
7. **Automate repetitive analysis** - Schedule regular spend reports and duplicate checks

### Fail-Fast Discipline
When building vendor analytics applications:
- Validate data schema before analysis (fail if required fields missing)
- No default thresholds - require explicit configuration
- Fail if vendor ID, amount, or date is missing
- Log all data quality issues
- Raise errors on currency mismatches without conversion rates
- Never swallow exceptions silently

### Performance Optimization
- Use **blocking** to reduce O(n²) comparisons (group by first 3 chars before fuzzy matching)
- Index database on frequently queried fields (vendor_id, tran_date)
- Use **Pandas groupby** for aggregations instead of loops
- Cache vendor master data for repeated queries
- Parallel processing for large duplicate detection runs

## Related Skills

**[NetSuite Business Automation](../netsuite-business-automation/SKILL.md)** - Use for:
- Automating vendor bill processing workflows
- Custom vendor approval routing
- Integration with procure-to-pay automation

**[Financial Analytics](../financial-analytics/SKILL.md)** - Use for:
- Broader financial KPI calculations
- Budget variance analysis
- Cash flow forecasting

## Reference Documentation

Complete documentation organized by topic:

**Core Methodologies:**
- [Spend Analysis](reference/spend-analysis.md) - Pareto, Kraljic, HHI, maverick spend
- [Duplicate Detection](reference/duplicate-detection.md) - Fuzzy matching algorithms
- [Cost Optimization](reference/cost-optimization.md) - Consolidation, payment terms, discounts
- [Data Quality](reference/data-quality.md) - Cleansing, normalization, validation
- [Vendor Segmentation](reference/vendor-segmentation.md) - Kraljic matrix implementation

**Workflows:**
- [Consolidation](workflows/consolidation.md) - Step-by-step vendor consolidation
- [Dashboard](workflows/dashboard.md) - Analytics dashboard design
- [Payment Terms](workflows/payment-terms.md) - Terms optimization workflow

**Integration:**
- [NetSuite](integrations/netsuite.md) - Data extraction from NetSuite
- [PostgreSQL](integrations/postgresql.md) - Local analytics database

**Examples:**
- [Full Pipeline](examples/full-pipeline.md) - Complete end-to-end case study
- [Scenarios](examples/scenarios.md) - Real-world implementations
- [Algorithm Comparison](examples/duplicate-algorithm-comparison.md) - Performance analysis

---

*This skill provides vendor cost analytics expertise for procurement optimization, spend analysis, and supplier consolidation.*
