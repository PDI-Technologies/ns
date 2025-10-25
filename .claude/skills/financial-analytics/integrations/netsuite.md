# NetSuite Financial Data Integration

Extract financial data from NetSuite for analysis, reporting, and dashboard applications.

## Overview

NetSuite provides multiple methods to extract financial data:
- **SuiteTalk REST API** - Standard REST endpoints for record operations
- **SuiteQL** - SQL-like queries for complex data extraction
- **RESTlets** - Custom endpoints with SuiteScript logic
- **Saved Searches** - Pre-configured queries accessible via API

## Authentication

### OAuth 2.0 (Required 2025+)

NetSuite now requires OAuth 2.0 for all integrations. TBA was deprecated in February 2025.

**Client Credentials Flow** (recommended for financial applications):

```python
import httpx
from datetime import datetime, timedelta

class NetSuiteAuth:
    def __init__(self, account_id: str, client_id: str, client_secret: str):
        self.account_id = account_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None
        self.token_expires_at = None

    def get_access_token(self) -> str:
        """Request OAuth 2.0 access token."""
        if self.token and self.token_expires_at > datetime.now():
            return self.token

        url = f"https://{self.account_id}.suitetalk.api.netsuite.com/rest/oauth2/token"

        response = httpx.post(
            url,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        data = response.json()
        self.token = data["access_token"]
        # Token expires in 3600 seconds, refresh 60 seconds early
        self.token_expires_at = datetime.now() + timedelta(seconds=data["expires_in"] - 60)

        return self.token

    def get_auth_headers(self) -> dict:
        """Get headers with current access token."""
        return {"Authorization": f"Bearer {self.get_access_token()}"}
```

**Setup Steps:**
1. Navigate to Setup > Integration > Manage Integrations > New
2. Enable OAuth 2.0 on Authentication tab
3. Note Consumer Key (client_id) and Consumer Secret (client_secret)
4. Configure redirect URI if using authorization code flow

**See Also:** `/opt/ns/kb/authentication.md`

## SuiteTalk REST API

### Base URL Structure

```
https://{account_id}.suitetalk.api.netsuite.com/services/rest/record/v1/{recordType}
```

### Common Financial Record Types

| Record Type | Use Case | Key Fields |
|-------------|----------|------------|
| `vendor` | Vendor master data | companyName, email, balance, terms |
| `vendorBill` | AP transactions | entity (vendor), amount, dueDate, tranDate |
| `customer` | Customer master data | companyName, balance, terms |
| `invoice` | AR transactions | entity (customer), amount, dueDate, tranDate |
| `account` | Chart of accounts | acctName, acctNumber, acctType |
| `transaction` | General ledger | type, entity, amount, tranDate |
| `journalEntry` | Manual journal entries | subsidiary, lines, tranDate |

### Query Operations

**Fetch records with pagination:**

```python
class NetSuiteClient:
    def __init__(self, auth: NetSuiteAuth, account_id: str):
        self.auth = auth
        self.base_url = f"https://{account_id}.suitetalk.api.netsuite.com/services/rest/record/v1"
        self.client = httpx.Client(timeout=30.0)

    def query_records(
        self,
        record_type: str,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        """Query records with pagination."""
        url = f"{self.base_url}/{record_type}"
        headers = {
            **self.auth.get_auth_headers(),
            "Accept": "application/json",
        }

        params = {
            "limit": limit,
            "offset": offset,
        }

        response = self.client.get(url, headers=headers, params=params)
        response.raise_for_status()

        return response.json()

    def fetch_all_records(self, record_type: str, page_size: int = 100) -> list:
        """Fetch all records handling pagination."""
        all_records = []
        offset = 0

        while True:
            response = self.query_records(record_type, limit=page_size, offset=offset)
            items = response.get("items", [])

            if not items:
                break

            all_records.extend(items)

            if not response.get("hasMore", False):
                break

            offset += page_size

        return all_records
```

**Get single record by ID:**

```python
def get_record(self, record_type: str, record_id: str) -> dict:
    """Get single record by internal ID."""
    url = f"{self.base_url}/{record_type}/{record_id}"
    headers = {
        **self.auth.get_auth_headers(),
        "Accept": "application/json",
    }

    response = self.client.get(url, headers=headers)
    response.raise_for_status()

    return response.json()
```

### Example: Vendor Spend Analysis

