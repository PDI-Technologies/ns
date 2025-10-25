# Database Integration for Financial Analytics

Store and analyze financial data using PostgreSQL, MSSQL, or MySQL databases.

## Overview

Databases provide:
- **Local storage** for fast analysis of financial data
- **Data warehouse** capabilities for historical reporting
- **SQL aggregation** for complex financial calculations
- **Multi-source integration** combining data from multiple systems

## Supported Databases

Three database types are supported via MCP tools:
- **PostgreSQL** - Recommended for financial applications
- **MSSQL** (Microsoft SQL Server) - Enterprise data warehouses
- **MySQL** - High-performance applications

## MCP Database Tool

The `mcp__mssql__query` tool supports all three database types via the `dbType` parameter.

### Connection Parameters

**PostgreSQL:**
```python
mcp__mssql__query(
    query="SELECT * FROM financial_data",
    host="postgres.server.com",
    port=5432,
    database="analytics",
    username="finance_user",
    password="***",
    dbType="postgres",
    sslMode="require"  # disable, require, verify-ca, verify-full
)
```

**MSSQL:**
```python
mcp__mssql__query(
    query="SELECT * FROM financial_data",
    host="mssql.server.com",
    port=1433,
    database="DataWarehouse",
    username="finance_user",
    password="***",
    dbType="mssql",
    encrypt=True,
    trustServerCertificate=True
)
```

**MySQL:**
```python
mcp__mssql__query(
    query="SELECT * FROM financial_data",
    host="mysql.server.com",
    port=3306,
    database="analytics",
    username="finance_user",
    password="***",
    dbType="mysql",
    timezone="+00:00"
)
```

## Database Schema Design

### Vendor Analysis Schema

```sql
-- Vendor master data
CREATE TABLE vendors (
    id VARCHAR(50) PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    balance DECIMAL(15, 2) DEFAULT 0,
    terms VARCHAR(100),
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_company_name (company_name),
    INDEX idx_synced_at (synced_at)
);

-- Vendor transactions
CREATE TABLE vendor_bills (
    id VARCHAR(50) PRIMARY KEY,
    tran_id VARCHAR(100),
    vendor_id VARCHAR(50) NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    tran_date DATE NOT NULL,
    due_date DATE,
    status VARCHAR(50),
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_vendor_id (vendor_id),
    INDEX idx_tran_date (tran_date),
    INDEX idx_status (status),

    FOREIGN KEY (vendor_id) REFERENCES vendors(id)
);

-- Analysis results cache
CREATE TABLE analysis_results (
    id SERIAL PRIMARY KEY,
    analysis_type VARCHAR(100) NOT NULL,
    result_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_analysis_type (analysis_type),
    INDEX idx_created_at (created_at)
);
```

### Revenue Analysis Schema

```sql
-- Customer master data
CREATE TABLE customers (
    id VARCHAR(50) PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    balance DECIMAL(15, 2) DEFAULT 0,
    lifetime_value DECIMAL(15, 2) DEFAULT 0,
    first_purchase_date DATE,
    last_purchase_date DATE,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Revenue transactions
CREATE TABLE invoices (
    id VARCHAR(50) PRIMARY KEY,
    invoice_number VARCHAR(100) NOT NULL,
    customer_id VARCHAR(50) NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    invoice_date DATE NOT NULL,
    due_date DATE,
    paid_date DATE,
    status VARCHAR(50),
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- Product revenue
CREATE TABLE product_revenue (
    id SERIAL PRIMARY KEY,
    product_id VARCHAR(50) NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    product_family VARCHAR(100),
    revenue DECIMAL(15, 2) NOT NULL,
    quantity INTEGER NOT NULL,
    period DATE NOT NULL,

    INDEX idx_product_id (product_id),
    INDEX idx_period (period)
);
```

## Data Loading Patterns

### Pattern 1: SQLAlchemy ORM (Python)

**Recommended for Python applications:**

