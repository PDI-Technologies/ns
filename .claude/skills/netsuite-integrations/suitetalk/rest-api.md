# SuiteTalk REST API

Comprehensive guide to NetSuite's SuiteTalk REST API, including the critical 2-step query pattern and performance strategies for integrations.

## Overview

SuiteTalk REST API provides programmatic access to NetSuite data using standard HTTP methods and JSON payloads.

**Base URL:** `https://{accountId}.suitetalk.api.netsuite.com/services/rest/record/v1/`

**Authentication:** TBA (OAuth 1.0) or OAuth 2.0 required

**Rate Limiting:** Subject to NetSuite governance limits

---

## CRITICAL: Query vs Get Endpoints

NetSuite REST API has **two fundamentally different endpoint types** that developers must understand to avoid data loss.

### Query Endpoint (List Records)

**Pattern:** `GET /services/rest/record/v1/{recordType}`

**Examples:**
- `GET /vendor`
- `GET /customer`
- `GET /vendorBill`

**Returns:** **IDs ONLY** (plus pagination metadata)

**Response:**
```json
{
  "items": [
    {"id": "123", "links": [...]},
    {"id": "456", "links": [...]}
  ],
  "hasMore": false,
  "offset": 0,
  "count": 2,
  "totalResults": 2
}
```

**Missing:** All field data (companyName, email, balance, custom fields, etc.)

**Use case:** Get list of IDs, count records, check existence

### Get Endpoint (Single Record)

**Pattern:** `GET /services/rest/record/v1/{recordType}/{id}`

**Examples:**
- `GET /vendor/123`
- `GET /customer/456`
- `GET /vendorBill/789`

**Returns:** **Complete record with ALL fields**

**Response:**
```json
{
  "id": "123",
  "companyName": "Acme Corp",
  "email": "vendor@acme.com",
  "balance": 15000.00,
  "currency": {"id": "1", "refName": "USD"},
  "custentity_region": "West",
  "custentity_payment_method": "ACH",
  ... [40+ more fields]
}
```

**Includes:** Standard fields, custom fields, sub-resources, reference objects

**Use case:** Get complete data for processing, display, or storage

---

## 2-Step Query Pattern (REQUIRED)

To get complete data for multiple records, you **MUST** use a 2-step pattern. There is no single endpoint that returns both list and complete data.

### Why 2 Steps?

**NetSuite API design:**
- Query endpoint optimized for filtering and pagination (fast, lightweight)
- Get endpoint optimized for complete data retrieval (slower, detailed)
- No way to request full fields from query endpoint
- Parameters like `expandSubResources`, `fields`, `include` do **NOT** work on query endpoint

**This is fundamental API architecture, not a bug.**

### Step 1: Query for IDs

```python
def fetch_all_ids(client, record_type="vendor", page_size=100):
    """Query for all record IDs using pagination

    Returns:
        List of record IDs
    """
    ids = []
    offset = 0

    while True:
        # Query endpoint - returns IDs only
        response = client.get(
            f'/services/rest/record/v1/{record_type}',
            params={"limit": page_size, "offset": offset}
        )

        items = response.get("items", [])
        if not items:
            break

        # Extract IDs
        for item in items:
            ids.append(item["id"])

        # Check for more results
        if not response.get("hasMore", False):
            break

        offset += page_size

    return ids
```

**Result:** List of IDs like `["123", "456", "789", ...]`

**API calls:** ~90 calls for 9000 records (100 per page)

### Step 2: Fetch Full Records

```python
def fetch_full_records(client, record_type, ids):
    """Fetch complete record data for each ID

    Returns:
        List of complete records with all fields
    """
    records = []

    for record_id in ids:
        # Get endpoint - returns complete data
        record = client.get(f'/services/rest/record/v1/{record_type}/{record_id}')
        records.append(record)

    return records
```

**Result:** Complete records with 40-50+ fields each

