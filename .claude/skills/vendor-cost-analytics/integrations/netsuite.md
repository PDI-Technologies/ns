# NetSuite Integration for Vendor Analytics

Patterns for integrating NetSuite vendor and transaction data into local analytics databases.

## Overview

NetSuite integration for vendor analytics requires read-only access via SuiteTalk REST API to extract vendor master data and transaction history for local analysis.

**Integration Goals:**
- Extract vendor records (company name, address, payment terms, contacts)
- Sync transaction history (vendor bills, payments, purchase orders)
- Maintain local analytics database (PostgreSQL, SQL Server, etc.)
- Enable offline analysis without impacting NetSuite performance
- Preserve data lineage (NetSuite ID mapping)

**Key Constraints:**
- Read-only operations (no writes to NetSuite)
- Pagination for large datasets (>1000 records)
- Rate limiting and retry logic
- Data validation at API boundary

**Technology Stack:**
- SuiteTalk REST API (NetSuite 2023.2+)
- OAuth 2.0 Client Credentials (recommended) or Token-Based Authentication
- Python httpx or Node.js axios for HTTP client
- Pydantic (Python) or Zod (TypeScript) for data validation

## Authentication

### OAuth 2.0 Client Credentials (Recommended)

OAuth 2.0 is the recommended authentication method for NetSuite integrations (TBA deprecated February 2025).

**Setup Requirements:**
1. Create Integration Record in NetSuite (Setup → Integrations → Manage Integrations)
2. Enable OAuth 2.0 authorization code grant
3. Note Client ID and Client Secret
4. Grant appropriate permissions (View Vendor, View Transaction)

**Python Implementation:**

```python
import time
from dataclasses import dataclass
import httpx

@dataclass
class OAuth2Token:
    """OAuth 2.0 access token with expiration."""
    access_token: str
    token_type: str
    expires_at: float  # Unix timestamp

    @property
    def is_expired(self) -> bool:
        """Check if token is expired (with 60s buffer)."""
        return time.time() >= (self.expires_at - 60)


class NetSuiteOAuth2Client:
    """OAuth 2.0 authentication for NetSuite."""

    TOKEN_ENDPOINT = "https://{account_id}.suitetalk.api.netsuite.com/services/rest/auth/oauth2/v1/token"

    def __init__(self, account_id: str, client_id: str, client_secret: str):
        self.account_id = account_id
        self.client_id = client_id
        self.client_secret = client_secret
        self._token: OAuth2Token | None = None

    def get_access_token(self) -> str:
        """Get valid access token, refreshing if needed."""
        if self._token is None or self._token.is_expired:
            self._token = self._request_new_token()
        return self._token.access_token

    def _request_new_token(self) -> OAuth2Token:
        """Request new OAuth 2.0 access token using client credentials."""
        url = self.TOKEN_ENDPOINT.format(account_id=self.account_id)

        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        response = httpx.post(
            url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30.0,
        )
        response.raise_for_status()

        token_data = response.json()

        return OAuth2Token(
            access_token=token_data["access_token"],
            token_type=token_data["token_type"],
            expires_at=time.time() + token_data["expires_in"],
        )

    def get_auth_headers(self) -> dict[str, str]:
        """Get authorization headers for API requests."""
        token = self.get_access_token()
        return {"Authorization": f"Bearer {token}"}
```

**Token Caching:**
- Tokens expire after 1 hour (3600 seconds)
- Cache tokens in memory with 60-second buffer before expiration
- Automatic refresh on expiration
- No need to store tokens persistently (client credentials can re-authenticate)

## Read-Only Enforcement

Enforce read-only access to prevent accidental data modifications.

**Pattern:**

