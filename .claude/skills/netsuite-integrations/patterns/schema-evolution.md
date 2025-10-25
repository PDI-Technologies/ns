# Handling NetSuite Schema Evolution

Patterns for building integrations that remain resilient when NetSuite custom fields are added, removed, or modified.

## The Challenge

NetSuite custom fields are highly dynamic:

**Can change at any time:**
- Admins add new custom fields for new business requirements
- Fields removed when processes deprecated
- Field types modified (text → dropdown, etc.)
- No API notification when schema changes

**Impact on integrations:**
- Hardcoded field lists miss new fields (data loss)
- Field removal breaks integrations (errors)
- Schema drift over time (inconsistent data)
- Manual code updates required after each NetSuite change

**Traditional integration failure:**
```python
# ❌ Breaks when NetSuite schema changes
class Vendor:
    id: str
    company_name: str
    balance: float
    # Only 3 fields - NetSuite has 50!
    # New custom fields completely lost!
```

---

## Solution: Schema-Resilient Storage

Build integrations that automatically adapt to schema changes without code modifications.

### Hybrid Schema Pattern

Combine **typed columns** for stable fields with **flexible storage** for evolving fields.

**PostgreSQL Example:**
```sql
CREATE TABLE vendors (
    -- Typed columns for known, stable fields
    id VARCHAR(50) PRIMARY KEY,
    company_name VARCHAR(500),
    email VARCHAR(255),
    balance NUMERIC,
    last_modified_date TIMESTAMP,

    -- JSONB columns for flexible/custom fields
    custom_fields JSONB,  -- All custentity_* fields
    raw_data JSONB        -- Complete NetSuite response
);

-- GIN index for fast JSONB queries
CREATE INDEX idx_vendors_custom_gin ON vendors USING GIN (custom_fields);
```

**Benefits:**
- Fast queries on typed columns (id, company_name)
- Automatic capture of new custom fields
- No data loss when fields removed
- Complete audit trail in raw_data

**SQLAlchemy Implementation:**
```python
from sqlalchemy import Column, String, Float, JSONB, DateTime
from sqlalchemy.orm import DeclarativeBase

class VendorRecord(Base):
    __tablename__ = "vendors"

    # Typed columns
    id = Column(String(50), primary_key=True)
    company_name = Column(String(500))
    balance = Column(Float)
    last_modified_date = Column(DateTime)

    # Flexible columns
    custom_fields = Column(JSONB)  # Schema-resilient
    raw_data = Column(JSONB)       # Complete backup
```

**Reference:** `/opt/ns/apps/vendor-analysis/src/vendor_analysis/db/models.py`

---

## Field Classification

Systematically distinguish stable from evolving fields.

### Define Known Fields

```python
from typing import Final

VENDOR_KNOWN_FIELDS: Final[frozenset[str]] = frozenset([
    # These rarely change
    "id", "entityId", "companyName", "email", "balance",
    "currency", "terms", "isInactive", "lastModifiedDate"
])

def is_known_field(field_name: str) -> bool:
    """Check if field is stable/known"""
    return field_name in VENDOR_KNOWN_FIELDS
```

### Split Fields Function

```python
def split_vendor_fields(netsuite_data: dict) -> tuple[dict, dict]:
    """Split NetSuite data into known vs custom fields

    Returns:
        (known_fields, custom_fields)
    """
    known = {}
    custom = {}

    for key, value in netsuite_data.items():
        if key in VENDOR_KNOWN_FIELDS:
            known[key] = value
        else:
            custom[key] = value

    return known, custom
```

**Reference:** `/opt/ns/apps/vendor-analysis/src/vendor_analysis/core/field_config.py`

---

## Field Lifecycle Tracking

Track when fields appear and disappear to preserve historical data.

### Enhanced Custom Field Storage

Instead of storing just values, store metadata:

