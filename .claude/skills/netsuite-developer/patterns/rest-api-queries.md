# NetSuite REST API Query Patterns

Critical patterns for fetching complete data from NetSuite REST API, including the 2-step query pattern and performance considerations.

## Contents

- The Critical Issue: Query vs Get Endpoints
- 2-Step Data Fetching Pattern (REQUIRED)
- Common Mistake and Correct Implementation
- Performance Implications
- Query Parameters Reference
- Optimization Strategies
- Related Patterns

---

## The Critical Issue: Query vs Get Endpoints

NetSuite REST API has **two types of endpoints** with fundamentally different behaviors:

### Query Endpoint Pattern

**Endpoint:** `GET /services/rest/record/v1/{recordType}`

**Examples:**
- `GET /vendor`
- `GET /customer`
- `GET /vendorBill`

**Returns:** **IDs ONLY** (plus links metadata)

**Response structure:**
```json
{
  "items": [
    {
      "id": "123",
      "links": [...]
    },
    {
      "id": "456",
      "links": [...]
    }
  ],
  "hasMore": false,
  "offset": 0,
  "count": 2,
  "totalResults": 2
}
```

**Missing:** All actual data fields (companyName, email, balance, custom fields, etc.)

**Use case:** Get list of record IDs, check existence, count records

### Get Endpoint Pattern

**Endpoint:** `GET /services/rest/record/v1/{recordType}/{id}`

**Examples:**
- `GET /vendor/123`
- `GET /customer/456`
- `GET /vendorBill/789`

**Returns:** **Complete record with ALL fields**

**Response structure:**
```json
{
  "id": "123",
  "companyName": "Acme Corp",
  "email": "vendor@acme.com",
  "balance": 15000.00,
  "currency": {"id": "1", "refName": "USD"},
  "custentity_region": "West",
  "custentity_payment_method": "ACH",
  ... [50+ more fields]
}
```

**Includes:** Standard fields, custom fields (custentity_*), sub-resources, reference objects

**Use case:** Get complete record data for processing, display, or storage

---

## 2-Step Data Fetching Pattern (REQUIRED)

To get complete data for multiple records, you MUST use a 2-step pattern.

### Why 2 Steps?

**NetSuite API design:**
- Query endpoint optimized for listing/filtering (fast, lightweight)
- Get endpoint optimized for complete data (slower, detailed)
- No single endpoint returns both list AND complete data
- No way to request full fields from query endpoint

**Attempts to bypass this fail:**
- Query parameter `expandSubResources` returns 400 error
- Query parameter `fields` not supported on query endpoint
- No "include" or "expand" parameters work

**This is fundamental NetSuite REST API design, not a bug.**

### Step 1: Query for IDs

```python
def fetch_all_vendor_ids(client, settings) -> list[str]:
    """Step 1: Get all vendor IDs using query endpoint

    Uses pagination to handle large datasets.

    Returns:
        List of vendor IDs (strings)
    """
    vendor_ids = []
    offset = 0
    page_size = settings.yaml_config.netsuite.page_size  # e.g., 100

    while True:
        # Query endpoint returns IDs only
        response = client.get(f'/vendor?limit={page_size}&offset={offset}')

        items = response.get("items", [])
        if not items:
            break  # No more results

        # Extract IDs
        for item in items:
            vendor_ids.append(item["id"])

        # Check pagination
        if not response.get("hasMore", False):
            break

        offset += page_size

    return vendor_ids
```

**Result:** List of IDs like `["123", "456", "789", ...]`

**API calls:** ~90 calls for 9000 vendors (100 per page)

### Step 2: Fetch Full Data for Each ID

```python
def fetch_vendor_data(client, vendor_id: str) -> dict:
    """Step 2: Get complete vendor data using get endpoint

    Args:
        vendor_id: Vendor ID from step 1

    Returns:
        Complete vendor record with all fields
    """
    # Get endpoint returns complete data
    vendor_data = client.get(f'/vendor/{vendor_id}')
    return vendor_data
```