```python
from sqlalchemy import create_engine, Column, String, Numeric, Date, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from decimal import Decimal

Base = declarative_base()

class VendorRecord(Base):
    """Vendor master data model."""
    __tablename__ = "vendors"

    id = Column(String(50), primary_key=True)
    company_name = Column(String(255), nullable=False)
    email = Column(String(255))
    balance = Column(Numeric(15, 2), default=0)
    terms = Column(String(100))
    synced_at = Column(DateTime, default=datetime.utcnow)

class VendorBillRecord(Base):
    """Vendor transaction model."""
    __tablename__ = "vendor_bills"

    id = Column(String(50), primary_key=True)
    tran_id = Column(String(100))
    vendor_id = Column(String(50), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    tran_date = Column(Date, nullable=False)
    due_date = Column(Date)
    status = Column(String(50))
    synced_at = Column(DateTime, default=datetime.utcnow)

# Create engine and session
engine = create_engine("postgresql://user:pass@localhost/analytics")
Session = sessionmaker(bind=engine)

# Create tables
Base.metadata.create_all(engine)

# Insert data
session = Session()
vendor = VendorRecord(
    id="123",
    company_name="Acme Corp",
    balance=Decimal("15000.50")
)
session.add(vendor)
session.commit()
```

**See:** `/opt/ns/apps/vendor-analysis/src/vendor_analysis/db/models.py`

### Pattern 2: Direct SQL via MCP

**For simple inserts or integration without ORM:**

```python
def insert_vendor_data(vendors: list[dict]):
    """Insert vendor data using MCP tool."""
    for vendor in vendors:
        query = """
            INSERT INTO vendors (id, company_name, email, balance, terms)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (id) DO UPDATE SET
                company_name = EXCLUDED.company_name,
                email = EXCLUDED.email,
                balance = EXCLUDED.balance,
                terms = EXCLUDED.terms,
                synced_at = CURRENT_TIMESTAMP
        """

        mcp__mssql__query(
            query=query,
            host="postgres.server.com",
            database="analytics",
            username="finance_user",
            password="***",
            dbType="postgres"
        )
```

### Pattern 3: Bulk Loading with Pandas

**For high-performance batch loading:**

```python
import pandas as pd
from sqlalchemy import create_engine

def bulk_load_vendors(vendors: list[dict], db_url: str):
    """Bulk load vendor data using Pandas."""
    # Convert to DataFrame
    df = pd.DataFrame(vendors)

    # Convert numeric columns
    df["balance"] = pd.to_numeric(df["balance"], errors="coerce")

    # Create engine
    engine = create_engine(db_url)

    # Bulk insert (upsert with replace)
    df.to_sql(
        name="vendors",
        con=engine,
        if_exists="replace",  # or 'append' for incremental
        index=False,
        method="multi",  # Batch insert for speed
        chunksize=1000
    )
```

## Querying Financial Data

### Vendor Spend Analysis

```python
def analyze_vendor_spend(db_url: str) -> pd.DataFrame:
    """Analyze vendor spend from database."""
    query = """
        SELECT
            v.id,
            v.company_name,
            COUNT(vb.id) as transaction_count,
            SUM(vb.amount) as total_spend,
            AVG(vb.amount) as avg_transaction,
            MIN(vb.tran_date) as first_transaction,
            MAX(vb.tran_date) as last_transaction
        FROM vendors v
        LEFT JOIN vendor_bills vb ON v.id = vb.vendor_id
        WHERE vb.status = 'Paid'
        GROUP BY v.id, v.company_name
        HAVING SUM(vb.amount) > 0
        ORDER BY total_spend DESC
    """

    engine = create_engine(db_url)
    df = pd.read_sql(query, engine)

    return df
```

### Revenue Trend Analysis

```python
def analyze_revenue_trends(db_url: str, months: int = 12) -> pd.DataFrame:
    """Analyze monthly revenue trends."""
    query = f"""
        SELECT
            DATE_TRUNC('month', invoice_date) as month,
            SUM(amount) as total_revenue,
            COUNT(id) as invoice_count,
            AVG(amount) as avg_invoice_size,
            COUNT(DISTINCT customer_id) as unique_customers
        FROM invoices
        WHERE
            invoice_date >= CURRENT_DATE - INTERVAL '{months} months'
            AND status = 'Paid'
        GROUP BY DATE_TRUNC('month', invoice_date)
        ORDER BY month ASC
    """

    engine = create_engine(db_url)
    df = pd.read_sql(query, engine)

    # Calculate growth rates
    df["revenue_growth"] = df["total_revenue"].pct_change()
    df["customer_growth"] = df["unique_customers"].pct_change()

    return df
```

