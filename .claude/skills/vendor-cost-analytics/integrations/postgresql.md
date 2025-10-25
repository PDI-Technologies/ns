# PostgreSQL Integration for Vendor Analytics

Local analytics database patterns for storing and analyzing NetSuite vendor data.

## Overview

PostgreSQL serves as a local analytics database for vendor spend analysis, enabling:
- Offline analysis without impacting NetSuite performance
- Complex aggregations and joins not supported by NetSuite queries
- Historical trend analysis with denormalized schemas
- Fast duplicate detection using fuzzy matching
- Custom reporting and dashboard queries

**Architecture Pattern:**
```
NetSuite (source of truth)
    ↓ sync
PostgreSQL (local analytics)
    ↓ analyze
Analysis Results (Pandas, dashboards)
```

**Key Design Principles:**
- NetSuite internal IDs preserved for traceability
- Denormalized schema optimized for analytics (not OLTP)
- SQLAlchemy ORM for type-safe database access
- Fail-fast validation with Pydantic
- Index strategies for fast aggregation queries

## Database Schema Design

### Vendor Records Table

```sql
CREATE TABLE vendor_records (
    id VARCHAR PRIMARY KEY,  -- NetSuite internal ID
    entity_id VARCHAR,        -- NetSuite entity ID (e.g., "VENDOR123")
    company_name VARCHAR,
    email VARCHAR,
    phone VARCHAR,
    address VARCHAR,
    city VARCHAR,
    state VARCHAR,
    zip VARCHAR,
    country VARCHAR,
    terms VARCHAR,            -- Payment terms (e.g., "Net 30", "2/10 Net 30")
    is_inactive BOOLEAN,
    date_created TIMESTAMP,
    last_modified TIMESTAMP,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Last sync from NetSuite

    -- Indexes for fast lookups
    INDEX idx_company_name (company_name),
    INDEX idx_entity_id (entity_id),
    INDEX idx_synced_at (synced_at)
);
```

**Design Notes:**
- Primary key = NetSuite internal ID (preserves lineage)
- `synced_at` tracks when record was last updated from NetSuite
- Indexes on searchable fields (company name, entity ID)
- Nullable fields for incomplete NetSuite data

### Transaction Records Table

```sql
CREATE TABLE transaction_records (
    id VARCHAR PRIMARY KEY,         -- NetSuite transaction internal ID
    vendor_id VARCHAR NOT NULL,     -- Foreign key to vendor_records.id
    transaction_number VARCHAR,     -- Human-readable transaction number
    transaction_type VARCHAR,       -- 'VendBill', 'VendPymt', etc.
    transaction_date DATE NOT NULL,
    due_date DATE,
    amount NUMERIC(15, 2) NOT NULL,
    status VARCHAR,                 -- 'Open', 'Paid', 'Voided'
    memo VARCHAR,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (vendor_id) REFERENCES vendor_records(id),

    -- Indexes for analytics queries
    INDEX idx_vendor_id (vendor_id),
    INDEX idx_transaction_date (transaction_date),
    INDEX idx_transaction_type (transaction_type),
    INDEX idx_status (status)
);
```

**Design Notes:**
- Foreign key to vendor_records ensures referential integrity
- `transaction_date` indexed for time-series queries
- `vendor_id` indexed for vendor-level aggregations
- NUMERIC type for precise currency calculations

### Analysis Results Table

```sql
CREATE TABLE analysis_results (
    id SERIAL PRIMARY KEY,
    analysis_type VARCHAR NOT NULL,  -- 'vendor_spend', 'duplicates', 'trends'
    result_data JSONB NOT NULL,      -- Flexible schema for results
    parameters JSONB,                -- Analysis parameters (threshold, date range)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_analysis_type (analysis_type),
    INDEX idx_created_at (created_at),
    INDEX gin_result_data (result_data) USING gin  -- GIN index for JSONB queries
);
```

**Design Notes:**
- JSONB for flexible result storage
- GIN index enables fast JSON queries
- `analysis_type` enables filtering by analysis kind
- Audit trail of historical analyses

## SQLAlchemy ORM Models

### Declarative Base and Models

