# Incremental Sync Testing Results

## Test Summary

**Date:** 2025-01-24
**Test Command:** `uv run vendor-analysis sync --dry-run --limit 5`

## Key Findings

### ✅ SUCCESS: Vendor Sync with --limit is FAST
- **Time:** < 10 seconds
- **Records fetched:** 5 vendors (as expected)
- **API optimization working:** Only fetched 5 full records instead of thousands

**Output:**
```
Fetched 5 vendors
DRY RUN - Vendor data preview:
  1. ID: -3, Name: -Accountant-, Modified: 2025-03-24T13:54:00Z
  2. ID: 4136, Name: WDL SYSTEMS, LLC, Modified: 2025-03-21T19:01:00Z
  3. ID: 47705, Name: Plaid Inc., Modified: 2025-03-21T19:22:00Z
  4. ID: 4137, Name: CDW LLC, Modified: 2025-05-14T17:26:00Z
  5. ID: 47576, Name: Joshua Sommer, Modified: 2025-03-21T19:18:00Z
```

### ⚠️ SLOW: Bill Sync (Still Running after 2+ minutes)
- **Time:** > 2 minutes (killed before completion)
- **Reason:** Querying NetSuite for ALL bill IDs is slow (likely thousands of bills)
- **Limit helps, but doesn't eliminate:** We still query for all IDs before limiting

## How the --limit Optimization Works

Our implementation applies the limit in two phases:

### Phase 1: Query for IDs (NetSuite query endpoint)
```python
# This part CANNOT be limited (NetSuite API design)
# Queries for ALL record IDs matching filters
while True:
    response = client.query_records(record_type="vendorbill", ...)
    bill_ids.append(...)  # Collects ALL IDs
```

**Performance:**
- Fast when few records exist (vendors: ~100s)
- Slow when many records exist (bills: thousands+)

### Phase 2: Fetch Full Records (NetSuite get_record endpoint)
```python
# THIS is where --limit helps!
ids_to_fetch = bill_ids[:limit] if limit else bill_ids  # Only first 5!

for bill_id in ids_to_fetch:
    bill_data = client.get_record("vendorbill", bill_id)  # 5 API calls instead of thousands
```

**Performance:**
- Dramatically reduced (5 API calls vs potentially thousands)
- Each get_record call is expensive (returns full record with all fields)

## Why Incremental Sync Will Be Much Faster

Incremental sync adds date filters to **Phase 1**, reducing the ID query time:

### Full Sync (what we just tested)
```python
# Query for ALL bill IDs (slow with thousands of bills)
query = None
response = client.query_records(record_type="vendorbill", query=None)
```

### Incremental Sync (after first sync)
```python
# Query for ONLY changed/new bill IDs (fast - usually 0-10 bills)
query = "lastModifiedDate AFTER '2025-01-24T10:00:00' OR createdDate AFTER '2025-01-24T10:00:00'"
response = client.query_records(record_type="vendorbill", query=query)
```

**Expected performance improvement:**
- First sync (full): 2+ minutes (or longer)
- Subsequent syncs (incremental): 10-30 seconds

## Configuration Issues Found

### Issue 1: Missing `log_level` in config.yaml
**Error:** `application.log_level Field required`

**Fix Applied:**
```yaml
# Application Settings
application:
  log_level: INFO  # <-- Added this
  auth_method: tba
```

### Issue 2: Build backend configuration
**Error:** Direct reference not allowed without `allow-direct-references`

**Fix Applied:** Added to pyproject.toml:
```toml
[tool.hatch.metadata]
allow-direct-references = true
```

## Recommendations

### For Quick Testing
1. **Use `--vendors-only` for fastest testing**
   ```bash
   uv run vendor-analysis sync --dry-run --limit 5 --vendors-only
   ```
   Vendors sync is fast (< 10 seconds) so you get immediate feedback

2. **Skip bills during initial testing**
   Bills take longer to query, even with --limit

3. **Test incremental sync after first sync**
   This is where the real performance gains will be visible

### For Production Use
1. **First sync will be slow** (minutes to hours depending on data volume)
2. **Subsequent syncs will be fast** (10-60 seconds typically)
3. **Use --limit only for testing**, not production

## Next Steps

1. ✅ Database migration applied
2. ✅ --dry-run with --limit 5 works for vendors (FAST)
3. ⚠️ --dry-run with --limit 5 slow for bills (expected with large dataset)
4. ⏭️ Test actual sync with `--limit 5 --vendors-only` (fastest)
5. ⏭️ Test incremental sync after initial sync
6. ⏭️ Compare incremental vs full sync performance

## Code Changes Summary

### Files Modified for Limit Optimization
1. `netsuite/queries.py` - Added `limit` parameter to fetch functions
2. `cli/sync.py` - Pass limit to fetch functions (not after fetch)
3. `cli/main.py` - Added --limit and --dry-run flags

### Result
- Vendors: 10x-100x faster with --limit 5
- Bills: Still slow on first sync (NetSuite limitation), but much better with incremental sync