### Customer Lifetime Value

```python
def calculate_customer_ltv(db_url: str) -> pd.DataFrame:
    """Calculate customer lifetime value."""
    query = """
        WITH customer_metrics AS (
            SELECT
                c.id,
                c.company_name,
                c.first_purchase_date,
                COUNT(i.id) as purchase_count,
                SUM(i.amount) as total_revenue,
                AVG(i.amount) as avg_order_value,
                MAX(i.invoice_date) - MIN(i.invoice_date) as customer_lifespan_days,
                CURRENT_DATE - MAX(i.invoice_date) as days_since_last_purchase
            FROM customers c
            LEFT JOIN invoices i ON c.id = i.customer_id
            WHERE i.status = 'Paid'
            GROUP BY c.id, c.company_name, c.first_purchase_date
        )
        SELECT
            *,
            total_revenue / NULLIF(customer_lifespan_days, 0) * 365 as annual_revenue_rate,
            CASE
                WHEN days_since_last_purchase <= 90 THEN 'Active'
                WHEN days_since_last_purchase <= 180 THEN 'At Risk'
                ELSE 'Churned'
            END as customer_status
        FROM customer_metrics
        ORDER BY total_revenue DESC
    """

    engine = create_engine(db_url)
    return pd.read_sql(query, engine)
```

## Session Management

For multiple operations, use session management to reuse connections:

```python
# Create session
mcp__mssql__manage_session(
    action="create",
    sessionId="financial-analysis-001"
)

# Execute multiple queries using same session
for query in queries:
    mcp__mssql__query(
        query=query,
        sessionId="financial-analysis-001",
        host="postgres.server.com",
        database="analytics",
        username="user",
        password="***",
        dbType="postgres"
    )

# End session when done
mcp__mssql__manage_session(
    action="end",
    sessionId="financial-analysis-001"
)

# Check session status
status = mcp__mssql__manage_session(
    action="status",
    sessionId="financial-analysis-001"
)
```

## Complete ETL Example

```python
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine

class FinancialDataPipeline:
    """Complete ETL pipeline for financial data."""

    def __init__(self, db_url: str):
        self.db_url = db_url
        self.engine = create_engine(db_url)

    def extract_from_netsuite(self, ns_client) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Extract vendor and transaction data from NetSuite."""
        # Fetch vendors
        vendors = fetch_all_vendors(ns_client, settings)
        vendors_df = pd.DataFrame([v.model_dump() for v in vendors])

        # Fetch transactions
        bills = fetch_vendor_bills(ns_client, settings)
        bills_df = pd.DataFrame([b.model_dump() for b in bills])

        return vendors_df, bills_df

    def transform(self, vendors_df: pd.DataFrame, bills_df: pd.DataFrame):
        """Transform and clean data."""
        # Add sync timestamp
        vendors_df["synced_at"] = datetime.utcnow()
        bills_df["synced_at"] = datetime.utcnow()

        # Convert amounts to Decimal
        bills_df["amount"] = bills_df["amount"].apply(lambda x: round(x, 2))

        # Handle nulls
        vendors_df["email"] = vendors_df["email"].fillna("")
        bills_df["due_date"] = bills_df["due_date"].fillna(bills_df["tran_date"])

        return vendors_df, bills_df

    def load(self, vendors_df: pd.DataFrame, bills_df: pd.DataFrame):
        """Load data to database."""
        # Load vendors (replace existing)
        vendors_df.to_sql(
            "vendors",
            self.engine,
            if_exists="replace",
            index=False,
            method="multi"
        )

        # Load bills (replace existing)
        bills_df.to_sql(
            "vendor_bills",
            self.engine,
            if_exists="replace",
            index=False,
            method="multi"
        )

    def run(self, ns_client):
        """Execute complete ETL pipeline."""
        print("Extracting data from NetSuite...")
        vendors_df, bills_df = self.extract_from_netsuite(ns_client)

        print("Transforming data...")
        vendors_df, bills_df = self.transform(vendors_df, bills_df)

        print("Loading to database...")
        self.load(vendors_df, bills_df)

        print(f"Loaded {len(vendors_df)} vendors and {len(bills_df)} bills")
```

## Data Warehouse Design

### Star Schema for Financial Reporting