**Result:** Complete vendor object with 50+ fields

**API calls:** 9000 calls for 9000 vendors (one per vendor)

### Complete 2-Step Implementation

```python
def fetch_all_vendors_raw(client, settings) -> list[dict]:
    """Fetch complete vendor data using 2-step pattern

    Step 1: Query for all IDs (fast, ~90 calls for 9000 vendors)
    Step 2: Fetch full data for each ID (slower, 9000 calls)

    Returns:
        List of complete vendor records with all fields

    Performance:
        9000 vendors = ~9090 API calls total
        Time depends on NetSuite rate limits
    """
    # Step 1: Get all vendor IDs
    vendor_ids = []
    offset = 0
    page_size = settings.yaml_config.netsuite.page_size

    console.print(f"[cyan]Fetching vendor IDs...[/cyan]")

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

**Reference:** `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/queries.py`

---

## Common Mistake vs Correct Implementation

### ❌ WRONG: Only Query Endpoint (Incomplete Data)

```python
# This looks like it should work, but only gets IDs!
def fetch_vendors_wrong(client):
    response = client.get('/vendor?limit=100')
    vendors = response['items']
    return vendors

# Result: List of dicts with ONLY 'id' and 'links'
# [
#   {"id": "123", "links": [...]},
#   {"id": "456", "links": [...]}
# ]
# Missing: companyName, email, balance, custom fields, EVERYTHING!
```

**Why this fails:**
- Code looks correct (no errors)
- Returns data (list of dictionaries)
- But data is incomplete (only IDs)
- Easy to miss until you try to access other fields
- Results in KeyError or missing data downstream

**Symptoms:**
- `KeyError: 'companyName'` when trying to access fields
- Database only stores IDs
- Analysis shows all vendors with null values
- "Why is all my vendor data missing?"

### ✅ CORRECT: 2-Step Pattern (Complete Data)

```python
def fetch_vendors_correct(client):
    # Step 1: Query for IDs
    response = client.get('/vendor?limit=100')
    vendor_ids = [item['id'] for item in response['items']]

    # Step 2: Fetch full data for each ID
    vendors = []
    for vendor_id in vendor_ids:
        full_data = client.get(f'/vendor/{vendor_id}')
        vendors.append(full_data)

    return vendors

# Result: List of complete vendor objects
# [
#   {
#     "id": "123",
#     "companyName": "Acme Corp",
#     "email": "vendor@acme.com",
#     "balance": 15000.00,
#     "custentity_region": "West",
#     ... [50+ more fields]
#   },
#   ...
# ]
```

**Why this works:**
- Step 1 gets IDs efficiently (paginated query)
- Step 2 gets complete data (individual get)
- All fields captured (standard + custom)
- Ready for processing and storage

---

## Performance Implications

### API Call Volume

**For 9000 vendors:**
- Step 1 (query): ~90 API calls (100 records per page)
- Step 2 (fetch): 9000 API calls (one per vendor)
- **Total: ~9090 API calls**

**For 50,000 transactions:**
- Step 1: ~500 API calls
- Step 2: 50,000 API calls
- **Total: ~50,500 API calls**

### Time Estimates

Actual time depends on NetSuite governance and rate limiting.

**Rough estimates (assuming no rate limit delays):**
- 9000 vendors @ 0.5s per call = ~75 minutes
- 50,000 transactions @ 0.5s per call = ~7 hours

**With rate limiting:**
- Can take 2-5x longer
- Unpredictable delays between requests
- NetSuite governance varies by account and time of day

### NetSuite Governance Limits

NetSuite enforces API usage limits:
- Concurrent request limits
- Requests per minute limits
- Total API usage limits (daily/weekly)
- Limits vary by account type and plan

**Impact:**
- Large syncs may hit governance limits
- Requests throttled or rejected
- Need retry logic with exponential backoff

---

## Query Parameters Reference

### Supported Parameters (Query Endpoint)

**`limit`** - Records per page (max: 1000, default: 1000)
```python
GET /vendor?limit=100
```

**`offset`** - Pagination offset
```python
GET /vendor?limit=100&offset=100  # Page 2
```

**`q`** - SuiteQL query filter (advanced)
```python
GET /vendor?q=isInactive IS FALSE
```

### NOT Supported (Common Mistakes)

**`expandSubResources`** - Returns 400 error
```python
# ❌ DOES NOT WORK
GET /vendor?limit=100&expandSubResources=true
# Error: 400 Bad Request
```

**`fields`** - Not supported on query endpoint
```python
# ❌ DOES NOT WORK
GET /vendor?limit=100&fields=companyName,email
# Returns IDs only (parameter ignored)
```

**`include`** / **`expand`** - Not recognized
```python
# ❌ DOES NOT WORK
GET /vendor?limit=100&include=all
# Returns IDs only (parameter ignored)
```

---

## Optimization Strategies

### Strategy 1: Incremental Sync

Only fetch records changed since last sync.

```python
def fetch_vendors_incremental(client, last_sync_time):
    """Fetch only vendors modified since last sync

    Uses SuiteQL to filter by lastModifiedDate.

    Args:
        last_sync_time: ISO format datetime of last sync

    Returns:
        List of changed vendor IDs
    """
    # Query with filter
    query = f"lastModifiedDate >= '{last_sync_time}'"
    response = client.get(f'/vendor?q={query}&limit=100')

    changed_ids = [item['id'] for item in response['items']]

    # Fetch full data only for changed records
    vendors = []
    for vendor_id in changed_ids:
        vendor = client.get(f'/vendor/{vendor_id}')
        vendors.append(vendor)

    return vendors
