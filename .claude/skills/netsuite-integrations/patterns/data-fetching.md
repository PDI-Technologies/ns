# Data Fetching Strategies for NetSuite Integrations

Performance patterns for efficiently fetching large datasets from NetSuite while respecting governance limits.

## Overview

NetSuite integrations often need to fetch thousands of records. The 2-step REST API pattern (query IDs → fetch full records) creates an N+1 problem requiring optimization.

**Challenge:**
- 9000 vendors = ~9090 API calls
- 50,000 transactions = ~50,500 API calls
- NetSuite governance limits apply
- Can take hours without optimization

**Solutions:**
- Incremental sync (only fetch changed records)
- Parallel fetching (concurrent requests)
- Caching (avoid redundant fetches)
- Batch processing (progress tracking, resumable)

---

## Strategy 1: Full Sync (Baseline)

Simple but slow - fetch all records every time.

### Implementation

```python
def full_sync(client, record_type="vendor"):
    """Complete sync of all records

    Step 1: Query all IDs
    Step 2: Fetch each full record

    Returns:
        List of all records
    """
    # Step 1: Get all IDs
    ids = []
    offset = 0

    while True:
        response = client.get(
            f'/services/rest/record/v1/{record_type}',
            params={"limit": 100, "offset": offset}
        )

        items = response.get("items", [])
        if not items:
            break

        ids.extend([item["id"] for item in items])

        if not response.get("hasMore", False):
            break

        offset += 100

    # Step 2: Fetch all full records
    records = []
    for record_id in ids:
        record = client.get(f'/services/rest/record/v1/{record_type}/{record_id}')
        records.append(record)

    return records
```

### Performance

**9000 vendors:**
- API calls: ~9090
- Time: 75-300 minutes (depending on rate limits)

**Use when:**
- Initial sync (first time)
- Infrequent syncs (weekly/monthly)
- Small datasets (< 1000 records)

---

## Strategy 2: Incremental Sync (Recommended)

Only fetch records changed since last sync - drastically reduces API calls.

### Implementation

```python
from datetime import datetime

def incremental_sync(client, record_type, last_sync_time):
    """Fetch only records modified since last sync

    Args:
        last_sync_time: ISO timestamp string (e.g., "2025-01-24T10:00:00")

    Returns:
        List of changed records
    """
    # Step 1: Query for changed IDs
    query = f"lastModifiedDate >= '{last_sync_time}'"

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

### Performance

**Initial sync:** Same as full sync (~9090 API calls)

**Subsequent syncs** (if 50 vendors changed):
- API calls: ~51 (1 query + 50 fetches)
- Time: < 1 minute
- **99% reduction** in API calls!

### Requirements

**Track last sync time:**
```python
# Store in database
class SyncMetadata(Base):
    __tablename__ = "sync_metadata"
    record_type = Column(String, primary_key=True)
    last_sync_time = Column(DateTime)

# Update after successful sync
metadata = session.query(SyncMetadata).filter_by(record_type="vendor").first()
metadata.last_sync_time = datetime.now()
session.commit()
```

**NetSuite records must have lastModifiedDate:**
- Most standard records have this field
- Custom records may not
- Verify field exists before using incremental sync

---

## Strategy 3: Parallel Fetching

Fetch multiple records concurrently to reduce wall-clock time.

### Implementation (Async)

```python
import asyncio
import httpx

async def fetch_record_async(client, record_type, record_id, semaphore):
    """Async fetch with concurrency control

    Args:
        semaphore: Limits concurrent requests
    """
    async with semaphore:
        response = await client.get_async(
            f'/services/rest/record/v1/{record_type}/{record_id}'
        )
        return response