```python
from pydantic import BaseModel
from datetime import date

class Vendor(BaseModel):
    id: str
    companyName: str
    email: str | None = None
    balance: float = 0.0
    terms: str | None = None

class VendorBill(BaseModel):
    id: str
    tranId: str  # Transaction number
    entity: str  # Vendor ID
    amount: float
    tranDate: date
    dueDate: date | None = None
    status: str

def fetch_vendor_spend_data(client: NetSuiteClient):
    """Fetch vendors and bills for spend analysis."""
    # Fetch all vendors
    vendor_data = client.fetch_all_records("vendor")
    vendors = [Vendor(**v) for v in vendor_data]

    # Fetch all vendor bills
    bill_data = client.fetch_all_records("vendorBill")
    bills = [VendorBill(**b) for b in bill_data]

    return vendors, bills
```

**See Also:** `/opt/ns/apps/vendor-analysis/` for complete implementation

## SuiteQL Queries

SuiteQL provides SQL-like syntax for complex queries.

### Endpoint

```
POST /services/rest/query/v1/suiteql
Content-Type: application/json

{
  "q": "SELECT field1, field2 FROM table WHERE condition"
}
```

### Financial Query Examples

**Vendor spend by period:**

```sql
SELECT
    v.companyname,
    SUM(t.foreignamount) as total_spend,
    COUNT(t.id) as transaction_count,
    TO_CHAR(t.trandate, 'YYYY-MM') as period
FROM
    transaction t
    JOIN vendor v ON t.entity = v.id
WHERE
    t.type = 'VendBill'
    AND t.trandate >= ADD_MONTHS(SYSDATE, -12)
GROUP BY
    v.companyname,
    TO_CHAR(t.trandate, 'YYYY-MM')
ORDER BY
    period DESC, total_spend DESC
```

**General ledger balance by account:**

```sql
SELECT
    a.acctnumber,
    a.acctname,
    a.accttype,
    SUM(tl.debitamount - tl.creditamount) as balance
FROM
    transactionline tl
    JOIN account a ON tl.account = a.id
WHERE
    tl.posting = 'T'
GROUP BY
    a.acctnumber, a.acctname, a.accttype
ORDER BY
    a.acctnumber
```

**Outstanding AR aging:**

```sql
SELECT
    c.companyname,
    SUM(CASE WHEN SYSDATE - t.duedate <= 30 THEN t.foreignamount ELSE 0 END) as current,
    SUM(CASE WHEN SYSDATE - t.duedate BETWEEN 31 AND 60 THEN t.foreignamount ELSE 0 END) as days_31_60,
    SUM(CASE WHEN SYSDATE - t.duedate BETWEEN 61 AND 90 THEN t.foreignamount ELSE 0 END) as days_61_90,
    SUM(CASE WHEN SYSDATE - t.duedate > 90 THEN t.foreignamount ELSE 0 END) as over_90
FROM
    transaction t
    JOIN customer c ON t.entity = c.id
WHERE
    t.type = 'CustInvc'
    AND t.status = 'CustInvc:A'  -- Open invoices
GROUP BY
    c.companyname
ORDER BY
    c.companyname
```

### Python Implementation

```python
def execute_suiteql(client: NetSuiteClient, query: str) -> list[dict]:
    """Execute SuiteQL query."""
    url = f"{client.base_url.replace('/record/v1', '/query/v1/suiteql')}"
    headers = {
        **client.auth.get_auth_headers(),
        "Content-Type": "application/json",
        "Prefer": "transient",  # Don't cache results
    }

    response = client.client.post(
        url,
        headers=headers,
        json={"q": query}
    )
    response.raise_for_status()

    data = response.json()
    return data.get("items", [])
```

**See Also:** `/opt/ns/kb/suitetalk-rest-api.md`

## Data Extraction Patterns

### Pattern 1: Full Sync

Extract complete dataset periodically for local analysis.

```python
import pandas as pd
from sqlalchemy import create_engine

def full_vendor_sync(ns_client: NetSuiteClient, db_url: str):
    """Full sync: NetSuite -> Local Database."""
    # Extract from NetSuite
    vendors, bills = fetch_vendor_spend_data(ns_client)

    # Convert to DataFrames
    vendors_df = pd.DataFrame([v.model_dump() for v in vendors])
    bills_df = pd.DataFrame([b.model_dump() for b in bills])

    # Load to database
    engine = create_engine(db_url)
    vendors_df.to_sql("vendors", engine, if_exists="replace", index=False)
    bills_df.to_sql("vendor_bills", engine, if_exists="replace", index=False)
```

**Use Cases:**
- Nightly data warehouse refresh
- Monthly financial close data extraction
- Quarterly reporting data prep

### Pattern 2: Incremental Sync

Extract only changed records since last sync.

