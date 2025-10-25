# Custom Fields in NetSuite

Patterns for handling custom fields (custentity_*, custbody_*, custitem_*) including classification, extraction, and storage strategies.

## Contents

- Field Types and Naming Conventions
- Custom Field Discovery
- Field Classification Strategies
- Reference Field Extraction
- Flexible Storage Patterns
- Related Patterns

---

## Field Types and Naming Conventions

NetSuite records contain three categories of fields:

### 1. Standard Fields

Built-in NetSuite fields present on all records of a type.

**Vendor standard fields:**
- `id` - Internal ID (unique identifier)
- `entityId` - Display name/number
- `companyName` - Company name
- `email` - Primary email
- `phone` - Primary phone
- `balance` - Current balance
- `currency` - Currency reference
- `terms` - Payment terms
- `category` - Vendor category
- `isInactive` - Active/inactive status
- `lastModifiedDate` - Last modification timestamp

**Characteristics:**
- Stable (rarely change)
- Documented in NetSuite API docs
- Same across all NetSuite accounts
- Type-safe (known types)

### 2. Standard Sub-Resources

Built-in nested resources (not custom fields, but often confused with them).

**Common sub-resources:**
- `addressBook` - List of addresses
- `contactList` - List of contacts
- `currencyList` - Supported currencies

**Response format:**
```json
{
  "addressBook": {
    "links": [...],
    "totalResults": 2
  }
}
```

**Not custom fields** - These are standard NetSuite sub-resources.

### 3. Custom Fields

User-defined fields added to NetSuite records by administrators.

**Naming patterns:**

| Record Type | Prefix | Example |
|-------------|--------|---------|
| Vendor/Customer/Employee | `custentity_` | `custentity_region` |
| Transactions (Sales Order, Invoice, etc.) | `custbody_` | `custbody_department` |
| Items (Inventory, Services, etc.) | `custitem_` | `custitem_size` |
| Custom Records | `custrecord_` | `custrecord_approval_level` |

**Characteristics:**
- Variable (can be added/removed anytime)
- Not in API documentation
- Different per NetSuite account
- Unknown types (must infer or accept any)

**Real-world example:**

A vendor record might have 50+ fields:
- 10 standard fields (id, companyName, email, etc.)
- 8 standard sub-resources (addressBook, contactList, etc.)
- 21 custom fields (custentity_region, custentity_payment_method, etc.)
- 11 other fields (externalId, customForm, etc.)

---

## Custom Field Discovery

### Approach 1: Fetch and Inspect

```python
def discover_custom_fields(client):
    """Discover custom fields by fetching sample records

    Returns:
        Set of custom field names found
    """
    # Fetch a few sample records
    response = client.get('/vendor?limit=10')
    vendor_ids = [item['id'] for item in response['items']]

    custom_fields = set()

    for vendor_id in vendor_ids:
        vendor = client.get(f'/vendor/{vendor_id}')

        # Find all custentity_* fields
        for field_name in vendor.keys():
            if field_name.startswith('custentity_'):
                custom_fields.add(field_name)

    return custom_fields
```

**Output example:**
```
{'custentity_region', 'custentity_payment_method', 'custentity_credit_rating',
 'custentity_account_manager', 'custentity_preferred_currency', ...}
```

### Approach 2: Database Analysis (After Sync)

```python
from vendor_analysis.db.query_helpers import CustomFieldQuery

def list_all_custom_fields(session):
    """List all custom fields from stored data

    Returns:
        Dict mapping field names to vendor counts
    """
    fields = CustomFieldQuery.list_all_custom_fields(session)
    # Result: {"custentity_region": 5000, "custentity_payment_method": 4800, ...}

    return fields
```

**Benefits:**
- See field population rates
- Identify commonly used vs rare fields
- Detect deprecated fields (low counts)

**Reference:** `/opt/ns/apps/vendor-analysis/src/vendor_analysis/db/query_helpers.py`

---

## Field Classification Strategies

### Define Known Fields

Create a frozen set of known standard fields for each record type.

```python
from typing import Final

VENDOR_KNOWN_FIELDS: Final[frozenset[str]] = frozenset([
    # Identity fields
    "id", "entityId", "companyName", "legalName", "externalId",

    # Contact fields
    "email", "phone", "fax", "url",

    # Financial fields
    "balance", "unbilledOrders", "currency", "terms", "creditLimit",

    # Status fields
    "isInactive", "isPerson", "isJobResourceVend",

    # Metadata fields
    "lastModifiedDate", "dateCreated",

    # Sub-resources (not custom, but not simple fields either)
    "addressBook", "contactList", "currencyList",

    # Other standard fields
    "comments", "customForm", "subsidiary", "category",
])

VENDOR_BILL_KNOWN_FIELDS: Final[frozenset[str]] = frozenset([
    "id", "transactionNumber", "tranId", "tranDate", "dueDate",
    "entity", "subsidiary", "currency", "exchangeRate",
    "total", "status", "memo", "account", "createdDate",
    "lastModifiedDate",
])
```