async def parallel_fetch(client, record_type, ids, max_concurrent=10):
    """Fetch records in parallel with concurrency limit

    Args:
        ids: Record IDs to fetch
        max_concurrent: Max simultaneous requests

    Returns:
        List of fetched records
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    tasks = [
        fetch_record_async(client, record_type, rid, semaphore)
        for rid in ids
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out errors
    records = [r for r in results if not isinstance(r, Exception)]

    return records
```

### Performance

**Sequential:** 9000 records @ 0.5s each = 4500 seconds (75 minutes)

**Parallel (10 concurrent):** 9000 records @ 0.5s / 10 = 450 seconds (7.5 minutes)

**Speedup:** 10x faster

### Risks and Considerations

**Rate limiting:**
- NetSuite has concurrent request limits
- Too many parallel requests = 429 errors
- Must tune `max_concurrent` parameter

**Error handling:**
- One failure shouldn't stop all requests
- Use `return_exceptions=True` in gather
- Log and retry failed requests

**Best practice:**
- Start with `max_concurrent=5`
- Monitor 429 errors
- Increase gradually if no errors
- Decrease if seeing throttling

---

## Strategy 4: Caching

Cache full records to avoid redundant fetches.

### Implementation

```python
from datetime import datetime, timedelta

class RecordCache:
    """Cache for NetSuite records with TTL"""

    def __init__(self, db_session, ttl_hours=24):
        self.session = db_session
        self.ttl_hours = ttl_hours

    def get(self, record_type, record_id):
        """Get record from cache if not stale"""
        cache_entry = self.session.query(CachedRecord).filter_by(
            record_type=record_type,
            record_id=record_id
        ).first()

        if not cache_entry:
            return None

        # Check if stale
        age = datetime.now() - cache_entry.fetched_at
        if age.total_seconds() > (self.ttl_hours * 3600):
            return None  # Stale

        return cache_entry.data

    def set(self, record_type, record_id, data):
        """Store record in cache"""
        cache_entry = self.session.query(CachedRecord).filter_by(
            record_type=record_type,
            record_id=record_id
        ).first()

        if cache_entry:
            cache_entry.data = data
            cache_entry.fetched_at = datetime.now()
        else:
            new_entry = CachedRecord(
                record_type=record_type,
                record_id=record_id,
                data=data,
                fetched_at=datetime.now()
            )
            self.session.add(new_entry)

        self.session.commit()

def fetch_with_cache(client, record_type, ids, cache):
    """Fetch records using cache"""
    records = []

    cache_hits = 0
    cache_misses = 0

    for record_id in ids:
        # Try cache first
        cached = cache.get(record_type, record_id)

        if cached:
            records.append(cached)
            cache_hits += 1
        else:
            # Fetch from NetSuite
            record = client.get(f'/services/rest/record/v1/{record_type}/{record_id}')
            cache.set(record_type, record_id, record)
            records.append(record)
            cache_misses += 1

    print(f"Cache hits: {cache_hits}, misses: {cache_misses}")
    return records
```

### Performance

**First run:** Same as full sync (populate cache)

**Subsequent runs** (within TTL):
- Cache hit rate: ~90-95%
- API calls: ~500 (5-10% misses out of 9000)
- Time: < 5 minutes
- **95% reduction** in API calls!

---

## Strategy 5: Batch Processing

Process large datasets in manageable batches with progress tracking.

### Implementation

```python
from rich.progress import Progress

def fetch_in_batches(client, record_type, ids, batch_size=100):
    """Fetch and process records in batches

    Args:
        ids: All IDs to fetch
        batch_size: Records per batch

    Yields:
        Batches of records for processing/storage
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
                    progress.advance(task)
                except Exception as e:
                    console.print(f"[red]Error {record_id}: {e}[/red]")
                    progress.advance(task)

            yield batch_records
            time.sleep(0.5)  # Respect rate limits

# Usage
for batch in fetch_in_batches(client, "vendor", all_ids, batch_size=100):
    # Process batch
    store_in_database(batch)
    db_session.commit()  # Commit per batch