**API calls:** One per record (9000 calls for 9000 records)

### Complete Implementation

```python
from rich.progress import Progress
from rich.console import Console

console = Console()

def fetch_all_records_complete(client, record_type="vendor", page_size=100):
    """Fetch complete records using 2-step pattern

    Args:
        client: Authenticated NetSuite client
        record_type: NetSuite record type
        page_size: Records per query page

    Returns:
        List of complete record dictionaries

    Performance:
        9000 records = ~9090 API calls total
        Time depends on NetSuite governance limits
    """
    # Step 1: Get all IDs
    console.print(f"[cyan]Fetching {record_type} IDs...[/cyan]")

    ids = []
    offset = 0

    while True:
        response = client.get(
            f'/services/rest/record/v1/{record_type}',
            params={"limit": page_size, "offset": offset}
        )

        items = response.get("items", [])
        if not items:
            break

        for item in items:
            ids.append(item["id"])

        if not response.get("hasMore", False):
            break

        offset += page_size

    console.print(f"[green]Found {len(ids)} {record_type} records[/green]")

    # Step 2: Fetch full data for each ID
    records = []

    with Progress() as progress:
        task = progress.add_task(
            f"[cyan]Fetching {record_type} data...",
            total=len(ids)
        )

        for record_id in ids:
            try:
                record = client.get(f'/services/rest/record/v1/{record_type}/{record_id}')
                records.append(record)
                progress.advance(task)
            except Exception as e:
                console.print(f"[red]Error fetching {record_type} {record_id}: {e}[/red]")
                continue

    return records
```

**Reference:** `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/queries.py`

---

## Performance Implications

### API Call Volume

**For 9000 vendors:**
- Step 1 (query): ~90 API calls (100 per page)
- Step 2 (fetch): 9000 API calls (one per vendor)
- **Total: ~9090 API calls**

**For 50,000 transactions:**
- Step 1: ~500 API calls
- Step 2: 50,000 API calls
- **Total: ~50,500 API calls**

### Time Estimates

Depends heavily on NetSuite governance limits and time of day.

**Best case** (no throttling):
- 9000 vendors @ 0.5s/call = ~75 minutes
- 50,000 transactions @ 0.5s/call = ~7 hours

**Realistic** (with throttling):
- 2-5x slower due to rate limits
- Unpredictable delays
- More expensive during peak NetSuite usage hours

### NetSuite Governance

NetSuite enforces usage limits:
- **Concurrent request limits** - Max simultaneous requests
- **Requests per minute** - Rate limiting
- **Total API usage** - Daily/weekly quotas
- **Limits vary** by account type and plan

**Impact:**
- Large syncs may hit governance
- Requests throttled or rejected (429 errors)
- Need retry logic with exponential backoff

---

## Optimization Strategies

### Strategy 1: Incremental Sync (Recommended)

Only fetch records changed since last sync.

```python
def fetch_incremental(client, record_type, last_sync_time):
    """Fetch only records modified since last sync

    Args:
        last_sync_time: ISO timestamp of last sync

    Returns:
        List of changed records
    """
    # Query with filter
    query = f"lastModifiedDate >= '{last_sync_time}'"

    # Step 1: Get changed IDs
    ids = []
    offset = 0

    while True:
        response = client.get(
            f'/services/rest/record/v1/{record_type}',
            params={"q": query, "limit": 100, "offset": offset}
        )

        items = response.get("items", [])
        if not items:
            break

        ids.extend([item["id"] for item in items])

        if not response.get("hasMore", False):
            break

        offset += 100

    # Step 2: Fetch full data only for changed records
    records = []
    for record_id in ids:
        record = client.get(f'/services/rest/record/v1/{record_type}/{record_id}')
        records.append(record)

    return records
```

**Benefits:**
- Drastically reduces API calls for subsequent syncs
- Only fetches what changed
- Much faster sync times after initial load

