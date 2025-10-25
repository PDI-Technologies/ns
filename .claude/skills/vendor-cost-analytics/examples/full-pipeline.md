# Full Vendor Analytics Pipeline

End-to-end workflow demonstrating NetSuite vendor data extraction, storage, and analysis.

## Overview

This example demonstrates a complete vendor analytics pipeline from NetSuite data extraction to actionable insights.

**Pipeline Stages:**
1. **Authentication** - Establish secure connection to NetSuite
2. **Data Extraction** - Sync vendors and transactions via SuiteTalk REST API
3. **Storage** - Persist data in local PostgreSQL database
4. **Analysis** - Run spend analysis and duplicate detection
5. **Reporting** - Generate reports and dashboards
6. **Action** - Use insights for cost optimization

**Technologies Used:**
- NetSuite SuiteTalk REST API (data source)
- OAuth 2.0 (authentication)
- PostgreSQL (local analytics database)
- SQLAlchemy ORM (database access)
- Pandas (data analysis)
- Python CLI (orchestration)

**Learning Example:**
The vendor-analysis CLI application (`/opt/ns/apps/vendor-analysis`) implements this pattern and serves as a reference implementation.

## Stage 1: Authentication

### OAuth 2.0 Setup

**Prerequisites:**
1. NetSuite Integration Record created (Setup → Integrations → Manage Integrations)
2. OAuth 2.0 enabled with appropriate scopes
3. Client ID and Client Secret obtained
4. Credentials stored in `.env` file

**Environment Configuration:**

```bash
# .env file
NS_ACCOUNT_ID=1234567
NS_CLIENT_ID=abc123def456...
NS_CLIENT_SECRET=xyz789ghi012...
DB_USER=analytics_user
DB_PASSWORD=secure_password
```

**Authentication Client:**

```python
import httpx
import time
from dataclasses import dataclass

@dataclass
class OAuth2Token:
    access_token: str
    token_type: str
    expires_at: float

    @property
    def is_expired(self) -> bool:
        return time.time() >= (self.expires_at - 60)


class NetSuiteAuth:
    """OAuth 2.0 authentication for NetSuite."""

    def __init__(self, account_id: str, client_id: str, client_secret: str):
        self.account_id = account_id
        self.client_id = client_id
        self.client_secret = client_secret
        self._token: OAuth2Token | None = None

    def get_access_token(self) -> str:
        """Get valid access token, refreshing if expired."""
        if self._token is None or self._token.is_expired:
            self._token = self._request_token()
        return self._token.access_token

    def _request_token(self) -> OAuth2Token:
        """Request new OAuth 2.0 token."""
        url = f"https://{self.account_id}.suitetalk.api.netsuite.com/services/rest/auth/oauth2/v1/token"

        response = httpx.post(
            url,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()

        token_data = response.json()
        return OAuth2Token(
            access_token=token_data["access_token"],
            token_type=token_data["token_type"],
            expires_at=time.time() + token_data["expires_in"],
        )
```

## Stage 2: Data Extraction

### Vendor Extraction

**SUITEQL Query:**

```sql
SELECT
    id,
    entityid,
    companyname,
    email,
    phone,
    billaddress,
    billcity,
    billstate,
    billzipcode,
    billcountry,
    terms,
    isinactive,
    datecreated,
    lastmodifieddate
FROM
    vendor
WHERE
    isinactive = 'F'
ORDER BY
    id
```

**Pagination Implementation:**

```python
from typing import Iterator
from pydantic import BaseModel

class Vendor(BaseModel):
    id: str
    entityid: str | None
    companyname: str | None
    email: str | None
    phone: str | None
    terms: str | None


def fetch_all_vendors(
    auth: NetSuiteAuth,
    account_id: str,
    page_size: int = 1000
) -> Iterator[Vendor]:
    """
    Fetch all vendors from NetSuite using pagination.

    Yields:
        Vendor objects validated with Pydantic
    """
    base_url = f"https://{account_id}.suitetalk.api.netsuite.com"
    offset = 0

    while True:
        query = f"""
            SELECT id, entityid, companyname, email, phone, terms
            FROM vendor
            WHERE isinactive = 'F'
            ORDER BY id
            LIMIT {page_size} OFFSET {offset}
        """

        response = httpx.get(
            f"{base_url}/services/rest/query/v1/suiteql",
            params={"q": query},
            headers={
                "Authorization": f"Bearer {auth.get_access_token()}",
                "Prefer": "transient"
            },
        )
        response.raise_for_status()

        result = response.json()
        items = result.get("items", [])

        for item in items:
            yield Vendor(**item)

        if len(items) < page_size:
            break

        offset += page_size


# Usage:
auth = NetSuiteAuth(account_id, client_id, client_secret)
vendors = list(fetch_all_vendors(auth, account_id))
print(f"Extracted {len(vendors)} vendors from NetSuite")
```