**Reference:** `/opt/ns/apps/vendor-analysis/src/vendor_analysis/core/field_config.py`

### Split Fields Function

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
            # Process known field (with type-specific extraction)
            if key in ("currency", "terms", "category"):
                # Extract reference value
                known[key] = extract_reference_value(value)
            else:
                known[key] = value
        else:
            # Unknown field = custom field
            custom[key] = value

    return known, custom
```

**Reference:** `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/field_processor.py`

### Pattern Matching

Alternative to explicit lists - match by pattern.

```python
def is_custom_field(field_name: str) -> bool:
    """Check if field name matches custom field pattern"""
    return field_name.startswith((
        'custentity',   # Entity fields
        'custbody',     # Transaction fields
        'custitem',     # Item fields
        'custrecord',   # Custom record fields
    ))

def classify_field(field_name: str, record_type: str) -> str:
    """Classify field as standard, custom, or sub-resource

    Returns:
        "standard" | "custom" | "subresource"
    """
    if is_custom_field(field_name):
        return "custom"
    elif field_name in KNOWN_SUBRESOURCES:
        return "subresource"
    else:
        return "standard"
```

---

## Reference Field Extraction

NetSuite returns reference fields as objects with id, refName, and links.

### Reference Object Structure

```json
{
  "currency": {
    "id": "1",
    "refName": "USD",
    "links": [...]
  },
  "terms": {
    "id": "3",
    "refName": "Net 30",
    "links": [...]
  }
}
```

### Extract Reference Value

```python
def extract_reference_value(field):
    """Extract meaningful value from NetSuite reference object

    Args:
        field: Either a simple value or a reference object

    Returns:
        Simple value (refName or id or original value)
    """
    if not isinstance(field, dict):
        return field  # Already simple value

    # Prefer refName (human-readable)
    if "refName" in field:
        return field["refName"]

    # Fallback to id (unique but less readable)
    if "id" in field:
        return field["id"]

    # No recognizable reference
    return field

# Usage
currency = extract_reference_value(vendor["currency"])
# currency = "USD" (not {"id": "1", "refName": "USD", ...})
```

**Benefits:**
- Stores readable values (USD vs "1")
- Simpler database schema
- Easier reporting and analysis

**Reference:** `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/field_processor.py`

---

## Flexible Storage Patterns

### Problem: Hardcoded Field Lists

**WRONG:**
```python
class Vendor:
    id: str
    company_name: str
    email: str
    # Only 3 fields! NetSuite returns 50!
    # Custom fields completely lost!
```

### Solution 1: Pydantic with `extra="allow"`

```python
from pydantic import BaseModel, Field

class FlexibleVendor(BaseModel):
    # Explicitly define known fields
    id: str
    company_name: str = Field(alias="companyName")
    email: str | None = None

    class Config:
        extra = "allow"  # Accept unknown fields
        populate_by_name = True  # Support both snake_case and camelCase
```

**Benefits:**
- Type-safe for known fields
- Captures all unknown fields
- No errors on schema changes

**Limitations:**
- Custom fields not type-checked
- No IDE autocomplete for custom fields

### Solution 2: Hybrid Database Schema (Recommended)

Store known fields in typed columns, custom fields in JSONB.

```python
from sqlalchemy import String, Float, JSONB
from sqlalchemy.orm import Mapped, mapped_column

class VendorRecord(Base):
    __tablename__ = "vendors"

    # Typed columns for known fields (fast queries, type-safe)
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    company_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    balance: Mapped[float] = mapped_column(Float, default=0.0)

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
```

**Storage example:**

```python
# Split fields
known, custom = process_vendor_fields(netsu ite_vendor)

# Store in database
vendor = VendorRecord(
    # Known fields in typed columns
    id=known["id"],
    company_name=known["companyName"],
    balance=known["balance"],

    # Custom fields in JSONB
    custom_fields=custom,  # {"custentity_region": "West", ...}

    # Complete data for audit
    raw_data=netsuite_vendor  # Everything
)
```

**Benefits:**
- Fast queries on typed columns
- Schema flexibility for custom fields
- Complete data preservation
- No data loss on schema changes

**Reference:** `/opt/ns/apps/vendor-analysis/src/vendor_analysis/db/models.py`

### Solution 3: Field Lifecycle Tracking

Track when fields appear and disappear.

```python
def merge_custom_fields(existing, new, sync_timestamp):
    """Merge custom fields, preserving historical data

    Args:
        existing: Existing custom_fields JSONB (or None)
        new: New custom fields from API
        sync_timestamp: Current sync time

    Returns:
        Merged custom fields with metadata
    """
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
            # Field was in existing but not in new (removed from NetSuite?)
            merged[field] = existing[field]
            merged[field]["deprecated"] = True

    return merged
