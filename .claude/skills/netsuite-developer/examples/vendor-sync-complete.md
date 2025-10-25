# Complete Vendor Sync Example

Real-world implementation showing all critical NetSuite REST API patterns working together: multi-method authentication, 2-step query, custom field handling, and schema-resilient storage.

## Overview

This example demonstrates the vendor-analysis application, a production Python CLI tool that syncs vendor data from NetSuite to PostgreSQL.

**Source code:** `/opt/ns/apps/vendor-analysis/`

**Patterns demonstrated:**
- Multi-method authentication (TBA and OAuth 2.0)
- 2-step REST API query pattern
- Custom field classification and processing
- JSONB-based schema-resilient storage
- Reference field extraction
- Error handling and diagnostics

---

## Architecture

```
CLI Command (sync)
    ↓
Configuration (load .env + config.yaml)
    ↓
Authentication Factory (create TBA or OAuth 2.0 provider)
    ↓
NetSuite Client (enforce read-only, handle retries)
    ↓
2-Step Query Pattern:
    Step 1: Query for IDs (pagination)
    Step 2: Fetch full records (one per ID)
    ↓
Field Processing (split known vs custom fields)
    ↓
Database Storage (typed columns + JSONB)
    ↓
CLI Output (Rich tables, progress bars)
```

---

## Key Files Reference

### Configuration
- **`.env`**: Credentials (NS_CONSUMER_KEY, NS_CONSUMER_SECRET, NS_TOKEN_ID, NS_TOKEN_SECRET, DB credentials)
- **`config.yaml`**: Application settings (database config, auth_method selection, page size, retries)
- **`core/config.py`**: Configuration loader with fail-fast validation

### Authentication
- **`netsuite/auth_base.py`**: Abstract base class for auth providers
- **`netsuite/auth_tba.py`**: TBA (OAuth 1.0) implementation
- **`netsuite/auth.py`**: OAuth 2.0 implementation
- **`netsuite/auth_factory.py`**: Factory to create appropriate provider

### Data Fetching
- **`netsuite/client.py`**: NetSuite HTTP client with read-only enforcement, retry logic
- **`netsuite/queries.py`**: 2-step query pattern implementation
- **`netsuite/models.py`**: Pydantic models with extra="allow"

### Custom Field Processing
- **`core/field_config.py`**: Known field definitions (VENDOR_KNOWN_FIELDS)
- **`netsuite/field_processor.py`**: Field classification, reference extraction, merge strategy

### Database
- **`db/models.py`**: SQLAlchemy ORM with hybrid schema (typed + JSONB columns)
- **`db/session.py`**: Database connection management
- **`db/query_helpers.py`**: JSONB query helpers

### CLI
- **`cli/main.py`**: Typer app entry point
- **`cli/sync.py`**: Sync command with batch processing

### Diagnostics
- **`scripts/diagnose_auth.py`**: Test authentication without NetSuite UI access

---

## Pattern 1: Multi-Method Authentication

**File:** `netsuite/auth_factory.py`

```python
def create_auth_provider(settings: Settings) -> NetSuiteAuthProvider:
    """Create appropriate auth provider based on configuration

    Supports both TBA (OAuth 1.0) and OAuth 2.0
    """
    auth_method = settings.yaml_config.application.auth_method.lower()

    if auth_method == "tba":
        return TBAAuthProvider(settings)
    elif auth_method == "oauth2":
        return OAuth2AuthProvider(settings)
    else:
        raise ValueError(f"Unknown auth method: {auth_method}")
```

**Configuration:**

```yaml
# config.yaml
application:
  auth_method: tba  # or "oauth2"
```

```bash
# .env
NS_ACCOUNT_ID=610574

# For TBA: 4 credentials
NS_CONSUMER_KEY=...
NS_CONSUMER_SECRET=...
NS_TOKEN_ID=...
NS_TOKEN_SECRET=...

# For OAuth 2.0: 2 credentials only
# NS_CONSUMER_KEY=...
# NS_CONSUMER_SECRET=...
```

**Pattern details:** See [patterns/authentication-methods.md](../patterns/authentication-methods.md)

---

## Pattern 2: OAuth 1.0 Signature with Query Params

**File:** `netsuite/auth_tba.py`

```python
def _generate_signature(self, url: str, method: str, oauth_params: dict) -> str:
    """Generate OAuth 1.0 signature

    CRITICAL: Includes query parameters from URL in signature
    """
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"

    # Combine OAuth params with query params (CRITICAL!)
    all_params = dict(oauth_params)
    if parsed_url.query:
        query_params = parse_qsl(parsed_url.query)
        all_params.update({k: str(v) for k, v in query_params})

    # Sort and build parameter string
    params = sorted(all_params.items())
    param_string = "&".join(
        f"{quote(str(k), safe='')}={quote(str(v), safe='')}"
        for k, v in params
    )

    # Build signature base string
    signature_base_string = (
        f"{method.upper()}&"
        f"{quote(base_url, safe='')}&"
        f"{quote(param_string, safe='')}"
    )

    # Sign with HMAC-SHA256
    signing_key = f"{self.consumer_secret}&{self.token_secret}"
    signature_bytes = hmac.new(
        key=signing_key.encode("utf-8"),
        msg=signature_base_string.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()

    return base64.b64encode(signature_bytes).decode("utf-8")
```