```json
{
  "custentity_region": {
    "value": "West",
    "first_seen": "2024-01-15T10:00:00Z",
    "last_seen": "2025-01-24T14:30:00Z",
    "deprecated": false
  },
  "custentity_old_field": {
    "value": "Legacy value",
    "first_seen": "2023-01-01T00:00:00Z",
    "last_seen": "2024-06-01T12:00:00Z",
    "deprecated": true  // Field removed from NetSuite
  }
}
```

### Merge Strategy

```python
from datetime import datetime

def merge_custom_fields(existing, new, sync_timestamp):
    """Merge custom fields preserving historical data

    Args:
        existing: Current custom_fields JSONB (or None)
        new: New custom fields from NetSuite API
        sync_timestamp: Current sync time

    Returns:
        Merged custom fields with lifecycle metadata
    """
    if existing is None:
        existing = {}

    merged = {}
    all_fields = set(existing.keys()) | set(new.keys())

    for field in all_fields:
        if field in new:
            # Field present in new data
            merged[field] = {
                "value": new[field],
                "last_seen": sync_timestamp.isoformat(),
                "deprecated": False,
                "first_seen": (
                    existing.get(field, {}).get("first_seen") or
                    sync_timestamp.isoformat()
                )
            }
        else:
            # Field was in existing but not in new (removed from NetSuite)
            merged[field] = existing[field]
            merged[field]["deprecated"] = True

    return merged
```

**Benefits:**
- Never lose data when fields removed from NetSuite
- Track field lifecycle automatically
- Identify actively used vs deprecated fields
- Historical analysis possible

**Reference:** `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/field_processor.py`

---

## Querying Flexible Schema

### Basic JSONB Queries

```sql
-- Find vendors by custom field value
SELECT * FROM vendors
WHERE custom_fields->>'custentity_region' = 'West';

-- With lifecycle tracking
SELECT * FROM vendors
WHERE custom_fields->'custentity_region'->>'value' = 'West'
  AND custom_fields->'custentity_region'->>'deprecated' = 'false';
```

### SQLAlchemy Queries

```python
from sqlalchemy import func

# Query by custom field
vendors = session.query(VendorRecord).filter(
    func.jsonb_extract_path_text(
        VendorRecord.custom_fields,
        'custentity_region',
        'value'
    ) == 'West'
).all()
```

### Helper Functions

```python
class CustomFieldQuery:
    @staticmethod
    def get_by_custom_field(session, field_name, field_value):
        """Query records by custom field value"""
        return session.query(VendorRecord).filter(
            func.jsonb_extract_path_text(
                VendorRecord.custom_fields,
                field_name,
                "value"
            ) == str(field_value)
        ).all()

    @staticmethod
    def list_all_custom_fields(session) -> dict[str, int]:
        """List all custom fields with record counts"""
        from sqlalchemy import text

        result = session.execute(text("""
            SELECT DISTINCT jsonb_object_keys(custom_fields) as field_name,
                   COUNT(*) as count
            FROM vendors
            WHERE custom_fields IS NOT NULL
            GROUP BY field_name
            ORDER BY count DESC
        """))

        return {row.field_name: row.count for row in result}
```

**Reference:** `/opt/ns/apps/vendor-analysis/src/vendor_analysis/db/query_helpers.py`

---

## Pydantic for Flexible Validation

Use Pydantic with `extra="allow"` to accept unknown fields.

```python
from pydantic import BaseModel, Field

class FlexibleVendor(BaseModel):
    # Explicitly define known fields
    id: str
    company_name: str = Field(alias="companyName")
    balance: float = 0.0

    class Config:
        extra = "allow"  # Accept unknown fields
        populate_by_name = True  # Support camelCase and snake_case

# Usage
vendor_data = {
    "id": "123",
    "companyName": "Acme Corp",
    "balance": 15000.00,
    "custentity_new_field": "New value",  # Automatically captured
    "custentity_another": "Another value"
}

vendor = FlexibleVendor(**vendor_data)
# vendor.id = "123"
# vendor.company_name = "Acme Corp"
# vendor.__dict__ contains all fields including custom
```

**Benefits:**
- Type-safe for known fields
- Captures all unknown fields
- No errors on schema changes

**Reference:** `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/models.py`

---