```

**Benefits:**
- Drastically reduces API calls for subsequent syncs
- Only fetches what changed
- Faster sync times

**Requirements:**
- Track last sync timestamp
- Store it in database or config

### Strategy 2: Parallel Fetching

Fetch multiple records concurrently (respect rate limits!).

```python
import asyncio
import httpx

async def fetch_vendor_async(client, vendor_id):
    """Async fetch for single vendor"""
    return await client.get_async(f'/vendor/{vendor_id}')

async def fetch_vendors_parallel(client, vendor_ids, batch_size=10):
    """Fetch vendors in parallel batches

    Args:
        vendor_ids: List of IDs to fetch
        batch_size: Concurrent requests per batch

    Returns:
        List of vendor records
    """
    vendors = []

    for i in range(0, len(vendor_ids), batch_size):
        batch = vendor_ids[i:i+batch_size]
        # Fetch batch concurrently
        tasks = [fetch_vendor_async(client, vid) for vid in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                console.print(f"[red]Error: {result}[/red]")
            else:
                vendors.append(result)

        # Rate limit respect
        await asyncio.sleep(1)

    return vendors
```

**Benefits:**
- Faster than sequential (2-5x speedup)
- Better network utilization

**Risks:**
- Easy to hit rate limits
- Must implement careful batching
- More complex error handling

**Recommendation:** Start with sequential; add parallelization only if needed and carefully.

### Strategy 3: Caching Full Records

Cache complete records to avoid re-fetching unchanged data.

```python
def fetch_with_cache(client, vendor_ids, cache_db):
    """Fetch vendors, using cache when available

    Args:
        vendor_ids: IDs to fetch
        cache_db: Database with cached vendor data

    Returns:
        List of vendor records (from cache or fresh fetch)
    """
    vendors = []

    for vendor_id in vendor_ids:
        # Check cache first
        cached = cache_db.get_vendor(vendor_id)

        if cached and not is_stale(cached):
            # Use cached version
            vendors.append(cached)
        else:
            # Fetch fresh data
            vendor = client.get(f'/vendor/{vendor_id}')
            cache_db.save_vendor(vendor)
            vendors.append(vendor)

    return vendors

def is_stale(cached_record, max_age_hours=24):
    """Check if cached record is too old"""
    age = datetime.now() - cached_record.fetched_at
    return age.total_seconds() > (max_age_hours * 3600)
```

**Benefits:**
- Reduces API calls significantly
- Faster subsequent syncs
- Respects NetSuite governance

**Considerations:**
- Need cache storage (database)
- Need staleness policy
- Track lastModifiedDate from NetSuite

### Strategy 4: Batch Processing with Progress

Process large datasets in manageable batches with user feedback.

```python
from rich.progress import Progress

def fetch_vendors_batched(client, vendor_ids, batch_size=100):
    """Fetch vendors in batches with progress tracking

    Args:
        vendor_ids: All IDs to fetch
        batch_size: Records to fetch before storage/commit

    Returns:
        Generator yielding batches of vendor records
    """
    with Progress() as progress:
        task = progress.add_task(
            "[cyan]Fetching vendors...",
            total=len(vendor_ids)
        )

        for i in range(0, len(vendor_ids), batch_size):
            batch_ids = vendor_ids[i:i+batch_size]
            batch_data = []

            for vendor_id in batch_ids:
                try:
                    vendor = client.get(f'/vendor/{vendor_id}')
                    batch_data.append(vendor)
                except Exception as e:
                    console.print(f"[red]Error {vendor_id}: {e}[/red]")

                progress.advance(task)

            yield batch_data  # Process/store batch
            time.sleep(0.5)  # Rate limit respect
```

**Benefits:**
- User sees progress (not frozen for hours)
- Can commit batches to database
- Resumable if interrupted
- Memory efficient (generator)

**Usage:**
```python
for vendor_batch in fetch_vendors_batched(client, all_ids):
    # Store batch in database
    store_vendors(vendor_batch)
    session.commit()  # Commit per batch
```

---

## SuiteQL for Bulk Queries

**Endpoint:** `POST /services/rest/query/v1/suiteql`

**Request:**
```json
{
  "q": "SELECT id, companyName, email FROM vendor WHERE isInactive = 'F'"
}
```

**Returns:** Complete records with requested fields. Supports pagination (limit/offset).

**Use SuiteQL for:**
- Fetching 10+ records
- Bulk synchronization
- Regular exports
- Any multi-record retrieval

**Use 2-step REST for:**
- Single record lookups
- Schema discovery
- Prototyping when field names unknown

**Note:** Custom fields may have different names in SuiteQL. Test first.

---

## Related Patterns

### Custom Field Handling

Fetched records contain custom fields (custentity_*, custbody_*).

See [custom-fields.md](custom-fields.md) for:
- Field classification strategies
- Reference field extraction
- JSONB storage patterns

### Authentication

Both query and get endpoints require authentication headers.

See [authentication-methods.md](authentication-methods.md) for:
- TBA (OAuth 1.0) implementation
- OAuth 2.0 implementation
- Critical: Query parameters must be in OAuth 1.0 signature

See [oauth-signatures.md](oauth-signatures.md) for:
- Signature generation including query params
- Common OAuth 1.0 bugs

### Schema Resilience

Complete records include many fields that may change over time.

See netsuite-integrations skill for:
- Schema evolution strategies
- JSONB storage for flexibility
- Merge patterns for historical data

---

## Summary: Key Takeaways

1. **Query endpoint returns IDs ONLY** - this is fundamental API design
2. **Get endpoint returns complete data** - all fields, standard and custom
3. **2-step pattern is REQUIRED** for complete data - no way to bypass
4. **Performance: N+1 problem** - 9000 vendors = ~9000 API calls
5. **Optimize with incremental sync** - only fetch changed records
6. **Use batch processing** - manageable chunks, progress feedback
7. **Respect rate limits** - NetSuite governance enforced
8. **Cache when possible** - reduce redundant fetches

**Reference Implementation:**
- Complete 2-step pattern: `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/queries.py`
- Client with retry logic: `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/client.py`
- Sync command with batching: `/opt/ns/apps/vendor-analysis/src/vendor_analysis/cli/sync.py`

**This pattern prevents the single most common NetSuite REST API mistake: thinking you have complete data when you only have IDs.**