**Pattern details:** See [patterns/oauth-signatures.md](../patterns/oauth-signatures.md)

---

## Pattern 3: Client URL Construction (Critical for Signatures)

**File:** `netsuite/client.py`

```python
def _request(self, method: str, endpoint: str, params=None):
    """Make authenticated HTTP request

    CRITICAL: Build full URL with query params BEFORE generating auth headers
    """
    self._enforce_read_only(method)

    # Build full URL including query parameters
    base_url = f"{self.base_url}/{endpoint}"

    if params:
        query_string = urlencode(params)
        full_url = f"{base_url}?{query_string}"
    else:
        full_url = base_url

    # Get auth headers using FULL URL (with query params)
    headers = {
        **self.auth.get_auth_headers(url=full_url, method=method),
        "Accept": "application/json",
    }

    # Make request (params already in URL)
    response = self.client.request(method=method, url=full_url, headers=headers)

    # Retry logic for rate limits
    if response.status_code == 429:
        time.sleep(2)
        response = self.client.request(method=method, url=full_url, headers=headers)

    response.raise_for_status()
    return response.json()
```

---

## Pattern 4: 2-Step Query Pattern

**File:** `netsuite/queries.py`

```python
def fetch_all_vendors_raw(client, settings) -> list[dict]:
    """Fetch complete vendor data using 2-step pattern

    Step 1: Query for all IDs (fast, ~90 calls for 9000 vendors)
    Step 2: Fetch full data for each ID (slower, 9000 calls)

    Returns complete vendor records with all fields (standard + custom)
    """
    # Step 1: Get all vendor IDs
    vendor_ids = []
    offset = 0
    page_size = settings.yaml_config.netsuite.page_size

    console.print("[cyan]Fetching vendor IDs...[/cyan]")

    while True:
        response = client.query_records(
            record_type="vendor",
            limit=page_size,
            offset=offset
        )

        items = response.get("items", [])
        if not items:
            break

        for item in items:
            vendor_ids.append(item["id"])

        if not response.get("hasMore", False):
            break

        offset += page_size

    console.print(f"[green]Found {len(vendor_ids)} vendors[/green]")

    # Step 2: Fetch full vendor data for each ID
    vendor_data_list = []

    with Progress() as progress:
        task = progress.add_task(
            "[cyan]Fetching vendor data...",
            total=len(vendor_ids)
        )

        for vendor_id in vendor_ids:
            try:
                vendor_data = client.get_record("vendor", vendor_id)
                vendor_data_list.append(vendor_data)
                progress.advance(task)
            except Exception as e:
                console.print(f"[red]Error fetching vendor {vendor_id}: {e}[/red]")
                continue

    return vendor_data_list
```

**Pattern details:** See [patterns/rest-api-queries.md](../patterns/rest-api-queries.md)

---

## Pattern 5: Field Classification

**File:** `core/field_config.py`

```python
VENDOR_KNOWN_FIELDS: Final[frozenset[str]] = frozenset([
    # Identity
    "id", "entityId", "companyName", "legalName",

    # Contact
    "email", "phone", "fax", "url",

    # Financial
    "balance", "unbilledOrders", "currency", "terms",

    # Status
    "isInactive", "isPerson",

    # Metadata
    "lastModifiedDate", "dateCreated",

    # Sub-resources
    "addressBook", "contactList", "currencyList",
])

def is_known_field(field_name: str, record_type: str) -> bool:
    """Check if field is known (standard)"""
    if record_type.lower() == "vendor":
        return field_name in VENDOR_KNOWN_FIELDS
    return False
```

**Pattern details:** See [patterns/custom-fields.md](../patterns/custom-fields.md)

---

## Pattern 6: Custom Field Processing

**File:** `netsuite/field_processor.py`