### Transaction Extraction

**Vendor Bills Query:**

```sql
SELECT
    t.id,
    t.tranid,
    t.entity AS vendor_id,
    t.trandate,
    t.duedate,
    t.amount,
    t.status,
    t.memo
FROM
    transaction t
WHERE
    t.type = 'VendBill'
    AND t.trandate >= '2024-01-01'
    AND t.voided = 'F'
ORDER BY
    t.trandate DESC
```

**Implementation:**

```python
class VendorBill(BaseModel):
    id: str
    tranid: str | None
    vendor_id: str
    trandate: str  # ISO date
    amount: float
    status: str | None


def fetch_vendor_bills(
    auth: NetSuiteAuth,
    account_id: str,
    start_date: str,
    page_size: int = 1000
) -> Iterator[VendorBill]:
    """Fetch vendor bills from NetSuite."""
    base_url = f"https://{account_id}.suitetalk.api.netsuite.com"
    offset = 0

    while True:
        query = f"""
            SELECT id, tranid, entity AS vendor_id, trandate, amount, status
            FROM transaction
            WHERE type = 'VendBill'
              AND trandate >= '{start_date}'
              AND voided = 'F'
            ORDER BY trandate DESC
            LIMIT {page_size} OFFSET {offset}
        """

        response = httpx.get(
            f"{base_url}/services/rest/query/v1/suiteql",
            params={"q": query},
            headers={
                "Authorization": f"Bearer {auth.get_access_token()}",
                "Prefer": "transient"
            },
        )
        response.raise_for_status()

        result = response.json()
        items = result.get("items", [])

        for item in items:
            yield VendorBill(**item)

        if len(items) < page_size:
            break

        offset += page_size
```

## Stage 3: Local Storage

### Database Schema

```python
from sqlalchemy import Column, String, Numeric, Date, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class VendorRecord(Base):
    """Local vendor record from NetSuite."""
    __tablename__ = "vendor_records"

    id = Column(String, primary_key=True)  # NetSuite internal ID
    entity_id = Column(String)
    company_name = Column(String)
    email = Column(String)
    phone = Column(String)
    terms = Column(String)
    is_inactive = Column(Boolean, default=False)
    synced_at = Column(DateTime)

    transactions = relationship("TransactionRecord", back_populates="vendor")


class TransactionRecord(Base):
    """Local transaction record from NetSuite."""
    __tablename__ = "transaction_records"

    id = Column(String, primary_key=True)
    vendor_id = Column(String, ForeignKey("vendor_records.id"), nullable=False)
    transaction_number = Column(String)
    transaction_date = Column(Date, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    status = Column(String)
    synced_at = Column(DateTime)

    vendor = relationship("VendorRecord", back_populates="transactions")
```

### Data Persistence

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from datetime import datetime

def persist_vendors(database_url: str, vendors: list[Vendor]) -> int:
    """
    Persist vendors to PostgreSQL.

    Returns:
        Number of vendors inserted/updated
    """
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        for vendor in vendors:
            # Upsert pattern
            existing = session.query(VendorRecord).filter_by(id=vendor.id).first()

            if existing:
                # Update existing
                existing.company_name = vendor.companyname
                existing.email = vendor.email
                existing.phone = vendor.phone
                existing.terms = vendor.terms
                existing.synced_at = datetime.utcnow()
            else:
                # Insert new
                record = VendorRecord(
                    id=vendor.id,
                    entity_id=vendor.entityid,
                    company_name=vendor.companyname,
                    email=vendor.email,
                    phone=vendor.phone,
                    terms=vendor.terms,
                    is_inactive=False,
                    synced_at=datetime.utcnow()
                )
                session.add(record)

        session.commit()
        return len(vendors)


def persist_transactions(database_url: str, bills: list[VendorBill]) -> int:
    """Persist transactions to PostgreSQL."""
    engine = create_engine(database_url)

    with Session(engine) as session:
        for bill in bills:
            existing = session.query(TransactionRecord).filter_by(id=bill.id).first()

            if not existing:
                record = TransactionRecord(
                    id=bill.id,
                    vendor_id=bill.vendor_id,
                    transaction_number=bill.tranid,
                    transaction_date=bill.trandate,
                    amount=bill.amount,
                    status=bill.status,
                    synced_at=datetime.utcnow()
                )
                session.add(record)

        session.commit()
        return len(bills)