## Migration Strategy

### Rule: Never DROP, Only ADD

```sql
-- ✅ SAFE - Adding columns
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS new_field VARCHAR;

-- ❌ NEVER - Dropping based on API changes
ALTER TABLE vendors DROP COLUMN old_field;
```

### Idempotent Migrations

```sql
-- Safe to run multiple times
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'vendors' AND column_name = 'custom_fields'
    ) THEN
        ALTER TABLE vendors ADD COLUMN custom_fields JSONB;
        COMMENT ON COLUMN vendors.custom_fields IS 'Custom NetSuite fields with metadata';
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_vendors_custom_gin
ON vendors USING GIN (custom_fields);
```

**Reference:** `/opt/ns/apps/vendor-analysis/scripts/migrate_add_custom_fields.sql`

---

## Sync Implementation

### Processing NetSuite Data

```python
from datetime import datetime

def sync_vendor(session, netsuite_data):
    """Sync vendor with schema-resilient storage"""
    sync_timestamp = datetime.now()

    # Split known vs custom fields
    known, custom = split_vendor_fields(netsuite_data)

    # Check if exists
    existing = session.query(VendorRecord).filter_by(id=known["id"]).first()

    if existing:
        # Update existing
        for key, value in known.items():
            setattr(existing, key, value)

        # Merge custom fields (preserves historical data)
        existing.custom_fields = merge_custom_fields(
            existing.custom_fields,
            custom,
            sync_timestamp
        )
        existing.raw_data = netsuite_data
        existing.synced_at = sync_timestamp
    else:
        # Create new
        enhanced_custom = merge_custom_fields(None, custom, sync_timestamp)

        new_vendor = VendorRecord(
            **known,
            custom_fields=enhanced_custom,
            raw_data=netsuite_data,
            synced_at=sync_timestamp
        )
        session.add(new_vendor)

    session.commit()
```

**Reference:** `/opt/ns/apps/vendor-analysis/src/vendor_analysis/cli/sync.py`

---

## Benefits Summary

**Schema-resilient integrations:**

✅ **Automatic adaptation** - New custom fields captured without code changes

✅ **No data loss** - Field removal doesn't destroy data

✅ **Historical preservation** - Track field lifecycle (first_seen, last_seen, deprecated)

✅ **Complete audit trail** - raw_data preserves original NetSuite response

✅ **Fast queries** - Typed columns for known fields, GIN indexes for JSONB

✅ **Type safety** - Known fields type-checked, custom fields flexible

✅ **No breaking changes** - NetSuite schema changes don't break integration

---

## Related Patterns

**NetSuite Developer Skill:**
- `patterns/custom-fields.md` - Field classification and discovery
- `patterns/rest-api-queries.md` - 2-step pattern to fetch complete data

**Python CLI Engineering Skill:**
- `patterns/postgresql-jsonb.md` - JSONB query patterns and indexing
- `patterns/schema-resilience.md` - General schema resilience architecture
- `reference/database-migrations.md` - Idempotent migration patterns

**This Skill:**
- [suitetalk/rest-api.md](../suitetalk/rest-api.md) - REST API data fetching
- [patterns/data-fetching.md](data-fetching.md) - Performance strategies

**Reference Implementation:**
- `/opt/ns/apps/vendor-analysis/` - Complete schema-resilient implementation
- `/opt/ns/apps/vendor-analysis/SCHEMA_RESILIENCE.md` - Detailed documentation

---

## Summary

**Key Points:**

1. **Custom fields change frequently** - Integrations must adapt automatically
2. **Hybrid schema recommended** - Typed columns + JSONB for flexibility
3. **Track field lifecycle** - first_seen, last_seen, deprecated
4. **Never destroy data** - Preserve historical fields when removed from NetSuite
5. **Use raw_data backup** - Complete API response for audit trail
6. **Pydantic extra="allow"** - Accept unknown fields without errors
7. **Idempotent migrations** - Safe to run multiple times

**This pattern prevents integration breaking when NetSuite admins add or remove custom fields, a common cause of production failures.**