**Requirements:**
- Track last sync timestamp in database
- NetSuite records must have lastModifiedDate

### Strategy 2: Parallel Fetching

Fetch multiple records concurrently (careful with rate limits!).

```python
import asyncio
import httpx

async def fetch_record_async(client, record_type, record_id):
    """Async fetch for single record"""
    return await client.get_async(f'/services/rest/record/v1/{record_type}/{record_id}')

async def fetch_records_parallel(client, record_type, ids, batch_size=10):
    """Fetch records in parallel batches

    Args:
        ids: List of IDs to fetch
        batch_size: Concurrent requests per batch

    Returns:
        List of complete records
    """
    records = []

    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i:i+batch_size]

        # Fetch batch concurrently
        tasks = [fetch_record_async(client, record_type, rid) for rid in batch_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                console.print(f"[red]Error: {result}[/red]")
            else:
                records.append(result)

        # Respect rate limits
        await asyncio.sleep(1)

    return records
```

**Benefits:**
- 2-5x faster than sequential
- Better network utilization

**Risks:**
- Easy to hit rate limits
- More complex error handling
- Requires careful tuning of batch_size

**Recommendation:** Start sequential, add parallelization only if needed

### Strategy 3: Caching Full Records

Cache complete records to avoid re-fetching unchanged data.

```python
def fetch_with_cache(client, record_type, ids, cache_db):
    """Fetch records using cache when available

    Args:
        ids: IDs to fetch
        cache_db: Database with cached records

    Returns:
        List of records (from cache or fresh fetch)
    """
    records = []

    for record_id in ids:
        # Check cache first
        cached = cache_db.get_record(record_type, record_id)

        if cached and not is_stale(cached, max_age_hours=24):
            # Use cached version
            records.append(cached.data)
        else:
            # Fetch fresh data
            record = client.get(f'/services/rest/record/v1/{record_type}/{record_id}')
            cache_db.save_record(record_type, record_id, record)
            records.append(record)

    return records
```

**Benefits:**
- Reduces API calls significantly
- Faster subsequent operations
- Respects NetSuite governance

### Strategy 4: Batch Processing

Process large datasets in manageable batches with progress tracking.

```python
def fetch_in_batches(client, record_type, ids, batch_size=100):
    """Fetch and process records in batches

    Args:
        ids: All IDs to fetch
        batch_size: Records per batch

    Yields:
        Batches of records for processing
    """
    with Progress() as progress:
        task = progress.add_task(
            f"[cyan]Fetching {record_type}...",
            total=len(ids)
        )

        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i+batch_size]
            batch_records = []

            for record_id in batch_ids:
                try:
                    record = client.get(f'/services/rest/record/v1/{record_type}/{record_id}')
                    batch_records.append(record)
                except Exception as e:
                    console.print(f"[red]Error {record_id}: {e}[/red]")

                progress.advance(task)

            yield batch_records  # Process/store batch
            time.sleep(0.5)  # Rate limit respect

# Usage
for batch in fetch_in_batches(client, "vendor", all_ids):
    store_in_database(batch)  # Commit per batch
```

**Benefits:**
- User sees progress (not frozen)
- Can commit batches to database
- Resumable if interrupted
- Memory efficient (generator)

---

## Query Parameters

### Supported on Query Endpoint

**`limit`** - Records per page (default: 1000, max: 1000)
```
GET /vendor?limit=100
```

**`offset`** - Pagination offset
```
GET /vendor?limit=100&offset=100  # Page 2
```

**`q`** - SuiteQL filter expression
```
GET /vendor?q=isInactive IS FALSE
GET /vendor?q=lastModifiedDate >= '2025-01-01'
```

### NOT Supported (Common Mistakes)

**`expandSubResources`** - Returns 400 error
```
GET /vendor?expandSubResources=true
# ❌ ERROR: 400 Bad Request
```