```python
from typing import Literal

class ReadOnlyViolationError(Exception):
    """Raised when attempting write operations in read-only mode."""
    pass


class NetSuiteReadOnlyClient:
    """NetSuite client with read-only enforcement."""

    ALLOWED_METHODS: set[str] = {"GET", "HEAD", "OPTIONS"}

    def __init__(self, auth_client: NetSuiteOAuth2Client, base_url: str):
        self.auth = auth_client
        self.base_url = base_url
        self.http_client = httpx.Client()

    def _enforce_read_only(self, method: str) -> None:
        """Raise error if method is not read-only."""
        if method.upper() not in self.ALLOWED_METHODS:
            raise ReadOnlyViolationError(
                f"Write operation blocked: {method} not allowed in read-only mode. "
                f"Allowed methods: {', '.join(self.ALLOWED_METHODS)}"
            )

    def request(
        self,
        method: Literal["GET", "HEAD", "OPTIONS"],
        endpoint: str,
        **kwargs
    ) -> httpx.Response:
        """Make read-only HTTP request to NetSuite."""
        self._enforce_read_only(method)

        url = f"{self.base_url}{endpoint}"
        headers = self.auth.get_auth_headers()
        headers.update(kwargs.pop("headers", {}))

        response = self.http_client.request(
            method=method,
            url=url,
            headers=headers,
            **kwargs
        )
        response.raise_for_status()
        return response

    def get(self, endpoint: str, **kwargs) -> httpx.Response:
        """GET request to NetSuite."""
        return self.request("GET", endpoint, **kwargs)
```

**Benefits:**
- Prevents accidental POST/PUT/PATCH/DELETE operations
- Clear error messages when write operations attempted
- Type hints enforce read-only methods
- Safe for production analytics environments

## Pagination for Large Datasets

NetSuite queries return maximum 1000 records per request. Use offset-based pagination for complete data extraction.

**SUITEQL Pagination Pattern:**

```python
from typing import Iterator, TypeVar
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

def fetch_all_records(
    client: NetSuiteReadOnlyClient,
    query: str,
    model_class: type[T],
    page_size: int = 1000
) -> Iterator[T]:
    """
    Fetch all records using offset pagination.

    Args:
        client: NetSuite read-only client
        query: SUITEQL query (SELECT ... FROM ...)
        model_class: Pydantic model for validation
        page_size: Records per page (max 1000)

    Yields:
        Validated records as Pydantic models
    """
    offset = 0

    while True:
        # Add pagination to query
        paginated_query = f"{query} LIMIT {page_size} OFFSET {offset}"

        # Execute query
        response = client.get(
            "/services/rest/query/v1/suiteql",
            params={"q": paginated_query},
            headers={"Prefer": "transient"}
        )

        result = response.json()
        items = result.get("items", [])

        # Validate and yield each record
        for item in items:
            yield model_class(**item)

        # Check if more records available
        if len(items) < page_size:
            break

        offset += page_size


# Example usage:
def fetch_all_vendors(client: NetSuiteReadOnlyClient) -> list[Vendor]:
    """Fetch all vendors from NetSuite."""
    query = """
        SELECT
            id,
            companyname,
            email,
            phone,
            terms
        FROM
            vendor
        WHERE
            isinactive = 'F'
    """

    vendors = list(fetch_all_records(client, query, Vendor, page_size=1000))
    return vendors
```

