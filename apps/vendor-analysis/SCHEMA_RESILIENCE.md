# Schema-Resilient Custom Fields

This document explains the custom fields implementation that makes the vendor-analysis application resilient to NetSuite schema changes.

## Problem Statement

NetSuite allows custom fields that can be added, modified, or removed at any time:
- Custom vendor fields: `custentity_*` (e.g., `custentity_payment_method`, `custentity_region`)
- Custom transaction fields: `custbody_*` (e.g., `custbody_department`, `custbody_project`)

**Traditional approach problems:**
1. **Schema brittleness** - Adding/removing fields breaks the application
2. **Data loss** - Removing DB columns destroys historical data
3. **Slow evolution** - Requires code changes for every NetSuite field change
4. **Incomplete data** - Can't capture all fields without knowing them in advance

## Solution Architecture

### Three-Layer Separation

```
┌─────────────────────────────────────┐
│ NetSuite API (Source of Truth)     │
│ - Returns 50+ fields                │
│ - Schema changes over time          │
└─────────────────────────────────────┘
                ↓
┌─────────────────────────────────────┐
│ Database Storage (Historical)       │
│ - Typed columns: Known fields       │
│ - JSONB columns: Custom fields      │
│ - Never destroys data               │
└─────────────────────────────────────┘
                ↓
┌─────────────────────────────────────┐
│ Application Code (Current)          │
│ - Queries only relevant fields      │
│ - Gracefully handles missing fields │
│ - No references to deprecated fields│
└─────────────────────────────────────┘
```

### Database Schema

```sql
CREATE TABLE vendors (
    -- Typed columns (known, stable fields)
    id VARCHAR(50) PRIMARY KEY,
    company_name VARCHAR(500),
    email VARCHAR(255),
    balance FLOAT,
    -- ...other known fields

    -- JSONB columns (flexible, evolving schema)
    custom_fields JSONB,        -- Custom fields with lifecycle metadata
    raw_data JSONB,              -- Complete NetSuite response
    schema_version INTEGER,      -- Tracks field availability

    synced_at TIMESTAMP
);

CREATE INDEX idx_vendors_custom_fields_gin ON vendors USING GIN (custom_fields);
```

### Custom Fields Structure

Custom fields are stored with lifecycle metadata:

```json
{
  "custentity_region": {
    "value": "West",
    "first_seen": "2024-01-15T10:30:00",
    "last_seen": "2025-01-24T15:45:00",
    "deprecated": false
  },
  "custentity_old_field": {
    "value": "legacy_value",
    "first_seen": "2023-05-10T08:00:00",
    "last_seen": "2024-12-01T12:00:00",
    "deprecated": true
  }
}
```

## Field Classification

Fields are classified into two categories in `core/field_config.py`:

### Known Fields (Typed Columns)
- NetSuite standard fields unlikely to change
- Examples: `id`, `companyName`, `email`, `balance`
- Stored in typed PostgreSQL columns
- Fast queries, indexed

### Custom Fields (JSONB)
- NetSuite custom fields (`custentity_*`, `custbody_*`)
- Unknown fields not in the known list
- Stored in JSONB column
- Flexible, queryable with GIN indexes

## Sync Process

### Step 1: Fetch Complete Data
```python
# NetSuite query endpoint only returns IDs
vendor_ids = query_for_ids()

# Fetch full record for each ID (includes ALL fields)
for vendor_id in vendor_ids:
    complete_data = client.get_record('vendor', vendor_id)
```

### Step 2: Split Fields
```python
from vendor_analysis.netsuite.field_processor import process_vendor_fields

known_fields, custom_fields = process_vendor_fields(complete_data)
# known_fields: {id, company_name, email, ...}
# custom_fields: {custentity_region, custentity_payment_method, ...}
```

### Step 3: Merge with Existing
```python
from vendor_analysis.netsuite.field_processor import merge_custom_fields

# Preserves fields that disappeared from NetSuite
merged = merge_custom_fields(existing_custom_fields, new_custom_fields, timestamp)
```

### Step 4: Store Everything
```python
vendor = VendorRecord(
    **known_fields,
    custom_fields=merged,
    raw_data=complete_data,
    schema_version=sync_timestamp
)
```

## Querying Custom Fields

### Using SQLAlchemy

```python
from vendor_analysis.db.query_helpers import CustomFieldQuery

# Find vendors in "West" region
vendors = CustomFieldQuery.get_vendor_by_custom_field(
    session, "custentity_region", "West"
)

# Find all vendors that have a payment_method field
vendors = CustomFieldQuery.get_vendors_with_field(
    session, "custentity_payment_method"
)

# List all custom fields
fields = CustomFieldQuery.list_all_custom_fields(session)
# Result: {"custentity_region": 5000, "custentity_payment_method": 4800, ...}
```

### Using SQL