```sql
-- Fact table: Financial transactions
CREATE TABLE fact_transactions (
    transaction_id VARCHAR(50) PRIMARY KEY,
    transaction_date DATE NOT NULL,
    customer_key INT,
    product_key INT,
    account_key INT,
    amount DECIMAL(15, 2) NOT NULL,
    quantity INT,
    cost DECIMAL(15, 2),

    FOREIGN KEY (customer_key) REFERENCES dim_customers(customer_key),
    FOREIGN KEY (product_key) REFERENCES dim_products(product_key),
    FOREIGN KEY (account_key) REFERENCES dim_accounts(account_key)
);

-- Dimension: Customers
CREATE TABLE dim_customers (
    customer_key SERIAL PRIMARY KEY,
    customer_id VARCHAR(50) UNIQUE,
    customer_name VARCHAR(255),
    industry VARCHAR(100),
    region VARCHAR(100)
);

-- Dimension: Products
CREATE TABLE dim_products (
    product_key SERIAL PRIMARY KEY,
    product_id VARCHAR(50) UNIQUE,
    product_name VARCHAR(255),
    product_family VARCHAR(100),
    unit_price DECIMAL(15, 2)
);

-- Dimension: Accounts (Chart of Accounts)
CREATE TABLE dim_accounts (
    account_key SERIAL PRIMARY KEY,
    account_id VARCHAR(50) UNIQUE,
    account_number VARCHAR(50),
    account_name VARCHAR(255),
    account_type VARCHAR(50)
);

-- Dimension: Time
CREATE TABLE dim_time (
    date_key INT PRIMARY KEY,
    full_date DATE UNIQUE,
    year INT,
    quarter INT,
    month INT,
    month_name VARCHAR(20),
    week INT,
    day_of_month INT,
    day_of_week INT,
    is_weekend BOOLEAN
);
```

## Performance Optimization

### Indexing Strategy

```sql
-- Indexes for vendor analysis
CREATE INDEX idx_vendor_bills_vendor_date ON vendor_bills(vendor_id, tran_date);
CREATE INDEX idx_vendor_bills_status ON vendor_bills(status);
CREATE INDEX idx_vendors_name ON vendors(company_name);

-- Indexes for revenue analysis
CREATE INDEX idx_invoices_customer_date ON invoices(customer_id, invoice_date);
CREATE INDEX idx_invoices_date_status ON invoices(invoice_date, status);

-- Composite index for common query patterns
CREATE INDEX idx_transactions_date_type_amount ON fact_transactions(transaction_date, transaction_type, amount);
```

### Partitioning Large Tables

```sql
-- Partition by year for historical data
CREATE TABLE vendor_bills_2024 PARTITION OF vendor_bills
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

CREATE TABLE vendor_bills_2025 PARTITION OF vendor_bills
FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
```

## Best Practices

### Use Decimal Types for Financial Data

```python
from decimal import Decimal

# CORRECT - Use Decimal
amount = Decimal("1234.56")

# INCORRECT - Don't use float
amount = 1234.56  # Precision issues!
```

### Validate Data Before Loading

```python
def validate_financial_record(record: dict) -> bool:
    """Validate financial record before database insert."""
    # Check required fields
    required_fields = ["id", "amount", "tran_date"]
    if not all(field in record for field in required_fields):
        return False

    # Validate amount is positive
    if record["amount"] < 0:
        return False

    # Validate date format
    try:
        datetime.fromisoformat(str(record["tran_date"]))
    except:
        return False

    return True
```

### Transaction Safety

```python
from sqlalchemy.orm import Session

def safe_bulk_insert(session: Session, records: list):
    """Insert with transaction safety."""
    try:
        session.bulk_insert_mappings(VendorRecord, records)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Insert failed: {e}")
        return False
```

## Related Resources

- **Vendor Analysis App:** `/opt/ns/apps/vendor-analysis/` (complete PostgreSQL implementation)
- **NetSuite Integration:** `netsuite.md` (data extraction)
- **Salesforce Integration:** `salesforce.md` (revenue data)

## Official Documentation

- **PostgreSQL:** https://www.postgresql.org/docs/
- **SQLAlchemy:** https://docs.sqlalchemy.org/
- **Pandas SQL:** https://pandas.pydata.org/docs/user_guide/io.html#sql-queries