```python
from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Date,
    create_engine,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class VendorRecord(Base):
    """Vendor master data from NetSuite."""

    __tablename__ = "vendor_records"

    id = Column(String, primary_key=True)  # NetSuite internal ID
    entity_id = Column(String)
    company_name = Column(String)
    email = Column(String)
    phone = Column(String)
    address = Column(String)
    city = Column(String)
    state = Column(String)
    zip = Column(String)
    country = Column(String)
    terms = Column(String)
    is_inactive = Column(Boolean, default=False)
    date_created = Column(DateTime)
    last_modified = Column(DateTime)
    synced_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    transactions = relationship("TransactionRecord", back_populates="vendor")

    def __repr__(self) -> str:
        return f"<VendorRecord(id={self.id}, name={self.company_name})>"


class TransactionRecord(Base):
    """Vendor transaction from NetSuite."""

    __tablename__ = "transaction_records"

    id = Column(String, primary_key=True)
    vendor_id = Column(String, ForeignKey("vendor_records.id"), nullable=False)
    transaction_number = Column(String)
    transaction_type = Column(String)
    transaction_date = Column(Date, nullable=False)
    due_date = Column(Date)
    amount = Column(Numeric(15, 2), nullable=False)
    status = Column(String)
    memo = Column(String)
    synced_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    vendor = relationship("VendorRecord", back_populates="transactions")

    def __repr__(self) -> str:
        return f"<TransactionRecord(id={self.id}, vendor_id={self.vendor_id}, amount={self.amount})>"


class AnalysisResult(Base):
    """Stored analysis results."""

    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_type = Column(String, nullable=False)
    result_data = Column(JSONB, nullable=False)
    parameters = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<AnalysisResult(type={self.analysis_type}, created_at={self.created_at})>"
```

**ORM Benefits:**
- Type-safe database access (Pyright/mypy validated)
- Automatic relationship loading
- Protection against SQL injection
- Database migrations via Alembic

## Database Session Management

**Session Factory Pattern:**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

def create_db_engine(database_url: str):
    """
    Create SQLAlchemy engine.

    Args:
        database_url: PostgreSQL connection URL
                      (e.g., 'postgresql://user:password@localhost/dbname')

    Returns:
        SQLAlchemy engine
    """
    return create_engine(
        database_url,
        echo=False,  # Set True for SQL query logging
        future=True,  # SQLAlchemy 2.0 style
        pool_size=5,
        max_overflow=10,
    )


def init_database(database_url: str) -> None:
    """
    Initialize database schema (create all tables).

    Args:
        database_url: PostgreSQL connection URL

    Raises:
        DatabaseError: If schema creation fails
    """
    engine = create_db_engine(database_url)
    Base.metadata.create_all(engine)


def get_session(database_url: str) -> Session:
    """
    Get database session.

    Args:
        database_url: PostgreSQL connection URL

    Returns:
        SQLAlchemy session

    Usage:
        with get_session(db_url) as session:
            vendors = session.query(VendorRecord).all()
    """
    engine = create_db_engine(database_url)
    session_factory = sessionmaker(bind=engine)
    return session_factory()
```

**Context Manager Pattern:**

```python
from contextlib import contextmanager

@contextmanager
def session_scope(database_url: str):
    """
    Provide transactional scope with automatic commit/rollback.

    Usage:
        with session_scope(db_url) as session:
            vendor = VendorRecord(id="123", company_name="Acme Corp")
            session.add(vendor)
            # Automatically commits on success, rolls back on error
    """
    session = get_session(database_url)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

## Data Insertion Patterns

### Upsert (Insert or Update)

```python
from sqlalchemy.dialects.postgresql import insert

def upsert_vendors(session: Session, vendors: list[VendorRecord]) -> None:
    """
    Insert or update vendors using PostgreSQL ON CONFLICT.

    Args:
        session: SQLAlchemy session
        vendors: List of vendor records
    """
    for vendor in vendors:
        stmt = insert(VendorRecord).values(
            id=vendor.id,
            entity_id=vendor.entity_id,
            company_name=vendor.company_name,
            email=vendor.email,
            phone=vendor.phone,
            terms=vendor.terms,
            is_inactive=vendor.is_inactive,
            synced_at=datetime.utcnow(),
        ).on_conflict_do_update(
            index_elements=['id'],  # Conflict on primary key
            set_={
                'company_name': vendor.company_name,
                'email': vendor.email,
                'phone': vendor.phone,
                'terms': vendor.terms,
                'is_inactive': vendor.is_inactive,
                'synced_at': datetime.utcnow(),
            }
        )
        session.execute(stmt)

    session.commit()
```

**Benefits:**
- Idempotent sync operations (can re-run safely)
- Handles incremental updates
- Single database round-trip per record

### Bulk Insert for Performance

```python
def bulk_insert_transactions(session: Session, transactions: list[dict]) -> None:
    """
    Bulk insert transactions for performance.

    Args:
        session: SQLAlchemy session
        transactions: List of transaction dictionaries
    """
    session.bulk_insert_mappings(TransactionRecord, transactions)
    session.commit()


# Usage:
transactions = [
    {
        'id': '1001',
        'vendor_id': '123',
        'transaction_date': '2024-01-15',
        'amount': 1500.00,
        'status': 'Open'
    },
    # ... 10,000 more records
]

bulk_insert_transactions(session, transactions)
```

**Performance:**
- 10-100x faster than individual inserts
- Use for initial data load (not incremental updates)
- Trade-off: No ON CONFLICT support