```sql
-- Query by custom field value
SELECT company_name, email
FROM vendors
WHERE custom_fields->'custentity_region'->>'value' = 'West';

-- Check if field exists
SELECT company_name
FROM vendors
WHERE custom_fields ? 'custentity_new_field';

-- Get all distinct field names
SELECT DISTINCT jsonb_object_keys(custom_fields)
FROM vendors;

-- Query non-deprecated fields only
SELECT company_name
FROM vendors
WHERE custom_fields->'custentity_region'->>'deprecated' = 'false';
```

## Handling Schema Changes

### Field Added to NetSuite
**What happens:** Automatically captured in next sync
**Action required:** None
**Data impact:** New field appears in `custom_fields`

```python
# Before sync: custom_fields = {"custentity_region": {...}}
# After sync:  custom_fields = {"custentity_region": {...}, "custentity_new": {...}}
```

### Field Removed from NetSuite
**What happens:** Field marked as deprecated, value preserved
**Action required:** None (data kept for historical analysis)
**Data impact:** Field's `deprecated` flag set to `true`

```python
# Sync 1: {"custentity_old": {"value": "X", "last_seen": "2025-01-01", "deprecated": false}}
# Sync 2: {"custentity_old": {"value": "X", "last_seen": "2025-01-01", "deprecated": true}}
```

### Field Promotion (Custom → Typed)
**When:** Custom field becomes important for business logic
**Action:** Add database migration

```sql
-- Promote custom field to typed column
ALTER TABLE vendors ADD COLUMN payment_method VARCHAR(50);

UPDATE vendors
SET payment_method = custom_fields->'custentity_payment_method'->>'value';

CREATE INDEX idx_vendors_payment_method ON vendors(payment_method);
```

## Migration Guide

### Initial Setup (New Database)

```bash
# Initialize database with schema
uv run vendor-analysis init-db

# Run migration to add JSONB columns
uv run python scripts/run_migration.py

# Sync data from NetSuite
uv run vendor-analysis sync
```

### Existing Database Upgrade

```bash
# Backup database
pg_dump vendor_analysis > backup.sql

# Run migration
uv run python scripts/run_migration.py

# Re-sync to populate custom fields
uv run vendor-analysis sync
```

The migration is idempotent (safe to run multiple times).

## Benefits

### For Data
✅ **No data loss** - Historical fields preserved even if removed from NetSuite
✅ **Complete capture** - All fields stored, not just known ones
✅ **Auditable** - Full raw NetSuite response saved

### For Development
✅ **No code changes** - NetSuite field additions don't require code updates
✅ **Flexible queries** - Can query any custom field via JSONB
✅ **Future-proof** - Schema evolution tracked automatically

### For Operations
✅ **Resilient sync** - Never breaks on NetSuite schema changes
✅ **Historical analysis** - Can see what fields existed at any point in time
✅ **Field lifecycle** - Know when fields were added/removed

## Performance Considerations

### JSONB Query Performance
- **GIN indexes** created on `custom_fields` for fast queries
- **Query performance** comparable to regular columns for simple lookups
- **Contains operator** (`?`) and path extraction are optimized

### Sync Performance
- **Trade-off:** Fetching full records is slower than ID-only queries
- **9000 vendors** ≈ 9000 individual API calls (rate-limited by NetSuite)
- **Mitigation:** Incremental sync strategies, caching, parallel requests

### Storage
- **JSONB compression** - PostgreSQL compresses JSON efficiently
- **Raw data size** - Complete response adds ~5-10KB per record
- **Total impact** - For 10K vendors ≈ 50-100MB additional storage

## Best Practices

### Do
✅ Use `CustomFieldQuery` helpers for querying
✅ Check field existence before querying (`custom_fields ? 'field_name'`)
✅ Handle None/null gracefully (field may not exist for all vendors)
✅ Use `deprecated: false` filter for current fields

### Don't
❌ Assume all vendors have the same custom fields
❌ Hard-code custom field names in business logic (use config)
❌ Query raw_data directly (use custom_fields instead)
❌ Drop JSONB columns (you'll lose all historical data)

## Troubleshooting

### Field not appearing in sync
1. Check if field exists in NetSuite record
2. Verify field not in `VENDOR_KNOWN_FIELDS` (would go to typed column)
3. Check `raw_data` to see if NetSuite returned it

### Query returns no results
```python
# Check if field exists in any records
fields = CustomFieldQuery.list_all_custom_fields(session)
print(fields)  # See all available fields

# Check specific vendor's custom fields
vendor = session.query(VendorRecord).first()
print(vendor.custom_fields)
```

### Performance issues
```sql
-- Verify GIN index exists
\d vendors
-- Should show: idx_vendors_custom_fields_gin (gin)

-- Analyze query plan
EXPLAIN ANALYZE
SELECT * FROM vendors
WHERE custom_fields->'custentity_region'->>'value' = 'West';
```

## Further Reading

- PostgreSQL JSONB documentation: https://www.postgresql.org/docs/current/datatype-json.html
- GIN indexes: https://www.postgresql.org/docs/current/gin-intro.html
- NetSuite REST API: `/opt/ns/kb/suitetalk-rest-api.md`