```

## Stage 4: Analysis

### Vendor Spend Analysis

```python
import pandas as pd
from dataclasses import dataclass

@dataclass
class VendorSpendSummary:
    """Vendor spend analysis result."""
    vendor_id: str
    vendor_name: str
    total_spend: float
    transaction_count: int
    avg_transaction: float


def analyze_vendor_spend(database_url: str, top_n: int = 25) -> list[VendorSpendSummary]:
    """
    Analyze vendor spend using Pandas.

    Args:
        database_url: PostgreSQL connection string
        top_n: Number of top vendors to return

    Returns:
        List of top vendors by spend
    """
    engine = create_engine(database_url)

    # Load data into DataFrame
    query = """
        SELECT
            v.id AS vendor_id,
            v.company_name AS vendor_name,
            t.amount
        FROM
            vendor_records v
        JOIN
            transaction_records t ON v.id = t.vendor_id
        WHERE
            t.status != 'Voided'
    """
    df = pd.read_sql(query, engine)

    # Aggregate by vendor
    spend_summary = df.groupby(['vendor_id', 'vendor_name']).agg(
        total_spend=('amount', 'sum'),
        transaction_count=('amount', 'count')
    ).reset_index()

    spend_summary['avg_transaction'] = (
        spend_summary['total_spend'] / spend_summary['transaction_count']
    )

    # Sort and limit
    top_vendors = spend_summary.nlargest(top_n, 'total_spend')

    # Convert to dataclass
    results = [
        VendorSpendSummary(
            vendor_id=row['vendor_id'],
            vendor_name=row['vendor_name'],
            total_spend=float(row['total_spend']),
            transaction_count=int(row['transaction_count']),
            avg_transaction=float(row['avg_transaction'])
        )
        for _, row in top_vendors.iterrows()
    ]

    return results
```

### Duplicate Detection

```python
from difflib import SequenceMatcher

@dataclass
class DuplicatePair:
    """Potential duplicate vendor pair."""
    vendor_1_id: str
    vendor_1_name: str
    vendor_2_id: str
    vendor_2_name: str
    similarity_score: float


def detect_duplicate_vendors(
    database_url: str,
    threshold: float = 0.85
) -> list[DuplicatePair]:
    """
    Detect duplicate vendors using fuzzy matching.

    Args:
        database_url: PostgreSQL connection string
        threshold: Similarity threshold (0-1)

    Returns:
        List of potential duplicate pairs
    """
    engine = create_engine(database_url)

    with Session(engine) as session:
        vendors = session.query(VendorRecord).filter(
            VendorRecord.is_inactive == False,
            VendorRecord.company_name != None
        ).all()

    duplicates = []

    # O(n²) pairwise comparison
    for i, v1 in enumerate(vendors):
        for v2 in vendors[i+1:]:
            # Fuzzy match on company name
            similarity = SequenceMatcher(
                None,
                v1.company_name.lower(),
                v2.company_name.lower()
            ).ratio()

            if similarity >= threshold:
                duplicates.append(DuplicatePair(
                    vendor_1_id=v1.id,
                    vendor_1_name=v1.company_name,
                    vendor_2_id=v2.id,
                    vendor_2_name=v2.company_name,
                    similarity_score=similarity
                ))

    # Sort by similarity descending
    duplicates.sort(key=lambda d: d.similarity_score, reverse=True)

    return duplicates
```

## Stage 5: Reporting

### CLI Output with Rich Tables

```python
from rich.console import Console
from rich.table import Table

def display_spend_report(results: list[VendorSpendSummary]) -> None:
    """Display vendor spend report in terminal."""
    console = Console()

    table = Table(title="Top Vendors by Spend")
    table.add_column("Rank", justify="right", style="cyan")
    table.add_column("Vendor Name", style="green")
    table.add_column("Total Spend", justify="right", style="magenta")
    table.add_column("Transactions", justify="right", style="blue")
    table.add_column("Avg Transaction", justify="right", style="yellow")

    for rank, vendor in enumerate(results, start=1):
        table.add_row(
            str(rank),
            vendor.vendor_name or "Unknown",
            f"${vendor.total_spend:,.2f}",
            str(vendor.transaction_count),
            f"${vendor.avg_transaction:,.2f}"
        )

    console.print(table)