**`fields`** - Ignored (still returns IDs only)
```
GET /vendor?fields=companyName,email
# ❌ Returns IDs only, parameter ignored
```

**`include`**, **`expand`** - Not recognized
```
GET /vendor?include=all
# ❌ Returns IDs only, parameter ignored
```

---

## Common Mistakes

### Mistake 1: Expecting Full Data from Query

```python
# ❌ WRONG - Only gets IDs!
response = client.get('/vendor?limit=100')
vendors = response['items']
for vendor in vendors:
    print(vendor['companyName'])  # KeyError - field doesn't exist!
```

**Fix:** Use 2-step pattern

### Mistake 2: Adding Params After Signature (TBA)

```python
# ❌ WRONG - Causes 401 with TBA
url = "/vendor"
headers = auth.get_headers(url)
response = client.get(url, params={"limit": 100}, headers=headers)
```

**Fix:** Build full URL with params before signature generation

See [tba.md](../authentication/tba.md#critical-bug-pattern) for details

### Mistake 3: No Pagination

```python
# ❌ WRONG - Only gets first 1000 records
response = client.get('/vendor?limit=1000')
ids = [item['id'] for item in response['items']]
# Missing records if total > 1000!
```

**Fix:** Loop until `hasMore` is false

### Mistake 4: No Error Handling

```python
# ❌ WRONG - Fails on first error, loses progress
for record_id in ids:
    record = client.get(f'/vendor/{record_id}')  # Fails if one record errors
    records.append(record)
```

**Fix:** Try-except with logging

---

## SuiteQL for Bulk Queries

**Endpoint:** `POST /services/rest/query/v1/suiteql`

Use SuiteQL for fetching 10+ records. It returns complete records in single requests instead of requiring individual fetches.

**Request:**
```json
{
  "q": "SELECT id, companyName, email FROM vendor WHERE isInactive = 'F'"
}
```

**Returns:** Complete records with requested fields. Supports pagination (limit/offset).

**Use SuiteQL for:**
- Bulk synchronization
- Regular exports
- Fetching 10+ records
- Any multi-record retrieval

**Use 2-step REST for:**
- Single record lookups
- Schema discovery
- Prototyping

**Note:** Custom fields may have different names in SuiteQL (e.g., `custentity_region` vs `custentityregion`). Test first.

---

## Related Documentation

**NetSuite Developer Skill:**
- `patterns/rest-api-queries.md` - Detailed 2-step pattern documentation
- `patterns/authentication-methods.md` - TBA and OAuth 2.0 setup
- `patterns/custom-fields.md` - Handling custentity_* fields
- `examples/vendor-sync-complete.md` - Complete working example

**This Skill (netsuite-integrations):**
- [tba.md](../authentication/tba.md) - TBA authentication
- [oauth2.md](../authentication/oauth2.md) - OAuth 2.0 authentication
- [patterns/schema-evolution.md](../patterns/schema-evolution.md) - Handling custom field changes
- [patterns/data-fetching.md](../patterns/data-fetching.md) - Advanced fetching strategies

**Local KB:**
- `/opt/ns/kb/suitetalk-rest-api.md` - SuiteTalk REST API basics

**Reference Implementation:**
- `/opt/ns/apps/vendor-analysis/` - Production 2-step implementation

---

## Summary

**Key Takeaways:**

1. **Query endpoint returns IDs ONLY** - fundamental API design
2. **2-step pattern is REQUIRED** for complete data - no workaround
3. **Performance: N+1 problem** - 9000 records = 9000+ API calls
4. **Optimize with incremental sync** - only fetch changed records
5. **Batch processing recommended** - manageable chunks, progress feedback
6. **Respect rate limits** - NetSuite governance enforced
7. **Cache when possible** - reduce redundant API calls

**This pattern is THE most important NetSuite REST API knowledge. Understanding and implementing it correctly is critical for any NetSuite integration.**