```python
def process_vendor_fields(raw_data: dict) -> tuple[dict, dict]:
    """Split vendor data into known vs custom fields

    Args:
        raw_data: Complete vendor record from NetSuite

    Returns:
        Tuple of (known_fields, custom_fields)
    """
    known = {}
    custom = {}

    for key, value in raw_data.items():
        if key in VENDOR_KNOWN_FIELDS:
            # Process known field with type-specific extraction
            if key in ("currency", "terms", "category"):
                # Extract reference value
                known[key] = extract_reference_value(value)
            else:
                known[key] = value
        else:
            # Unknown field = custom field
            custom[key] = value

    return known, custom

def extract_reference_value(field):
    """Extract meaningful value from NetSuite reference object

    NetSuite returns: {"id": "1", "refName": "USD", "links": [...]}
    Extract: "USD"
    """
    if not isinstance(field, dict):
        return field

    # Prefer refName (human-readable)
    if "refName" in field:
        return field["refName"]

    # Fallback to id
    if "id" in field:
        return field["id"]

    return field

def merge_custom_fields(existing, new, sync_timestamp):
    """Merge custom fields, preserving historical data with lifecycle tracking"""
    if existing is None:
        existing = {}

    merged = {}
    all_fields = set(existing.keys()) | set(new.keys())

    for field in all_fields:
        if field in new:
            # Field is present in new data
            merged[field] = {
                "value": new[field],
                "last_seen": sync_timestamp.isoformat(),
                "deprecated": False,
                "first_seen": (
                    existing.get(field, {}).get("first_seen") or
                    sync_timestamp.isoformat()
                ),
            }
        else:
            # Field removed from NetSuite (preserve historical data)
            merged[field] = existing[field]
            merged[field]["deprecated"] = True

    return merged
```

---

## Pattern 7: Hybrid Database Schema

**File:** `db/models.py`

```python
class VendorRecord(Base):
    """Vendor record with hybrid schema (typed + JSONB)"""
    __tablename__ = "vendors"

    # Typed columns for known fields (fast queries, type-safe)
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    company_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    is_inactive: Mapped[bool] = mapped_column(Boolean, default=False)
    last_modified_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # JSONB columns for flexible fields (schema-resilient)
    custom_fields: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Custom NetSuite fields (custentity_*) with metadata"
    )
    raw_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Complete NetSuite response for auditing"
    )

    # Metadata
    synced_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    schema_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
```

---

## Pattern 8: Sync Implementation

**File:** `cli/sync.py`

```python
@app.command()
def sync(
    vendors_only: bool = False,
    transactions_only: bool = False
):
    """Sync vendor data from NetSuite to database"""
    settings = get_settings()
    client = NetSuiteClient(settings)
    session = get_session(settings)

    sync_timestamp = datetime.now()
    schema_version = int(sync_timestamp.timestamp())

    # Fetch all vendors (2-step pattern)
    vendor_data_list = fetch_all_vendors_raw(client, settings)

    # Process and store vendors
    for raw_vendor in vendor_data_list:
        # Split known vs custom fields
        known_fields, custom_fields = process_vendor_fields(raw_vendor)

        # Check if vendor exists
        existing = session.query(VendorRecord).filter_by(
            id=known_fields["id"]
        ).first()

        if existing:
            # Update existing vendor
            for key, value in known_fields.items():
                setattr(existing, key, value)

            # Merge custom fields (preserves historical data)
            existing.custom_fields = merge_custom_fields(
                existing.custom_fields,
                custom_fields,
                sync_timestamp
            )
            existing.raw_data = raw_vendor
            existing.synced_at = sync_timestamp
            existing.schema_version = schema_version
        else:
            # Create new vendor
            enhanced_custom = merge_custom_fields(
                None,
                custom_fields,
                sync_timestamp
            )

            new_vendor = VendorRecord(
                **known_fields,
                custom_fields=enhanced_custom,
                raw_data=raw_vendor,
                synced_at=sync_timestamp,
                schema_version=schema_version
            )
            session.add(new_vendor)

    session.commit()
    console.print(f"[green]Synced {len(vendor_data_list)} vendors[/green]")
```

---

## Running the Example

```bash
# Navigate to app
cd /opt/ns/apps/vendor-analysis

# Install dependencies
uv sync

# Initialize database
uv run vendor-analysis init-db

# Test authentication
uv run python scripts/diagnose_auth.py

# Sync vendors
uv run vendor-analysis sync --vendors-only

# Analyze vendor spend
uv run vendor-analysis analyze --top 25

# Find duplicate vendors
uv run vendor-analysis duplicates --threshold 0.90
```

---

## Key Learnings

1. **2-step pattern is REQUIRED** - Query returns IDs only, must fetch full records individually
2. **Query params must be in signature** - OAuth 1.0 bug causes 401 if params added after signature
3. **Custom fields are everywhere** - 20-40 per record type, must use flexible schema
4. **JSONB enables resilience** - Schema changes don't break the application
5. **Reference extraction simplifies storage** - Store "USD" not {"id": "1", "refName": "USD"}
6. **Lifecycle tracking prevents data loss** - Track first_seen, last_seen, deprecated
7. **Multi-method auth enables migration** - Support both TBA and OAuth 2.0 during transition

---

## Related Patterns

- **Authentication Methods**: [patterns/authentication-methods.md](../patterns/authentication-methods.md)
- **OAuth Signatures**: [patterns/oauth-signatures.md](../patterns/oauth-signatures.md)
- **REST API Queries**: [patterns/rest-api-queries.md](../patterns/rest-api-queries.md)
- **Custom Fields**: [patterns/custom-fields.md](../patterns/custom-fields.md)
- **Diagnostics**: [testing/diagnostics-without-ui.md](../testing/diagnostics-without-ui.md)

For schema resilience and JSONB patterns, see python-cli-engineering skill.
