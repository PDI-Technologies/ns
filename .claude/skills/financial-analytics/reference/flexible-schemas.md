# Flexible Schemas for Financial Data

Patterns for using JSONB and flexible schemas to handle custom financial dimensions, GL account attributes, and evolving financial system metadata.

## Overview

Financial systems often have custom dimensions beyond standard chart of accounts:
- **Custom GL account attributes** (account categories, fund codes, program codes)
- **Custom department/location codes** (beyond standard subsidiaries)
- **Custom financial dimensions** (project codes, grant codes, cost centers)
- **Budget metadata** (budget owner, approval level, spending authority)
- **Vendor financial metadata** (payment terms tiers, credit classifications)

**Challenge:** These custom dimensions vary widely across organizations and change as business evolves.

**Solution:** Use hybrid schema (typed columns + JSONB) to capture both standard and custom financial data.

---

## Hybrid Financial Schema Pattern

### Chart of Accounts with Custom Attributes

```sql
CREATE TABLE gl_accounts (
    -- Standard fields (typed columns)
    account_id VARCHAR(50) PRIMARY KEY,
    account_number VARCHAR(50) NOT NULL,
    account_name VARCHAR(500) NOT NULL,
    account_type VARCHAR(50) NOT NULL,  -- Asset, Liability, Equity, Revenue, Expense
    balance NUMERIC(15, 2) DEFAULT 0.0,
    is_inactive BOOLEAN DEFAULT FALSE,

    -- Custom dimensions (JSONB)
    custom_dimensions JSONB,  -- Fund codes, program codes, grants, etc.
    attributes JSONB,          -- Additional account metadata

    -- Audit fields
    last_modified_date TIMESTAMP,
    synced_at TIMESTAMP DEFAULT NOW()
);

-- Index for custom dimension queries
CREATE INDEX idx_gl_accounts_custom_gin
ON gl_accounts USING GIN (custom_dimensions);
```

### Financial Transaction with Dimensions

```sql
CREATE TABLE financial_transactions (
    -- Standard transaction fields
    transaction_id VARCHAR(50) PRIMARY KEY,
    transaction_date DATE NOT NULL,
    account_id VARCHAR(50) REFERENCES gl_accounts(account_id),
    amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    description TEXT,

    -- Standard dimensions (typed)
    department VARCHAR(50),
    location VARCHAR(50),
    subsidiary VARCHAR(50),

    -- Custom dimensions (JSONB)
    custom_dimensions JSONB,  -- Project, grant, fund, program, etc.

    -- Complete source data
    source_data JSONB  -- Original ERP response
);

CREATE INDEX idx_transactions_custom_gin
ON financial_transactions USING GIN (custom_dimensions);
```

---

## Common Custom Financial Dimensions

### Government/Non-Profit

**Fund accounting:**
```json
{
  "fund_code": "10100",
  "fund_name": "General Fund",
  "fund_type": "Unrestricted",
  "grant_id": "GRANT2025-001",
  "program_code": "PROG-EDU",
  "restricted": false
}
```

### Project-Based

**Project tracking:**
```json
{
  "project_id": "PRJ-2025-042",
  "project_name": "Office Renovation",
  "project_manager": "Jane Doe",
  "budget_code": "CAPEX-2025",
  "cost_center": "CC-100",
  "approval_level": "VP"
}
```

### Multi-Entity

**Intercompany dimensions:**
```json
{
  "entity_id": "ENT-US-01",
  "profit_center": "PC-WEST",
  "business_unit": "BU-RETAIL",
  "region": "Americas",
  "segment": "Commercial"
}
```

---

## SQLAlchemy Models

### GL Account Model

```python
from sqlalchemy import Column, String, Numeric, Boolean, DateTime, JSONB
from sqlalchemy.orm import DeclarativeBase

class GLAccount(Base):
    __tablename__ = "gl_accounts"

    # Typed columns
    account_id = Column(String(50), primary_key=True)
    account_number = Column(String(50), nullable=False)
    account_name = Column(String(500), nullable=False)
    account_type = Column(String(50), nullable=False)
    balance = Column(Numeric(15, 2), default=0.0)
    is_inactive = Column(Boolean, default=False)

    # Flexible columns
    custom_dimensions = Column(JSONB)
    attributes = Column(JSONB)

    # Audit
    last_modified_date = Column(DateTime)
    synced_at = Column(DateTime)
```

### Transaction Model