## Query Patterns for Analytics

### Vendor Spend Aggregation

```python
from sqlalchemy import func
from datetime import date

def calculate_vendor_spend(
    session: Session,
    start_date: date,
    end_date: date
) -> list[dict]:
    """
    Calculate total spend by vendor for date range.

    Args:
        session: SQLAlchemy session
        start_date: Start of analysis period
        end_date: End of analysis period

    Returns:
        List of {vendor_id, vendor_name, total_spend, transaction_count}
    """
    results = session.query(
        VendorRecord.id.label('vendor_id'),
        VendorRecord.company_name.label('vendor_name'),
        func.sum(TransactionRecord.amount).label('total_spend'),
        func.count(TransactionRecord.id).label('transaction_count')
    ).join(
        TransactionRecord,
        VendorRecord.id == TransactionRecord.vendor_id
    ).filter(
        TransactionRecord.transaction_date >= start_date,
        TransactionRecord.transaction_date <= end_date,
        TransactionRecord.status != 'Voided'
    ).group_by(
        VendorRecord.id,
        VendorRecord.company_name
    ).order_by(
        func.sum(TransactionRecord.amount).desc()
    ).all()

    return [
        {
            'vendor_id': r.vendor_id,
            'vendor_name': r.vendor_name,
            'total_spend': float(r.total_spend),
            'transaction_count': r.transaction_count
        }
        for r in results
    ]
```

### Monthly Trend Analysis

```python
def calculate_monthly_trends(session: Session, vendor_id: str) -> list[dict]:
    """
    Calculate monthly spend trend for vendor.

    Args:
        session: SQLAlchemy session
        vendor_id: Vendor internal ID

    Returns:
        List of {month, total_spend, transaction_count}
    """
    results = session.query(
        func.date_trunc('month', TransactionRecord.transaction_date).label('month'),
        func.sum(TransactionRecord.amount).label('total_spend'),
        func.count(TransactionRecord.id).label('transaction_count')
    ).filter(
        TransactionRecord.vendor_id == vendor_id,
        TransactionRecord.status != 'Voided'
    ).group_by(
        func.date_trunc('month', TransactionRecord.transaction_date)
    ).order_by('month').all()

    return [
        {
            'month': r.month.strftime('%Y-%m'),
            'total_spend': float(r.total_spend),
            'transaction_count': r.transaction_count
        }
        for r in results
    ]
```

### Duplicate Vendor Detection Query

```python
def get_potential_duplicates(session: Session) -> list[tuple[VendorRecord, VendorRecord]]:
    """
    Get potential duplicate vendors using database fuzzy matching.

    Note: For production, use Python difflib for better fuzzy matching.
    This query uses PostgreSQL trigram similarity as a pre-filter.

    Returns:
        List of (vendor1, vendor2) tuples
    """
    from sqlalchemy import text

    # Requires pg_trgm extension: CREATE EXTENSION pg_trgm;
    query = text("""
        SELECT
            v1.id AS vendor_1_id,
            v2.id AS vendor_2_id,
            similarity(v1.company_name, v2.company_name) AS similarity
        FROM
            vendor_records v1
        JOIN
            vendor_records v2 ON v1.id < v2.id
        WHERE
            v1.company_name % v2.company_name  -- % is trigram similarity operator
            AND similarity(v1.company_name, v2.company_name) > 0.6
        ORDER BY
            similarity DESC
        LIMIT 100
    """)

    results = session.execute(query).fetchall()

    duplicate_pairs = []
    for row in results:
        v1 = session.query(VendorRecord).filter_by(id=row.vendor_1_id).first()
        v2 = session.query(VendorRecord).filter_by(id=row.vendor_2_id).first()
        duplicate_pairs.append((v1, v2))

    return duplicate_pairs
```

## Integration with Pandas for Advanced Analytics

**Export to DataFrame:**

```python
import pandas as pd

def vendor_spend_to_dataframe(session: Session) -> pd.DataFrame:
    """
    Export vendor spend to Pandas DataFrame for analysis.

    Returns:
        DataFrame with vendor spend data
    """
    results = session.query(
        VendorRecord.id,
        VendorRecord.company_name,
        VendorRecord.terms,
        func.sum(TransactionRecord.amount).label('total_spend'),
        func.count(TransactionRecord.id).label('transaction_count')
    ).join(
        TransactionRecord
    ).group_by(
        VendorRecord.id,
        VendorRecord.company_name,
        VendorRecord.terms
    ).all()

    df = pd.DataFrame([
        {
            'vendor_id': r.id,
            'company_name': r.company_name,
            'terms': r.terms,
            'total_spend': float(r.total_spend),
            'transaction_count': r.transaction_count
        }
        for r in results
    ])

    return df


# Pandas aggregation
df = vendor_spend_to_dataframe(session)
top_vendors = df.nlargest(20, 'total_spend')
spend_by_terms = df.groupby('terms')['total_spend'].sum()
```