```

**Stored structure:**
```json
{
  "custentity_region": {
    "value": "West",
    "first_seen": "2024-01-15T10:00:00",
    "last_seen": "2025-01-24T14:30:00",
    "deprecated": false
  },
  "custentity_old_field": {
    "value": "Some value",
    "first_seen": "2024-01-15T10:00:00",
    "last_seen": "2024-06-01T09:00:00",
    "deprecated": true
  }
}
```

**Benefits:**
- Never lose data when fields removed
- Track field lifecycle
- Identify actively used vs deprecated fields

**Reference:** `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/field_processor.py`

---

## Querying Custom Fields (JSONB)

### Basic Queries

```python
from sqlalchemy import func

# Find vendors by custom field value
vendors = session.query(VendorRecord).filter(
    VendorRecord.custom_fields['custentity_region'].astext == 'West'
).all()

# With lifecycle tracking
vendors = session.query(VendorRecord).filter(
    func.jsonb_extract_path_text(
        VendorRecord.custom_fields,
        'custentity_region',
        'value'
    ) == 'West'
).all()
```

### Raw SQL Queries

```sql
-- Find vendors by custom field
SELECT * FROM vendors
WHERE custom_fields->>'custentity_region' = 'West';

-- With lifecycle tracking
SELECT * FROM vendors
WHERE custom_fields->'custentity_region'->>'value' = 'West'
  AND custom_fields->'custentity_region'->>'deprecated' = 'false';

-- List all custom fields and counts
SELECT
  jsonb_object_keys(custom_fields) as field_name,
  COUNT(*) as vendor_count
FROM vendors
WHERE custom_fields IS NOT NULL
GROUP BY field_name
ORDER BY vendor_count DESC;
```

### Helper Functions

```python
class CustomFieldQuery:
    @staticmethod
    def get_vendor_by_custom_field(session, field_name, field_value):
        """Query vendors by custom field value"""
        return session.query(VendorRecord).filter(
            func.jsonb_extract_path_text(
                VendorRecord.custom_fields,
                field_name,
                "value"
            ) == str(field_value)
        ).all()

    @staticmethod
    def list_all_custom_fields(session) -> dict[str, int]:
        """List all custom fields with vendor counts"""
        result = session.execute(text("""
            SELECT DISTINCT jsonb_object_keys(custom_fields) as field_name,
                   COUNT(*) as vendor_count
            FROM vendors WHERE custom_fields IS NOT NULL
            GROUP BY field_name ORDER BY vendor_count DESC
        """))
        return {row.field_name: row.vendor_count for row in result}
```

**Reference:** `/opt/ns/apps/vendor-analysis/src/vendor_analysis/db/query_helpers.py`

---

## Related Patterns

### REST API Data Fetching

Custom fields only appear when using the 2-step fetch pattern.

See [rest-api-queries.md](rest-api-queries.md) for:
- Why query endpoint doesn't return custom fields
- How to fetch complete records with all custom fields

### Schema Resilience

Custom fields can be added/removed by NetSuite admins at any time.

See netsuite-integrations skill for:
- Schema evolution strategies
- Merge patterns for field changes
- Database migration patterns

For python-cli-engineering skill:
- PostgreSQL JSONB patterns
- GIN indexes for performance
- Idempotent migrations

### Integration Patterns

Custom fields often drive business logic and analysis.

See netsuite-integrations skill for:
- Mapping custom fields between systems
- Validating custom field values
- Handling missing custom fields gracefully

For vendor-cost-analytics skill:
- Segmenting vendors by custom fields
- Analyzing spend by custom dimensions
- Detecting duplicates using custom identifiers

---

## Summary

**Key Points:**

1. **Custom fields are pervasive** - 20-40 per record type is common
2. **Naming patterns** - custentity_*, custbody_*, custitem_*, custrecord_*
3. **Don't hardcode field lists** - Use flexible schemas (Pydantic `extra="allow"` or JSONB)
4. **Reference extraction** - Get refName or id from reference objects
5. **Hybrid storage** - Typed columns for known fields, JSONB for custom fields
6. **Track lifecycle** - First seen, last seen, deprecated status
7. **2-step fetch required** - Custom fields only in full record fetch

**This pattern prevents losing 80% of NetSuite data by capturing custom fields alongside standard fields.**

**Reference Implementation:**
- Field configuration: `/opt/ns/apps/vendor-analysis/src/vendor_analysis/core/field_config.py`
- Field processing: `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/field_processor.py`
- Database models: `/opt/ns/apps/vendor-analysis/src/vendor_analysis/db/models.py`
- Query helpers: `/opt/ns/apps/vendor-analysis/src/vendor_analysis/db/query_helpers.py`