def display_duplicate_report(duplicates: list[DuplicatePair]) -> None:
    """Display duplicate vendors report."""
    console = Console()

    table = Table(title=f"Potential Duplicate Vendors ({len(duplicates)} pairs)")
    table.add_column("Vendor 1", style="cyan")
    table.add_column("Vendor 2", style="cyan")
    table.add_column("Similarity", justify="right", style="red")

    for dup in duplicates[:50]:  # Show top 50
        table.add_row(
            dup.vendor_1_name,
            dup.vendor_2_name,
            f"{dup.similarity_score * 100:.0f}%"
        )

    console.print(table)
```

## Stage 6: Orchestration

### Complete Pipeline Script

```python
#!/usr/bin/env python3
"""
Vendor analytics pipeline orchestration.

Usage:
    python pipeline.py sync       # Extract data from NetSuite
    python pipeline.py analyze    # Run spend analysis
    python pipeline.py duplicates # Detect duplicates
"""

import sys
from datetime import datetime

def run_sync(database_url: str, account_id: str, client_id: str, client_secret: str):
    """Sync vendors and transactions from NetSuite."""
    print("🔐 Authenticating with NetSuite...")
    auth = NetSuiteAuth(account_id, client_id, client_secret)

    print("📥 Extracting vendors...")
    vendors = list(fetch_all_vendors(auth, account_id))
    print(f"✓ Extracted {len(vendors)} vendors")

    print("💾 Persisting vendors to database...")
    vendor_count = persist_vendors(database_url, vendors)
    print(f"✓ Persisted {vendor_count} vendors")

    print("📥 Extracting transactions...")
    bills = list(fetch_vendor_bills(auth, account_id, start_date="2024-01-01"))
    print(f"✓ Extracted {len(bills)} vendor bills")

    print("💾 Persisting transactions to database...")
    bill_count = persist_transactions(database_url, bills)
    print(f"✓ Persisted {bill_count} transactions")

    print(f"\n✅ Sync completed at {datetime.now()}")


def run_analysis(database_url: str, top_n: int = 25):
    """Run vendor spend analysis."""
    print(f"📊 Analyzing vendor spend (top {top_n})...")
    results = analyze_vendor_spend(database_url, top_n)

    display_spend_report(results)

    total_spend = sum(v.total_spend for v in results)
    print(f"\n💰 Total spend (top {top_n}): ${total_spend:,.2f}")


def run_duplicate_detection(database_url: str, threshold: float = 0.85):
    """Run duplicate vendor detection."""
    print(f"🔍 Detecting duplicate vendors (threshold: {threshold})...")
    duplicates = detect_duplicate_vendors(database_url, threshold)

    display_duplicate_report(duplicates)

    print(f"\n⚠️  Found {len(duplicates)} potential duplicate pairs")


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python pipeline.py [sync|analyze|duplicates]")
        sys.exit(1)

    command = sys.argv[1]

    # Load config from .env
    database_url = "postgresql://user:password@localhost/vendor_analytics"
    account_id = "1234567"
    client_id = "abc123..."
    client_secret = "xyz789..."

    if command == "sync":
        run_sync(database_url, account_id, client_id, client_secret)
    elif command == "analyze":
        run_analysis(database_url, top_n=25)
    elif command == "duplicates":
        run_duplicate_detection(database_url, threshold=0.85)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

## Performance Metrics

**Typical Performance (1,000 vendors, 10,000 transactions):**

| Stage | Operation | Time | Notes |
|-------|-----------|------|-------|
| 1 | Authentication | <1s | Token cached for 1 hour |
| 2 | Vendor extraction | 5-10s | Depends on network latency |
| 2 | Transaction extraction | 15-30s | Pagination overhead |
| 3 | Database persist | 2-5s | Bulk insert pattern |
| 4 | Spend analysis | <1s | Pandas aggregation |
| 4 | Duplicate detection | 10-30s | O(n²) comparison |
| **Total** | **Full pipeline** | **45-90s** | End-to-end |

**Optimization Opportunities:**
- Incremental sync (only fetch changed records)
- Parallel requests (if rate limits allow)
- Blocking strategy for duplicate detection (reduce O(n²))
- Materialized views for common aggregations

## Related Documentation

- **[NetSuite Integration](../integrations/netsuite.md)** - API patterns and pagination
- **[PostgreSQL Integration](../integrations/postgresql.md)** - Database schema and queries
- **[Duplicate Detection](../reference/duplicate-detection.md)** - Fuzzy matching algorithms
- **[Cost Optimization](../reference/cost-optimization.md)** - Analyzing results for savings

**Reference Implementation:**
- [vendor-analysis CLI](/opt/ns/apps/vendor-analysis) - Production implementation of this pipeline

---

*Example pipeline demonstrating end-to-end vendor analytics workflow*