**Performance Considerations:**
- Use `Prefer: transient` header to avoid server-side result caching
- Start with page_size=1000 (NetSuite max)
- Monitor for rate limiting (429 Too Many Requests)
- Process records in batches (don't load all into memory)

## REST API 2-Step Pattern (Alternative to SuiteQL)

For complete vendor data including all custom fields, use the 2-step REST API pattern instead of SuiteQL.

### Critical Difference

**SuiteQL:** Requires knowing exact field names, custom fields may have different names in SuiteQL

**REST API:** Returns all fields (standard + custom) automatically, no field name mapping needed

### 2-Step Pattern

**Step 1 - Query for IDs:**
```python
# Query endpoint returns IDs only (not full data)
response = client.get('/services/rest/record/v1/vendor', params={"limit": 100})
vendor_ids = [item["id"] for item in response["items"]]
```

**Step 2 - Fetch Full Records:**
```python
# Get endpoint returns complete data (all 50+ fields)
vendors = []
for vendor_id in vendor_ids:
    vendor = client.get(f'/services/rest/record/v1/vendor/{vendor_id}')
    vendors.append(vendor)  # Includes all custom fields!
```

**Why 2 steps:** NetSuite query endpoint returns IDs only. This is fundamental API design, not a bug.

**Reference:** See netsuite-integrations skill `suitetalk/rest-api.md` for complete implementation

**Use when:**
- Need all fields including custom fields
- Don't know exact custom field names
- Want raw NetSuite objects
- Prefer REST API over SuiteQL

## Custom Vendor Fields

NetSuite vendor records typically contain 20-40 custom fields beyond standard fields.

### Common Custom Fields

**Payment and terms:**
- `custentity_payment_method` - Preferred payment method (ACH, Check, Wire, etc.)
- `custentity_payment_terms` - Custom payment terms
- `custentity_credit_limit` - Custom credit limit

**Regional and organizational:**
- `custentity_region` - Geographic region
- `custentity_territory` - Sales territory
- `custentity_account_manager` - Account manager assignment

**Financial and risk:**
- `custentity_credit_rating` - Credit rating/score
- `custentity_risk_level` - Risk classification
- `custentity_vendor_tier` - Strategic vendor tier

**Operational:**
- `custentity_preferred_currency` - Currency preference
- `custentity_1099_eligible` - Tax reporting flag
- `custentity_minority_owned` - Diversity classification

### Field Discovery

**Don't hardcode custom field lists** - NetSuite admins can add/remove fields at any time.

Use flexible schema to capture all custom fields:

```python
from pydantic import BaseModel

class FlexibleVendor(BaseModel):
    # Standard fields
    id: str
    company_name: str
    balance: float

    class Config:
        extra = "allow"  # Automatically capture custom fields
```

**Or use JSONB storage:**
```python
# Split known vs custom fields
known_fields = {"id": "123", "companyName": "Acme", "balance": 15000}
custom_fields = {
    "custentity_region": "West",
    "custentity_payment_method": "ACH",
    ... (20-30 more custom fields)
}

# Store in database
vendor = VendorRecord(
    **known_fields,  # Typed columns
    custom_fields=custom_fields  # JSONB column
)
```

**Reference:** See python-cli-engineering skill `patterns/postgresql-jsonb.md` and netsuite-developer skill `patterns/custom-fields.md`

### Custom Field Analysis Use Cases

Custom fields often contain critical vendor metadata for analytics:

**Segmentation:**
- Group spend by region (custentity_region)
- Analyze by payment method (custentity_payment_method)
- Risk-based analysis (custentity_credit_rating)

**Duplicate detection:**
- Match vendors by regional coding
- Identify same vendor with different IDs using custom identifiers

**Optimization:**
- Payment term analysis (custentity_payment_terms)
- Preferred currency consolidation (custentity_preferred_currency)
- Strategic vendor identification (custentity_vendor_tier)

→ **See**: [workflows/custom-field-analysis.md](../workflows/custom-field-analysis.md) for complete patterns

## Data Validation with Pydantic

Validate NetSuite API responses at the boundary using Pydantic models.

**Vendor Model:**

```python
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

class Vendor(BaseModel):
    """NetSuite vendor record."""

    id: str = Field(..., min_length=1, description="NetSuite internal ID")
    companyname: str | None = Field(None, description="Vendor company name")
    email: str | None = Field(None, description="Primary email")
    phone: str | None = Field(None, description="Primary phone")
    terms: str | None = Field(None, description="Payment terms (e.g., 'Net 30')")

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Ensure ID is non-empty string."""
        if not v.strip():
            raise ValueError("Vendor ID cannot be empty")
        return v.strip()

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        """Basic email validation."""
        if v and "@" not in v:
            raise ValueError(f"Invalid email format: {v}")
        return v


class VendorBill(BaseModel):
    """NetSuite vendor bill transaction."""

    id: str = Field(..., description="Transaction internal ID")
    tranid: str | None = Field(None, description="Transaction number")
    entity: str = Field(..., description="Vendor internal ID")
    trandate: str = Field(..., description="Transaction date (ISO format)")
    amount: float = Field(..., description="Total amount")
    status: str | None = Field(None, description="Bill status")

    @field_validator("trandate")
    @classmethod
    def validate_date(cls, v: str) -> str:
        """Validate ISO date format."""
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except ValueError as e:
            raise ValueError(f"Invalid date format: {v}") from e
        return v
```

**Fail-Fast Validation:**
- Required fields raise ValidationError if missing
- Type coercion happens automatically (string → float)
- Custom validators for domain logic
- Clear error messages for debugging

## Retry Logic with Exponential Backoff

Handle transient failures with automatic retries.

**Retry Decorator:**

```python
import time
from functools import wraps
from typing import Callable, TypeVar

T = TypeVar('T')

def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    backoff_factor: float = 2.0,
    retriable_status_codes: set[int] = {429, 500, 502, 503, 504}
):
    """
    Retry decorator with exponential backoff.

    Args:
        max_retries: Maximum retry attempts
        base_delay: Initial delay in seconds
        backoff_factor: Multiplier for each retry
        retriable_status_codes: HTTP status codes to retry
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            delay = base_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except httpx.HTTPStatusError as e:
                    last_exception = e

                    if e.response.status_code not in retriable_status_codes:
                        raise  # Don't retry client errors (4xx)

                    if attempt == max_retries:
                        raise  # Max retries reached

                    time.sleep(delay)
                    delay *= backoff_factor

            raise last_exception  # Should never reach here

        return wrapper
    return decorator


# Usage:
class NetSuiteClientWithRetries(NetSuiteReadOnlyClient):
    """NetSuite client with automatic retries."""

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def get(self, endpoint: str, **kwargs) -> httpx.Response:
        """GET request with retries."""
        return super().get(endpoint, **kwargs)
```

**Retry Strategy:**
- Retry on 429 (rate limit), 500, 502, 503, 504 (server errors)
- Do NOT retry on 4xx client errors (bad request, auth failure)
- Exponential backoff: 1s, 2s, 4s
- Maximum 3 retries (4 total attempts)

## Complete Integration Example

**Full workflow from authentication to data extraction:**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# 1. Setup authentication
auth_client = NetSuiteOAuth2Client(
    account_id="1234567",
    client_id="your_client_id",
    client_secret="your_client_secret"
)

# 2. Create read-only client with retries
base_url = "https://1234567.suitetalk.api.netsuite.com"
netsuite_client = NetSuiteClientWithRetries(auth_client, base_url)

# 3. Fetch vendors with pagination
vendors = fetch_all_vendors(netsuite_client)
print(f"Fetched {len(vendors)} vendors from NetSuite")

# 4. Fetch vendor bills
query = """
    SELECT
        id,
        tranid,
        entity,
        trandate,
        amount,
        status
    FROM
        transaction
    WHERE
        type = 'VendBill'
        AND trandate >= '2024-01-01'
"""
bills = list(fetch_all_records(netsuite_client, query, VendorBill))
print(f"Fetched {len(bills)} vendor bills")

# 5. Store in local database (see integrations/postgresql.md)
engine = create_engine("postgresql://user:password@localhost/vendor_analytics")
with Session(engine) as session:
    # Insert vendors and bills into local database
    pass
```

## Configuration Management

**Dual-source configuration pattern:**

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Configuration from .env file.

    Fail-fast: All credentials are REQUIRED.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # NetSuite credentials (from .env)
    ns_account_id: str = Field(..., description="NetSuite account ID")
    ns_client_id: str = Field(..., description="OAuth 2.0 client ID")
    ns_client_secret: str = Field(..., description="OAuth 2.0 client secret")

    # Database credentials (from .env)
    db_user: str = Field(..., description="Database user")
    db_password: str = Field(..., description="Database password")


# .env file:
# NS_ACCOUNT_ID=1234567
# NS_CLIENT_ID=abc123...
# NS_CLIENT_SECRET=xyz789...
# DB_USER=analytics_user
# DB_PASSWORD=secure_password
```

**Best Practices:**
- Store credentials in `.env` file (never commit to git)
- Use Pydantic validation for fail-fast behavior
- No default values for required credentials
- Case-insensitive environment variable matching

## Error Handling

**Comprehensive error handling pattern:**

```python
class NetSuiteError(Exception):
    """Base exception for NetSuite integration errors."""
    pass

class NetSuiteConnectionError(NetSuiteError):
    """Failed to connect to NetSuite API."""
    pass

class NetSuiteAuthenticationError(NetSuiteError):
    """Authentication failure."""
    pass

class NetSuiteValidationError(NetSuiteError):
    """Data validation failure."""
    pass


def sync_vendors_with_error_handling():
    """Sync vendors with comprehensive error handling."""
    try:
        # Authenticate
        auth_client = NetSuiteOAuth2Client(...)
        token = auth_client.get_access_token()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise NetSuiteAuthenticationError("Invalid credentials") from e
        raise NetSuiteConnectionError(f"Failed to authenticate: {e}") from e

    try:
        # Fetch data
        client = NetSuiteReadOnlyClient(auth_client, base_url)
        vendors = fetch_all_vendors(client)
    except httpx.TimeoutError as e:
        raise NetSuiteConnectionError("Request timeout") from e
    except ValidationError as e:
        raise NetSuiteValidationError(f"Invalid vendor data: {e}") from e

    return vendors
```

## Performance Optimization

**Strategies for large datasets:**

1. **Parallel requests** (if rate limits allow):
```python
from concurrent.futures import ThreadPoolExecutor

def fetch_vendors_parallel(client: NetSuiteReadOnlyClient, date_ranges: list[tuple[str, str]]):
    """Fetch vendors in parallel by date range."""
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(fetch_vendors_for_range, client, start, end)
            for start, end in date_ranges
        ]
        results = [f.result() for f in futures]
    return results
```

2. **Incremental sync** (only fetch changed records):
```python
def fetch_vendors_since(client: NetSuiteReadOnlyClient, last_sync_date: str):
    """Fetch only vendors modified since last sync."""
    query = f"""
        SELECT * FROM vendor
        WHERE lastmodifieddate >= '{last_sync_date}'
    """
    return list(fetch_all_records(client, query, Vendor))
```

3. **Batch processing** (avoid loading all records into memory):
```python
def process_vendors_in_batches(client: NetSuiteReadOnlyClient, batch_size: int = 100):
    """Process vendors in batches to conserve memory."""
    batch = []
    for vendor in fetch_all_records(client, query, Vendor):
        batch.append(vendor)
        if len(batch) >= batch_size:
            process_batch(batch)
            batch = []
    if batch:
        process_batch(batch)
```

## Testing Considerations

**Mock NetSuite responses for testing:**

```python
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_netsuite_response():
    """Mock NetSuite vendor query response."""
    return {
        "items": [
            {"id": "1", "companyname": "Acme Corp", "email": "ap@acme.com"},
            {"id": "2", "companyname": "Tech Solutions", "email": "billing@tech.com"}
        ],
        "hasMore": False
    }

def test_fetch_vendors(mock_netsuite_response):
    """Test vendor fetching with mocked response."""
    with patch.object(NetSuiteReadOnlyClient, 'get') as mock_get:
        mock_get.return_value.json.return_value = mock_netsuite_response

        client = NetSuiteReadOnlyClient(...)
        vendors = fetch_all_vendors(client)

        assert len(vendors) == 2
        assert vendors[0].companyname == "Acme Corp"
```

## Related Documentation

- **[PostgreSQL Integration](postgresql.md)** - Local database storage patterns
- **[Data Quality](../reference/data-quality.md)** - Data cleansing after extraction
- **[Full Pipeline Example](../examples/full-pipeline.md)** - End-to-end integration workflow

**External References:**
- [NetSuite SuiteTalk REST API Guide](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/chapter_1540391670.html)
- [OAuth 2.0 Setup in NetSuite](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_157771482304.html)
- [SUITEQL Reference](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_156257770590.html)

---

*Based on production implementation in vendor-analysis CLI application*