```python
from datetime import datetime, timedelta

def incremental_sync(
    ns_client: NetSuiteClient,
    db_engine,
    last_sync_time: datetime
):
    """Incremental sync using lastModifiedDate."""
    # SuiteQL query for changed records
    query = f"""
        SELECT * FROM vendor
        WHERE lastmodifieddate > TO_DATE('{last_sync_time.isoformat()}', 'YYYY-MM-DD HH24:MI:SS')
    """

    changed_vendors = execute_suiteql(ns_client, query)

    # Upsert to database
    vendors_df = pd.DataFrame(changed_vendors)
    vendors_df.to_sql(
        "vendors",
        db_engine,
        if_exists="append",
        index=False,
        method="multi"  # Batch insert
    )
```

**Use Cases:**
- Real-time analytics dashboards
- Continuous data synchronization
- Minimizing API usage

### Pattern 3: On-Demand Extraction

Extract specific data when needed for analysis.

```python
def extract_vendor_analysis_data(
    ns_client: NetSuiteClient,
    start_date: date,
    end_date: date
) -> pd.DataFrame:
    """Extract vendor spend for specific period."""
    query = f"""
        SELECT
            v.id as vendor_id,
            v.companyname as vendor_name,
            t.tranid,
            t.amount,
            t.trandate
        FROM transaction t
        JOIN vendor v ON t.entity = v.id
        WHERE
            t.type = 'VendBill'
            AND t.trandate BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY t.trandate DESC
    """

    data = execute_suiteql(ns_client, query)
    return pd.DataFrame(data)
```

**Use Cases:**
- Ad-hoc analysis requests
- Custom date range reports
- Executive dashboard queries

## Error Handling

### Retry Logic with Exponential Backoff

```python
import time

def request_with_retry(
    func,
    max_retries: int = 3,
    base_delay: float = 1.0
):
    """Execute function with exponential backoff retry."""
    last_error = None

    for attempt in range(max_retries):
        try:
            return func()
        except httpx.HTTPStatusError as e:
            last_error = e

            # Don't retry client errors (4xx)
            if 400 <= e.response.status_code < 500:
                raise

            # Retry server errors (5xx) with backoff
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)

    raise last_error
```

### Rate Limit Handling

```python
def handle_rate_limit(response: httpx.Response):
    """Handle NetSuite rate limiting."""
    if response.status_code == 429:
        retry_after = response.headers.get("Retry-After", "60")
        wait_seconds = int(retry_after)

        print(f"Rate limited. Waiting {wait_seconds} seconds...")
        time.sleep(wait_seconds)

        return True

    return False
```

## Best Practices

### Performance Optimization

1. **Use pagination** - Fetch in batches (100-1000 records)
2. **Filter at source** - Use WHERE clauses in SuiteQL
3. **Select specific fields** - Don't fetch all columns
4. **Batch operations** - Group API calls when possible
5. **Cache results** - Store frequently accessed data locally

### Data Validation

```python
from decimal import Decimal

def validate_financial_record(record: dict):
    """Validate financial data integrity."""
    # Ensure critical fields exist
    required = ["id", "tranDate", "amount"]
    missing = [f for f in required if f not in record]
    if missing:
        raise ValueError(f"Missing fields: {missing}")

    # Validate amount is numeric
    try:
        amount = Decimal(str(record["amount"]))
    except:
        raise ValueError(f"Invalid amount: {record['amount']}")

    # Validate date format
    try:
        tranDate = datetime.fromisoformat(record["tranDate"])
    except:
        raise ValueError(f"Invalid date: {record['tranDate']}")

    return True
```

### Read-Only Enforcement

```python
class ReadOnlyNetSuiteClient(NetSuiteClient):
    """Client that only allows GET operations."""

    ALLOWED_METHODS = {"GET"}

    def _enforce_read_only(self, method: str):
        """Raise error if attempting write operations."""
        if method.upper() not in self.ALLOWED_METHODS:
            raise ReadOnlyViolationError(
                f"CRITICAL: Attempted {method} operation. "
                f"This client is READ-ONLY."
            )

    def request(self, method: str, *args, **kwargs):
        """Override to enforce read-only."""
        self._enforce_read_only(method)
        return super().request(method, *args, **kwargs)
```

**See Example:** `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/client.py`

## Complete Example

See the vendor-analysis CLI application for a production-ready implementation:
- **Location:** `/opt/ns/apps/vendor-analysis/`
- **Features:** OAuth 2.0 auth, pagination, retry logic, read-only enforcement
- **Tech Stack:** Python 3.12+, httpx, Pydantic, SQLAlchemy

## Official Documentation

- **SuiteTalk REST API:** https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N3748057
- **OAuth 2.0 Setup:** https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N250541
- **SuiteQL Reference:** https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_156257770590

## Related Skills

- **netsuite-developer** - Building SuiteScript customizations
- **netsuite-integrations** - Complete integration patterns
- **vendor-cost-analytics** - Specialized vendor analysis workflows