## Storing Analysis Results

**Save analysis results for historical tracking:**

```python
import json

def store_analysis_result(
    session: Session,
    analysis_type: str,
    result_data: dict,
    parameters: dict | None = None
) -> int:
    """
    Store analysis result in database.

    Args:
        session: SQLAlchemy session
        analysis_type: Type of analysis (e.g., 'vendor_spend', 'duplicates')
        result_data: Analysis results as dictionary
        parameters: Analysis parameters (threshold, date range, etc.)

    Returns:
        ID of created analysis result
    """
    result = AnalysisResult(
        analysis_type=analysis_type,
        result_data=result_data,
        parameters=parameters or {},
        created_at=datetime.utcnow()
    )

    session.add(result)
    session.commit()

    return result.id


# Usage:
duplicate_results = {
    'pairs_found': 47,
    'threshold': 0.85,
    'top_duplicates': [
        {'vendor_1': 'Acme Corp', 'vendor_2': 'Acme Corporation', 'similarity': 0.92},
        # ... more results
    ]
}

result_id = store_analysis_result(
    session,
    analysis_type='duplicates',
    result_data=duplicate_results,
    parameters={'threshold': 0.85, 'date_range': '2024-01-01 to 2024-12-31'}
)
```

## Database Migrations with Alembic

**Initialize Alembic:**

```bash
# Install Alembic
pip install alembic

# Initialize migrations
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Add custom_fields to vendor_records"

# Apply migration
alembic upgrade head
```

**Migration Script Example:**

```python
"""Add custom fields to vendor_records

Revision ID: abc123def456
"""
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    op.add_column('vendor_records',
        sa.Column('custom_field_1', sa.String(), nullable=True))
    op.add_column('vendor_records',
        sa.Column('custom_field_2', sa.String(), nullable=True))

def downgrade() -> None:
    op.drop_column('vendor_records', 'custom_field_2')
    op.drop_column('vendor_records', 'custom_field_1')
```

## Performance Optimization

### Indexing Strategy

```sql
-- Composite index for vendor spend queries
CREATE INDEX idx_vendor_transaction_date
ON transaction_records(vendor_id, transaction_date);

-- Partial index for active vendors only
CREATE INDEX idx_active_vendors
ON vendor_records(company_name)
WHERE is_inactive = FALSE;

-- GIN index for JSONB analysis results
CREATE INDEX idx_analysis_jsonb
ON analysis_results USING gin(result_data);
```

### Query Performance

```python
# Bad: N+1 query problem
vendors = session.query(VendorRecord).all()
for vendor in vendors:
    transactions = vendor.transactions  # Separate query per vendor!

# Good: Eager loading with joinedload
from sqlalchemy.orm import joinedload

vendors = session.query(VendorRecord)\
    .options(joinedload(VendorRecord.transactions))\
    .all()  # Single query with JOIN
```

## Complete Integration Example

```python
from datetime import datetime, date

# 1. Initialize database
init_database("postgresql://user:password@localhost/vendor_analytics")

# 2. Create session
with session_scope("postgresql://user:password@localhost/vendor_analytics") as session:

    # 3. Insert vendors from NetSuite sync
    vendors = [
        VendorRecord(id="123", company_name="Acme Corp", terms="Net 30"),
        VendorRecord(id="456", company_name="Tech Solutions", terms="2/10 Net 30")
    ]
    upsert_vendors(session, vendors)

    # 4. Insert transactions
    transactions = [
        {
            'id': '1001',
            'vendor_id': '123',
            'transaction_date': date(2024, 1, 15),
            'amount': 1500.00,
            'status': 'Paid'
        }
    ]
    bulk_insert_transactions(session, transactions)

    # 5. Run analytics
    spend_results = calculate_vendor_spend(
        session,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31)
    )

    # 6. Store results
    store_analysis_result(
        session,
        analysis_type='vendor_spend',
        result_data={'results': spend_results},
        parameters={'year': 2024}
    )

print(f"Analyzed {len(spend_results)} vendors")
```

## Related Documentation

- **[NetSuite Integration](netsuite.md)** - Data extraction from NetSuite
- **[Duplicate Detection](../reference/duplicate-detection.md)** - Fuzzy matching algorithms
- **[Full Pipeline Example](../examples/full-pipeline.md)** - End-to-end workflow

**External References:**
- [SQLAlchemy ORM Documentation](https://docs.sqlalchemy.org/en/20/orm/)
- [PostgreSQL Performance Tips](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Alembic Database Migrations](https://alembic.sqlalchemy.org/)

---

*Based on production implementation in vendor-analysis CLI application*