```

### Benefits

- **Progress visibility:** User sees real-time progress
- **Resumable:** Can restart from last committed batch
- **Memory efficient:** Generator pattern, doesn't load all records at once
- **Rate limiting:** Sleep between batches
- **Error resilience:** One failure doesn't stop entire sync

---

## Combined Strategy (Production Pattern)

Combine multiple strategies for optimal performance.

### Recommended Approach

```python
def smart_sync(client, record_type, last_sync_time=None, use_cache=True, max_concurrent=5):
    """Intelligent sync combining multiple strategies

    1. Incremental if last_sync_time provided
    2. Parallel fetching for speed
    3. Caching to avoid redundant fetches
    4. Batch processing for progress/resumability

    Args:
        last_sync_time: ISO timestamp for incremental sync (None = full sync)
        use_cache: Enable caching
        max_concurrent: Parallel request limit

    Returns:
        List of fetched records
    """
    # Step 1: Get IDs (incremental if possible)
    if last_sync_time:
        query = f"lastModifiedDate >= '{last_sync_time}'"
        ids = query_ids(client, record_type, query)  # Incremental
    else:
        ids = query_ids(client, record_type, None)   # Full

    # Step 2: Fetch with caching and parallelization
    records = []

    if use_cache:
        cache = RecordCache(db_session, ttl_hours=24)

        # Separate cached from non-cached
        cached_records = []
        fetch_ids = []

        for record_id in ids:
            cached = cache.get(record_type, record_id)
            if cached:
                cached_records.append(cached)
            else:
                fetch_ids.append(record_id)

        # Fetch missing records in parallel
        if fetch_ids:
            fetched = await parallel_fetch(client, record_type, fetch_ids, max_concurrent)

            # Update cache
            for record in fetched:
                cache.set(record_type, record["id"], record)

        records = cached_records + fetched
    else:
        # No cache - just parallel fetch
        records = await parallel_fetch(client, record_type, ids, max_concurrent)

    return records
```

### Performance Matrix

| Strategy | Initial Sync | Subsequent Sync | Complexity |
|----------|--------------|-----------------|------------|
| Full Sync | 75 min | 75 min | Low |
| + Incremental | 75 min | < 1 min | Low |
| + Parallel | 7.5 min | < 1 min | Medium |
| + Caching | 7.5 min | < 30 sec | Medium |
| **Combined** | **7.5 min** | **< 30 sec** | **High** |

---

## Handling Governance Limits

### Retry with Exponential Backoff

```python
import time

def fetch_with_retry(client, url, max_retries=3):
    """Fetch with exponential backoff on rate limits

    Args:
        url: API endpoint URL
        max_retries: Max retry attempts

    Returns:
        Response JSON
    """
    for attempt in range(max_retries):
        try:
            response = client.get(url)
            return response
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:  # Rate limit
                # Exponential backoff: 1s, 2s, 4s
                wait = 2 ** attempt
                console.print(f"[yellow]Rate limited, waiting {wait}s...[/yellow]")
                time.sleep(wait)
            else:
                raise  # Other errors, don't retry

    raise Exception(f"Failed after {max_retries} retries")
```

### Throttling

Deliberately slow down requests to stay under limits.

```python
import time

def fetch_with_throttle(client, ids, requests_per_minute=100):
    """Fetch with rate limiting

    Args:
        ids: Record IDs
        requests_per_minute: Max requests per minute

    Returns:
        List of records
    """
    records = []
    delay = 60.0 / requests_per_minute  # Seconds between requests

    for record_id in ids:
        record = client.get(f'/services/rest/record/v1/vendor/{record_id}')
        records.append(record)

        time.sleep(delay)  # Throttle

    return records
```

---

## Related Patterns

**This Skill:**
- [suitetalk/rest-api.md](../suitetalk/rest-api.md) - 2-step query pattern
- [schema-evolution.md](schema-evolution.md) - Schema-resilient storage
- [authentication/tba.md](../authentication/tba.md) - TBA authentication
- [authentication/oauth2.md](../authentication/oauth2.md) - OAuth 2.0 authentication

**NetSuite Developer Skill:**
- `patterns/rest-api-queries.md` - Detailed 2-step pattern
- `examples/vendor-sync-complete.md` - Production implementation

**Reference Implementation:**
- `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/queries.py` - Fetching strategies
- `/opt/ns/apps/vendor-analysis/src/vendor_analysis/cli/sync.py` - Batch processing

---

## Summary

**Key Takeaways:**

1. **Incremental sync is critical** - Reduces 9000 calls to 50 calls (99% reduction)
2. **Parallel fetching for speed** - 10x faster but requires careful tuning
3. **Caching prevents redundant fetches** - 95% reduction in API calls
4. **Batch processing for UX** - Progress bars, resumability, memory efficiency
5. **Combine strategies** - Incremental + parallel + caching = optimal
6. **Respect governance limits** - Retry with exponential backoff, throttling
7. **Track last sync time** - Required for incremental sync

**Recommended approach:** Start with incremental + batch processing, add parallelization only if needed, add caching for frequently accessed data.