```python
from decimal import Decimal

class FinancialTransaction(Base):
    __tablename__ = "financial_transactions"

    # Core fields
    transaction_id = Column(String(50), primary_key=True)
    transaction_date = Column(Date, nullable=False)
    account_id = Column(String(50), ForeignKey('gl_accounts.account_id'))
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default='USD')

    # Standard dimensions
    department = Column(String(50))
    location = Column(String(50))
    subsidiary = Column(String(50))

    # Custom dimensions
    custom_dimensions = Column(JSONB)
    source_data = Column(JSONB)
```

---

## Querying Custom Financial Dimensions

### Basic Dimension Queries

```python
from sqlalchemy import func

# Find transactions by custom project
project_transactions = session.query(FinancialTransaction).filter(
    func.jsonb_extract_path_text(
        FinancialTransaction.custom_dimensions,
        'project_id'
    ) == 'PRJ-2025-042'
).all()

# Sum by fund code
fund_totals = session.query(
    func.jsonb_extract_path_text(
        FinancialTransaction.custom_dimensions,
        'fund_code'
    ).label('fund'),
    func.sum(FinancialTransaction.amount).label('total')
).group_by('fund').all()
```

### Complex Dimension Analysis

```python
import pandas as pd

def analyze_by_dimensions(session, dimensions):
    """Analyze spend by multiple custom dimensions

    Args:
        dimensions: List of dimension keys to analyze

    Returns:
        DataFrame with aggregated spend
    """
    # Build query
    dimension_selects = [
        f"custom_dimensions->>'{dim}' as {dim}"
        for dim in dimensions
    ]

    query = f"""
        SELECT
            {', '.join(dimension_selects)},
            SUM(amount) as total_amount,
            COUNT(*) as transaction_count
        FROM financial_transactions
        GROUP BY {', '.join(dimensions)}
        ORDER BY total_amount DESC
    """

    df = pd.read_sql(query, session.connection())
    return df

# Usage
spend_by_project_and_fund = analyze_by_dimensions(
    session,
    dimensions=['project_id', 'fund_code']
)
```

---

## Budget Tracking with Custom Dimensions

```python
class Budget(Base):
    """Budget with custom dimensional attributes"""
    __tablename__ = "budgets"

    # Core
    budget_id = Column(String(50), primary_key=True)
    fiscal_year = Column(Integer, nullable=False)
    account_id = Column(String(50))
    budgeted_amount = Column(Numeric(15, 2))

    # Standard dimensions
    department = Column(String(50))
    location = Column(String(50))

    # Custom dimensions (fund, project, grant, etc.)
    dimensions = Column(JSONB)

def check_budget_available(session, account_id, dimensions, amount):
    """Check if budget available for transaction with dimensions

    Args:
        account_id: GL account
        dimensions: Dict of custom dimensions
        amount: Transaction amount

    Returns:
        Boolean indicating if budget sufficient
    """
    # Find matching budget
    budget = session.query(Budget).filter(
        Budget.account_id == account_id,
        Budget.dimensions.contains(dimensions)
    ).first()

    if not budget:
        return False  # No budget defined

    # Calculate spent amount
    spent = session.query(func.sum(FinancialTransaction.amount)).filter(
        FinancialTransaction.account_id == account_id,
        FinancialTransaction.custom_dimensions.contains(dimensions)
    ).scalar() or 0

    # Check availability
    available = budget.budgeted_amount - spent
    return available >= amount
```

---

## Related Patterns

**Python CLI Engineering Skill:**
- `patterns/postgresql-jsonb.md` - JSONB query patterns and indexing
- `patterns/schema-resilience.md` - 3-layer architecture for evolving schemas
- `reference/database-migrations.md` - Idempotent migrations for adding JSONB columns

**NetSuite Integrations Skill:**
- `patterns/schema-evolution.md` - Handling custom field changes in NetSuite
- `suitetalk/rest-api.md` - Fetching complete financial data from NetSuite

**Vendor Cost Analytics Skill:**
- `workflows/custom-field-analysis.md` - Custom field discovery and analysis
- `reference/data-quality.md` - Custom field quality checks

**Reference Implementation:**
- `/opt/ns/apps/vendor-analysis/` - JSONB patterns for financial vendor data

---

## Summary

**Key Points:**

1. **Hybrid schema** - Typed columns for standard GL/dimensions, JSONB for custom
2. **GIN indexes** - Fast queries on custom dimensions
3. **Budget tracking** - Use JSONB contains for multi-dimensional budget matching
4. **Analysis flexibility** - Query any custom dimension without schema changes
5. **Cross-reference pattern** - Link to python-cli-engineering for implementation details

**JSONB enables flexible financial reporting across organizations with different dimensional requirements, eliminating custom schema development for each deployment.**
