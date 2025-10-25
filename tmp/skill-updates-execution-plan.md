# Skill Updates Execution Plan
Generated: 2025-10-24

## Overview

Based on learnings from implementing vendor-analysis with TBA authentication and schema-resilient custom fields, we need to update 6 skills with critical NetSuite patterns and architectural improvements.

**Total Tasks:** 28 file updates across 6 skills
**Estimated Time:** 3-4 hours
**Priority:** CRITICAL → LOW

---

## PHASE 1: CRITICAL - netsuite-developer (8 updates)

### Task 1.1: Add Multi-Method Authentication Pattern
**File:** `.claude/skills/netsuite-developer/patterns/authentication-methods.md` (NEW)
**Priority:** CRITICAL
**Why:** Users confused by CLIENT vs CONSUMER terminology; need multi-method support

**Content to add:**
```markdown
# Authentication Methods

## Credential Vernacular (NetSuite Standard)

**CORRECT Terminology:**
- CONSUMER_KEY / CONSUMER_SECRET (from Integration Record)
- TOKEN_ID / TOKEN_SECRET (from Access Token)

**INCORRECT (Don't use):**
- CLIENT_ID / CLIENT_SECRET (OAuth 2.0 spec, not NetSuite vernacular)

## TBA (Token-Based Authentication) - OAuth 1.0

**Status:** DEPRECATED February 2025, but still widely used

**Requires 4 credentials:**
1. Consumer Key (from Integration Record)
2. Consumer Secret (from Integration Record)
3. Token ID (from Access Token)
4. Token Secret (from Access Token)

**Sources:**
- Integration Record: Setup > Integration > Manage Integrations
- Access Token: Setup > Users/Roles > Access Tokens

**Code Example:** See implementation in /opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/auth_tba.py

## OAuth 2.0 Client Credentials

**Status:** Required 2025+

**Requires 2 credentials:**
1. Consumer Key (from Integration Record)
2. Consumer Secret (from Integration Record)

**Code Example:** See implementation in /opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/auth.py

## Multi-Method Factory Pattern

Use abstraction to support multiple auth methods:

```python
# auth_base.py
class NetSuiteAuthProvider(ABC):
    @abstractmethod
    def get_auth_headers(self, url: str, method: str) -> dict[str, str]:
        pass

# auth_factory.py
def create_auth_provider(auth_method: str) -> NetSuiteAuthProvider:
    if auth_method == "tba":
        return TBAAuthProvider(settings)
    elif auth_method == "oauth2":
        return OAuth2AuthProvider(settings)
```

**Reference:** /opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/auth_factory.py
```

**Checkpoint:**
- [ ] File created and readable
- [ ] Both TBA and OAuth 2.0 explained
- [ ] Vernacular clearly stated
- [ ] Code examples referenced

**Look-back:** Does this clearly explain the credential naming confusion we hit?

---

### Task 1.2: Document REST API 2-Step Query Pattern
**File:** `.claude/skills/netsuite-developer/patterns/rest-api-queries.md` (NEW)
**Priority:** CRITICAL
**Why:** THIS IS THE #1 GAP - Query endpoint only returns IDs, not full data

**Content to add:**
```markdown
# NetSuite REST API Query Patterns

## CRITICAL: 2-Step Data Fetching Pattern

### The Problem

NetSuite REST API has two endpoint types with different behaviors:

**Query Endpoint** (`GET /vendor?limit=100`):
- Returns: **IDs ONLY** (plus links)
- Fast, lightweight
- No way to request full fields

**Get Endpoint** (`GET /vendor/{id}`):
- Returns: **Complete record with ALL fields** (standard + custom)
- Slower (individual requests)
- Only way to get full data

### Common Mistake (WRONG)

```python
# This WON'T work - only gets IDs!
response = client.get('/vendor?limit=100')
vendors = response['items']
# vendors = [{"id": "123", "links": [...]}]  ← Missing all data!
```

### Correct Pattern

```python
# Step 1: Query for IDs (fast)
response = client.query('/vendor?limit=100')
vendor_ids = [item['id'] for item in response['items']]

# Step 2: Fetch full record for each ID (slower, complete)
vendors = []
for vendor_id in vendor_ids:
    full_data = client.get(f'/vendor/{vendor_id}')
    vendors.append(full_data)  # Now has all 50+ fields
```

### Performance Implications

**For 9000 vendors:**
- Step 1: ~90 API calls (100 per page)
- Step 2: 9000 API calls (one per vendor)
- **Total:** 9090+ API calls
- **Time:** Depends on rate limits (NetSuite governance)

**Mitigation strategies:**
- Incremental sync (only fetch changed records)
- Parallel requests (respect rate limits)
- Cache full records, only re-fetch when lastModifiedDate changes
- Consider SuiteQL for bulk queries (different endpoint)

### Query Parameters

**Supported:**
- `limit` - Max records per page (default: 1000)
- `offset` - Pagination offset
- `q` - SuiteQL query filter

**NOT Supported:**
- `expandSubResources` - Does NOT work (returns 400 error)
- `fields` - Does NOT work on query endpoint

**Reference:** /opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/queries.py
```

**Checkpoint:**
- [ ] File created
- [ ] 2-step pattern clearly explained with WRONG vs CORRECT examples
- [ ] Performance implications documented
- [ ] Query parameters listed

**Look-back:** Will this prevent the "only getting IDs" mistake we made?

---

### Task 1.3: Add OAuth 1.0 Signature Bug Pattern
**File:** `.claude/skills/netsuite-developer/patterns/oauth-signatures.md` (NEW)
**Priority:** CRITICAL
**Why:** Subtle bug that breaks TBA auth - query params must be in signature

**Content to add:**
```markdown
# OAuth 1.0 Signature Generation (TBA)

## Critical Bug Pattern

### The Problem

OAuth 1.0 signatures MUST include query parameters in the signature base string.

**WRONG (Causes 401 errors):**
```python
# Build URL
url = "https://account.api.netsuite.com/vendor"

# Generate signature using base URL
headers = auth.get_auth_headers(url)

# Add query params AFTER signature generation
response = httpx.get(url, params={"limit": 100}, headers=headers)
# ❌ FAILS - Signature doesn't include limit=100
```

**CORRECT:**
```python
# Build COMPLETE URL with query params FIRST
from urllib.parse import urlencode

base_url = "https://account.api.netsuite.com/vendor"
params = {"limit": 100, "offset": 0}
query_string = urlencode(params)
full_url = f"{base_url}?{query_string}"

# Generate signature using FULL URL (includes query params)
headers = auth.get_auth_headers(full_url, method="GET")

# Make request with full URL (params already in URL)
response = httpx.get(full_url, headers=headers)
# ✅ WORKS - Signature includes limit=100&offset=0
```

### Signature Generation Steps

1. **Parse URL** - Extract scheme, host, path, query params
2. **Combine params** - OAuth params + Query params
3. **Sort params** - Alphabetically by key
4. **Build signature base string**
5. **Generate HMAC-SHA256**
6. **Build Authorization header**

**Reference Implementation:** `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/auth_tba.py`

### Common Issues

**Issue:** 401 "Invalid login attempt" despite correct credentials
**Cause:** Query params not included in signature
**Fix:** Build full URL before generating signature

**Issue:** Signature mismatch on pagination
**Cause:** offset parameter added after signature
**Fix:** Include offset in initial URL construction
```

**Checkpoint:**
- [ ] File created
- [ ] Bug pattern clearly shown (WRONG vs CORRECT)
- [ ] Reference to working implementation
- [ ] Common issues documented

**Look-back:** Would this have saved us 2+ hours of debugging auth?

---

### Task 1.4: Add Custom Fields Deep-Dive
**File:** `.claude/skills/netsuite-developer/patterns/custom-fields.md` (NEW)
**Priority:** HIGH
**Why:** Custom fields are pervasive but not documented; need classification

**Content to add:**
```markdown
# Custom Fields in NetSuite

## Field Types

### Standard Fields
NetSuite built-in fields that exist on all records:
- `id`, `entityId`, `companyName`, `email`, `balance`
- Stable, documented, rarely change

### Standard Sub-Resources
NetSuite built-in nested resources:
- `addressBook`, `contactList`, `currencyList`
- Return link objects: `{"links": [...], "id": "..."}`
- Not custom fields, but often mistaken for them

### Custom Fields
User-defined fields added to NetSuite records:
- **Vendor/Customer**: `custentity_*` (e.g., `custentity_region`, `custentity_payment_method`)
- **Transactions**: `custbody_*` (e.g., `custbody_department`, `custbody_project`)
- **Items**: `custitem_*`
- Can be added/removed at any time by admins

## Identifying Custom Fields

**Pattern matching:**
```python
def is_custom_field(field_name: str) -> bool:
    return field_name.startswith(('custentity', 'custbody', 'custitem', 'custrecord'))
```

**Real-world example:**
NetSuite vendor record returns 50+ fields:
- 10 standard fields (id, companyName, email, etc.)
- 8 standard sub-resources (addressBook, contactList, etc.)
- 21 custom fields (custentity_*)
- 11 other fields (externalId, customForm, etc.)

## Handling Custom Fields

### Problem: Hardcoded Field Lists

**WRONG (Loses 80% of data):**
```python
class Vendor:
    id: str
    company_name: str
    email: str
    # Only 3 fields! NetSuite returns 50!
```

**CORRECT (Flexible schema):**
```python
# Use Pydantic extra="allow" or JSONB storage
class Vendor(BaseModel):
    # Known fields explicitly typed
    id: str
    company_name: str

    class Config:
        extra = "allow"  # Capture unknown fields
```

### Field Classification Strategy

See: `/opt/ns/apps/vendor-analysis/src/vendor_analysis/core/field_config.py`

```python
VENDOR_KNOWN_FIELDS = frozenset([
    "id", "entityId", "companyName", "email",
    "balance", "currency", "terms", ...
])

def split_fields(data: dict) -> tuple[dict, dict]:
    known = {k: v for k, v in data.items() if k in VENDOR_KNOWN_FIELDS}
    custom = {k: v for k, v in data.items() if k not in VENDOR_KNOWN_FIELDS}
    return known, custom
```

## Reference Field Extraction

NetSuite returns references as objects:

```python
# NetSuite returns
{"currency": {"id": "1", "refName": "USD", "links": [...]}}

# Extract for storage
def extract_reference(field):
    if isinstance(field, dict):
        return field.get("refName") or field.get("id")
    return field

# Result: "USD"
```

**Reference:** `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/field_processor.py`
```

**Checkpoint:**
- [ ] File created
- [ ] Custom field patterns documented
- [ ] Field classification explained
- [ ] Reference extraction shown

**Look-back:** Does this prevent hardcoding only 10 fields?

---

### Task 1.5: Add Diagnostics Without UI Access Pattern
**File:** `.claude/skills/netsuite-developer/testing/diagnostics-without-ui.md` (NEW)
**Priority:** HIGH
**Why:** Users may not have NetSuite access; need programmatic diagnostics

**Content to add:**
```markdown
# Diagnostics Without NetSuite UI Access

## The Problem

Users may not have interactive NetSuite access but need to:
- Verify credentials are correct
- Troubleshoot 401/403 errors
- Understand what admin needs to fix

## Solution: Diagnostic Scripts

### Test Authentication Programmatically

```python
# Test script pattern
def test_auth():
    # Show what credentials are being used (masked)
    print(f"Account: {account_id}")
    print(f"Consumer Key: {consumer_key[:20]}...")

    # Make test API call
    response = client.get('/vendor?limit=1')

    if response.status_code == 200:
        print("✓ Authentication successful!")
    else:
        print(f"✗ Auth failed: {response.status_code}")
        print_admin_checklist()
```

**Reference:** `/opt/ns/apps/vendor-analysis/scripts/diagnose_auth.py`

### Admin Checklists for Common Errors

**401 Unauthorized:**
```
Admin must verify in NetSuite UI:
1. Integration Record (Setup > Integration > Manage Integrations)
   - Find integration with Consumer Key: [masked]...
   - Confirm Status = "Enabled"
   - Confirm "Token-Based Authentication" is checked

2. Access Token (Setup > Users/Roles > Access Tokens)
   - Find token with Token ID: [masked]...
   - Confirm Status = "Active" (not Revoked)
   - Confirm Role has required permissions

3. Login Audit Trail (Setup > Users/Roles > View Login Audit Trail)
   - Filter by Integration
   - Check specific error reason
```

**403 Forbidden:**
```
Permission issue:
- Token's role lacks permissions for the operation
- Admin must check role permissions
```

### Providing Actionable Errors

**WRONG:**
```python
raise Exception("Authentication failed")
```

**CORRECT:**
```python
if response.status_code == 401:
    raise NetSuiteAuthError(
        f"401 Unauthorized. Possible causes:\n"
        f"1. Integration record is disabled\n"
        f"2. Access token is revoked\n"
        f"3. Wrong environment (Production vs Sandbox)\n"
        f"\n"
        f"Have NetSuite admin check:\n"
        f"- Setup > Integration > Manage Integrations (Consumer Key: {key[:20]}...)\n"
        f"- Setup > Users/Roles > Access Tokens (Token ID: {token[:20]}...)\n"
        f"- Setup > Users/Roles > View Login Audit Trail"
    )
```
```

**Checkpoint:**
- [ ] File created
- [ ] Diagnostic pattern documented
- [ ] Admin checklists included
- [ ] Actionable error examples shown

**Look-back:** Would this help users without NetSuite access troubleshoot?

---

### Task 1.6: Update SKILL.md with New Patterns Section
**File:** `.claude/skills/netsuite-developer/SKILL.md`
**Priority:** HIGH
**Action:** ADD section after line 80 (SuiteScript Development)

**Content to add:**
```markdown
## Core Patterns (NEW)

### Authentication
- **Multi-Method Support**: [patterns/authentication-methods.md](patterns/authentication-methods.md)
- **OAuth 1.0 Signatures**: [patterns/oauth-signatures.md](patterns/oauth-signatures.md)
- **Diagnostics Without UI**: [testing/diagnostics-without-ui.md](testing/diagnostics-without-ui.md)

### Data Access
- **REST API 2-Step Query**: [patterns/rest-api-queries.md](patterns/rest-api-queries.md) ⚠️ CRITICAL
- **Custom Fields Handling**: [patterns/custom-fields.md](patterns/custom-fields.md)
- **Reference Field Extraction**: [patterns/custom-fields.md#reference-field-extraction](patterns/custom-fields.md#reference-field-extraction)
```

**Checkpoint:**
- [ ] SKILL.md updated
- [ ] New section added
- [ ] Links to new patterns included

**Look-back:** Are the new patterns discoverable from main SKILL.md?

---

### Task 1.7: Update kb-reference.md Index
**File:** `.claude/skills/netsuite-developer/kb-reference.md`
**Priority:** MEDIUM
**Action:** ADD new patterns to index

**Content to add:**
```markdown
### New Patterns (2025-01)
- [Authentication Methods](patterns/authentication-methods.md) - TBA vs OAuth 2.0, credential vernacular
- [REST API Query Patterns](patterns/rest-api-queries.md) - **CRITICAL**: 2-step fetch for complete data
- [OAuth 1.0 Signatures](patterns/oauth-signatures.md) - Query param signature bug
- [Custom Fields](patterns/custom-fields.md) - custentity_*, field classification
- [Diagnostics Without UI](testing/diagnostics-without-ui.md) - Testing credentials programmatically
```

**Checkpoint:**
- [ ] Index updated
- [ ] New patterns listed with descriptions

**Look-back:** Can users discover the new critical patterns?

---

### Task 1.8: Add Real-World Example
**File:** `.claude/skills/netsuite-developer/examples/vendor-sync-complete.md` (NEW)
**Priority:** MEDIUM
**Why:** Concrete example of all patterns working together

**Content to add:**
```markdown
# Complete Vendor Sync Example

Real-world implementation from vendor-analysis app showing:
- Multi-method authentication
- 2-step REST API query
- Custom field handling
- Schema-resilient storage

## Source Code Reference

**Location:** `/opt/ns/apps/vendor-analysis/`

**Key files:**
- `src/vendor_analysis/netsuite/auth_tba.py` - TBA authentication
- `src/vendor_analysis/netsuite/queries.py` - 2-step fetch pattern
- `src/vendor_analysis/netsuite/field_processor.py` - Custom field processing
- `src/vendor_analysis/cli/sync.py` - Complete workflow

## Authentication Setup

[Include relevant code snippets from auth_factory.py and auth_tba.py]

## Data Fetching

[Include snippets from queries.py showing fetch_all_vendors_raw]

## Custom Field Processing

[Include snippets from field_processor.py]
```

**Checkpoint:**
- [ ] Example created
- [ ] References vendor-analysis code
- [ ] Ties all patterns together

**Look-back:** Does example show how patterns work together?

---

## PHASE 2: HIGH - netsuite-integrations (6 updates)

### Task 2.1: Update TBA Authentication Document
**File:** `.claude/skills/netsuite-integrations/authentication/tba.md`
**Priority:** HIGH
**Action:** MAJOR UPDATE - Add complete 4-credential flow

**Current issues to fix:**
- Missing explanation of all 4 credentials
- No credential source documentation
- Missing OAuth 1.0 signature details

**Content to add:**
```markdown
## Complete TBA Setup

### 4 Required Credentials

**From Integration Record** (Setup > Integration > Manage Integrations):
1. **Consumer Key** - Identifies your application
2. **Consumer Secret** - Used to sign requests

**From Access Token** (Setup > Users/Roles > Access Tokens):
3. **Token ID** - Identifies the user/role
4. **Token Secret** - Used to sign requests

### Environment Variables

```bash
# NetSuite Account
NS_ACCOUNT_ID=610574

# From Integration Record
NS_CONSUMER_KEY=bf53d76ed90272357816...
NS_CONSUMER_SECRET=bfde7978f8397e413f2ca145...

# From Access Token
NS_TOKEN_ID=e6229be96752005bc32fdb...
NS_TOKEN_SECRET=c0e4b2b5dc4c386ba0ef5271...
```

### OAuth 1.0 Signature with Query Params

**Critical:** Query parameters MUST be in signature base string.

[Include signature generation code from auth_tba.py]

### Troubleshooting

**401 Errors - Admin Checklist:**
[Include admin checklist from diagnostics]
```

**Checkpoint:**
- [ ] File updated
- [ ] 4-credential flow documented
- [ ] Signature bug pattern included
- [ ] Troubleshooting added

**Look-back:** Is the complete TBA flow now clear?

---

### Task 2.2: Update REST API Document
**File:** `.claude/skills/netsuite-integrations/suitetalk/rest-api.md`
**Priority:** CRITICAL
**Action:** ADD 2-step query pattern

**Content to add (new section):**
```markdown
## Query Patterns and Data Completeness

### 2-Step Pattern for Complete Data

NetSuite REST API requires 2 steps to get full record data:

1. **Query for IDs** (endpoint: `/vendor`)
2. **Fetch each record** (endpoint: `/vendor/{id}`)

[Include pattern from netsuite-developer/patterns/rest-api-queries.md]

### Performance Considerations

- 9000 vendors = 9000+ API calls
- Rate limiting applies (NetSuite governance)
- Consider incremental sync strategies
- Cache full records when possible

### Data Fetching Strategies

**Strategy 1: Full Sync (Simple)**
```python
# Fetch all IDs
ids = query_all_ids()
# Fetch all records
records = [get_record(id) for id in ids]
```

**Strategy 2: Incremental Sync (Efficient)**
```python
# Only fetch records changed since last sync
query = f"lastModifiedDate >= '{last_sync_time}'"
changed_ids = query_ids_with_filter(query)
records = [get_record(id) for id in changed_ids]
```

**Strategy 3: Parallel Fetch (Fast)**
```python
# Fetch multiple records concurrently (respect rate limits)
import asyncio
records = await asyncio.gather(*[get_record(id) for id in ids[:batch_size]])
```
```

**Checkpoint:**
- [ ] Section added to existing file
- [ ] 2-step pattern documented
- [ ] Performance strategies included

**Look-back:** Are integration developers warned about the performance implications?

---

### Task 2.3: Add Schema Evolution Section
**File:** `.claude/skills/netsuite-integrations/patterns/schema-evolution.md` (NEW)
**Priority:** HIGH
**Why:** Custom fields change; integrations must be resilient

**Content to add:**
```markdown
# Handling NetSuite Schema Evolution

## The Challenge

NetSuite custom fields can be:
- Added at any time (new business requirements)
- Removed at any time (deprecated processes)
- Modified (field type changes)

**Traditional integration problem:**
- Hardcoded field lists miss new fields
- Field removal breaks the integration
- Schema drift over time

## Solution: Schema-Resilient Storage

### Hybrid Schema Pattern

**Typed columns** for known, stable fields:
```sql
CREATE TABLE vendors (
    id VARCHAR PRIMARY KEY,
    company_name VARCHAR,
    email VARCHAR,
    ...
```

**JSONB columns** for custom/evolving fields:
```sql
    custom_fields JSONB,  -- All custentity_* fields
    raw_data JSONB        -- Complete API response
);
```

### Benefits

✅ **Field added** - Automatically captured in custom_fields
✅ **Field removed** - Data preserved, marked deprecated
✅ **No integration breaks** - Schema changes don't cause errors
✅ **Complete audit trail** - raw_data has everything

**Reference Implementation:** `/opt/ns/apps/vendor-analysis/` (see SCHEMA_RESILIENCE.md)
```

**Checkpoint:**
- [ ] File created
- [ ] Challenge explained
- [ ] Solution documented
- [ ] Reference to vendor-analysis

**Look-back:** Does this prepare developers for schema changes?

---

### Task 2.4: Update OAuth 2.0 Document
**File:** `.claude/skills/netsuite-integrations/authentication/oauth2.md`
**Priority:** MEDIUM
**Action:** ADD comparison with TBA, credential sources

**Content to add (new section):**
```markdown
## TBA vs OAuth 2.0 Comparison

| Aspect | TBA (OAuth 1.0) | OAuth 2.0 |
|--------|----------------|-----------|
| **Status** | Deprecated Feb 2025 | Required 2025+ |
| **Credentials** | 4 (Consumer + Token) | 2 (Consumer only) |
| **Signature** | OAuth 1.0 HMAC-SHA256 | Bearer token |
| **Token Lifetime** | No expiration | 1 hour (refresh) |
| **Complexity** | High (signature calculation) | Medium (token refresh) |

### Migration from TBA to OAuth 2.0

[Include migration guide]

### Credential Sources

Both methods use Integration Record:
- Setup > Integration > Manage Integrations
- Get Consumer Key/Secret

TBA additionally requires Access Token:
- Setup > Users/Roles > Access Tokens
- Get Token ID/Secret
```

**Checkpoint:**
- [ ] Comparison table added
- [ ] Migration guide included
- [ ] Credential sources documented

**Look-back:** Is the difference between TBA and OAuth 2.0 now clear?

---

### Task 2.5: Add Data Fetching Strategies Document
**File:** `.claude/skills/netsuite-integrations/patterns/data-fetching.md` (NEW)
**Priority:** HIGH
**Why:** Need strategies for efficient large-scale data retrieval

**Content to add:**
```markdown
# Data Fetching Strategies for NetSuite

## 2-Step Pattern (Fundamental)

[Reference pattern from netsuite-developer]

## Rate Limiting Considerations

NetSuite governance limits:
- Concurrent requests
- Requests per minute
- Total API usage

### Handling 10,000+ Records

**Naive approach (slow):**
```python
# 10,000 sequential API calls
for vendor_id in vendor_ids:
    vendor = get_record(vendor_id)  # 1-2 seconds each
# Total: 3-5 hours!
```

**Batched approach (better):**
```python
# Process in batches with progress tracking
for batch in chunks(vendor_ids, batch_size=100):
    vendors = [get_record(id) for id in batch]
    store_batch(vendors)
    time.sleep(1)  # Rate limit respect
# Total: 30-60 minutes
```

**Async approach (fastest):**
```python
# Concurrent requests (respect limits!)
import httpx

async with httpx.AsyncClient() as client:
    tasks = [fetch_record_async(id) for id in batch]
    results = await asyncio.gather(*tasks)
```

## Incremental Sync

Only fetch changed records:

```python
# Get last sync time from database
last_sync = get_last_sync_time()

# Query for records modified since last sync
query = f"lastModifiedDate >= '{last_sync}'"
changed_ids = query_records(query)

# Only fetch changed records
records = [get_record(id) for id in changed_ids]
```

**Reference:** `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/queries.py`
```

**Checkpoint:**
- [ ] File created
- [ ] Strategies documented
- [ ] Performance implications shown
- [ ] Incremental sync pattern included

**Look-back:** Will this help developers avoid slow, naive implementations?

---

### Task 2.6: Update Integration Decision Matrix
**File:** `.claude/skills/netsuite-integrations/SKILL.md`
**Priority:** MEDIUM
**Action:** UPDATE decision matrix with custom field considerations

**Content to add (after existing matrix):**
```markdown
### Authentication Method Selection

| Scenario | Method | Timeframe | Complexity |
|----------|--------|-----------|------------|
| New integration (2025+) | OAuth 2.0 | Long-term | Medium |
| Existing integration | TBA | Until Feb 2025 | High (signatures) |
| Migration needed | TBA → OAuth 2.0 | Before Feb 2025 | Medium |

### Data Completeness Strategy

| Data Volume | Strategy | Trade-off |
|-------------|----------|-----------|
| < 1000 records | 2-step full fetch | Simple, complete data |
| 1000-10000 records | 2-step with batching | Moderate complexity, good performance |
| 10000+ records | Incremental sync | Complex, best performance |
| Real-time needs | Webhooks + RESTlets | Low latency, event-driven |
```

**Checkpoint:**
- [ ] SKILL.md updated
- [ ] Decision matrices expanded
- [ ] Clear guidance on method selection

**Look-back:** Can users quickly decide which approach to use?

---

## PHASE 3: HIGH - python-cli-engineering (7 updates)

### Task 3.1: Add PostgreSQL JSONB Patterns
**File:** `.claude/skills/python-cli-engineering/patterns/postgresql-jsonb.md` (NEW)
**Priority:** HIGH
**Why:** JSONB is critical for schema flexibility; not documented

**Content to add:**
```markdown
# PostgreSQL JSONB for Schema Flexibility

## When to Use JSONB

Use JSONB when:
- Schema evolves frequently (custom fields)
- Unknown fields need to be captured
- Flexibility more important than strict validation
- Need to preserve complete API responses

## Hybrid Schema Pattern

### Typed Columns + JSONB Combination

```python
class VendorRecord(Base):
    # Typed columns (known, stable fields - fast queries)
    id = Column(String, primary_key=True)
    company_name = Column(String)
    balance = Column(Float)

    # JSONB columns (flexible, evolving fields)
    custom_fields = Column(JSONB)  # Business-specific fields
    raw_data = Column(JSONB)       # Complete source data
```

### Benefits

**Typed columns:**
- Fast queries (indexed)
- Type safety
- Clear schema
- IDE autocomplete

**JSONB columns:**
- Schema flexibility
- No migrations for new fields
- Capture everything
- Still queryable

## Querying JSONB

### Basic Queries

```python
# SQLAlchemy
vendors = session.query(VendorRecord).filter(
    VendorRecord.custom_fields['region'].astext == 'West'
).all()

# Raw SQL
SELECT * FROM vendors
WHERE custom_fields->>'region' = 'West';
```

### GIN Indexes for Performance

```sql
CREATE INDEX idx_vendors_custom_gin
ON vendors USING GIN (custom_fields);
```

GIN indexes make JSONB queries as fast as regular columns.

### Operators

```sql
-- Contains key
WHERE custom_fields ? 'field_name'

-- Get text value
WHERE custom_fields->>'field_name' = 'value'

-- Get nested value
WHERE custom_fields->'level1'->'level2'->>'value' = 'x'

-- Contains object
WHERE custom_fields @> '{"key": "value"}'::jsonb
```

## Lifecycle Tracking in JSONB

Store metadata with values:

```json
{
  "region": {
    "value": "West",
    "first_seen": "2024-01-15",
    "last_seen": "2025-01-24",
    "deprecated": false
  }
}
```

Query with helper function:
```sql
SELECT get_custom_field_value(custom_fields, 'region') as region
FROM vendors;
```

**Reference Implementation:**
- Models: `/opt/ns/apps/vendor-analysis/src/vendor_analysis/db/models.py`
- Queries: `/opt/ns/apps/vendor-analysis/src/vendor_analysis/db/query_helpers.py`
- Migration: `/opt/ns/apps/vendor-analysis/scripts/migrate_add_custom_fields.sql`
```

**Checkpoint:**
- [ ] File created
- [ ] Hybrid pattern explained
- [ ] Query examples included
- [ ] GIN indexes documented

**Look-back:** Can developers implement JSONB patterns correctly?

---

### Task 3.2: Add Schema Resilience Pattern
**File:** `.claude/skills/python-cli-engineering/patterns/schema-resilience.md` (NEW)
**Priority:** HIGH
**Why:** Core architectural pattern for evolving schemas

**Content to add:**
```markdown
# Schema Resilience for Evolving APIs

## The Problem

External API schemas change:
- New fields added
- Old fields removed
- Field types modified

**Traditional approach fails:**
```python
# Breaks when API adds/removes fields
class Record:
    field1: str
    field2: str
    # What about field3 that was just added?
```

## 3-Layer Architecture

### Layer 1: Source (API)
- Returns complete data
- Schema changes over time
- No control over changes

### Layer 2: Storage (Database)
- Typed columns for known fields
- JSONB for unknown/custom fields
- **Never destroys data**

### Layer 3: Application (Code)
- Queries only needed fields
- Handles missing fields gracefully
- No references to deprecated fields

## Implementation Patterns

### Field Classification

```python
KNOWN_FIELDS = {"id", "name", "email"}

def split_fields(api_data):
    known = {k: v for k, v in api_data.items() if k in KNOWN_FIELDS}
    custom = {k: v for k, v in api_data.items() if k not in KNOWN_FIELDS}
    return known, custom
```

### Merge Strategy (Preserve Historical Data)

```python
def merge_custom_fields(existing, new, timestamp):
    merged = {}
    all_fields = set(existing.keys()) | set(new.keys())

    for field in all_fields:
        if field in new:
            # Update with new data
            merged[field] = {
                "value": new[field],
                "last_seen": timestamp,
                "deprecated": False
            }
        else:
            # Preserve from existing (field removed from API)
            merged[field] = existing[field]
            merged[field]["deprecated"] = True

    return merged
```

### Pydantic Configuration

```python
class FlexibleModel(BaseModel):
    # Known fields explicitly typed
    id: str
    name: str

    class Config:
        extra = "allow"  # Accept unknown fields
        populate_by_name = True  # Support camelCase and snake_case
```

## Migration Strategy

**Rule: Never DROP, Only ADD**

```sql
-- ✅ SAFE
ALTER TABLE records ADD COLUMN new_field VARCHAR;

-- ❌ NEVER
ALTER TABLE records DROP COLUMN old_field;
```

**Idempotent migrations:**
```sql
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'vendors' AND column_name = 'custom_fields'
    ) THEN
        ALTER TABLE vendors ADD COLUMN custom_fields JSONB;
    END IF;
END $$;
```

**Reference:** `/opt/ns/apps/vendor-analysis/scripts/migrate_add_custom_fields.sql`
```

**Checkpoint:**
- [ ] File created
- [ ] 3-layer architecture explained
- [ ] Patterns documented
- [ ] Migration strategy shown

**Look-back:** Can developers build schema-resilient apps?

---

### Task 3.3: Add Multi-Method Authentication Pattern
**File:** `.claude/skills/python-cli-engineering/patterns/multi-method-auth.md` (NEW)
**Priority:** MEDIUM
**Why:** Common pattern for APIs with multiple auth methods

**Content to add:**
```markdown
# Multi-Method Authentication Abstraction

## When to Use

When your application needs to support multiple authentication methods:
- Legacy methods being deprecated (TBA → OAuth 2.0)
- Different environments use different methods
- User choice of auth method

## Factory Pattern

### Abstract Base Class

```python
class AuthProvider(ABC):
    @abstractmethod
    def get_auth_headers(self, url: str, method: str) -> dict[str, str]:
        pass
```

### Concrete Implementations

```python
class OAuth1Provider(AuthProvider):
    def get_auth_headers(self, url, method):
        # Generate OAuth 1.0 signature
        # Signature depends on URL and method
        return {"Authorization": f"OAuth {signature}"}

class OAuth2Provider(AuthProvider):
    def get_auth_headers(self, url, method):
        # OAuth 2.0 doesn't need URL/method for signature
        token = self.get_access_token()
        return {"Authorization": f"Bearer {token}"}
```

### Factory Selection

```python
def create_auth_provider(auth_method: str) -> AuthProvider:
    if auth_method == "oauth1":
        return OAuth1Provider(settings)
    elif auth_method == "oauth2":
        return OAuth2Provider(settings)
    else:
        raise ValueError(f"Unknown auth method: {auth_method}")
```

### Configuration

```yaml
# config.yaml
application:
  auth_method: oauth1  # or oauth2
```

```bash
# .env
# OAuth 1.0 credentials
NS_CONSUMER_KEY=...
NS_CONSUMER_SECRET=...
NS_TOKEN_ID=...
NS_TOKEN_SECRET=...

# OAuth 2.0 credentials (subset)
# NS_CONSUMER_KEY=...
# NS_CONSUMER_SECRET=...
```

**Reference:** `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/auth_factory.py`
```

**Checkpoint:**
- [ ] File created
- [ ] Factory pattern documented
- [ ] Configuration shown
- [ ] Reference included

**Look-back:** Can developers implement multi-method auth correctly?

---

### Task 3.4: Add Make Integration Pattern
**File:** `.claude/skills/python-cli-engineering/patterns/make-integration.md` (NEW)
**Priority:** LOW
**Why:** Useful for mono-repos with multiple CLI apps

**Content to add:**
```markdown
# Make Integration for CLI Tools

## Use Case

For mono-repos with multiple applications, provide easy access to CLI commands from root:

```bash
# From repo root
make vendor-analysis sync
make data-processor transform
```

Instead of:
```bash
cd apps/vendor-analysis && uv run vendor-analysis sync
```

## Pattern: ARGS Variable

### The Challenge

Make interprets `--flags` as Make options, not CLI parameters.

**WRONG:**
```makefile
vendor-analysis:
    uv run vendor-analysis $(MAKECMDGOALS)

# make vendor-analysis sync --vendors-only
# Error: make doesn't recognize --vendors-only
```

**CORRECT:**
```makefile
vendor-analysis:
    @cd apps/vendor-analysis && uv run vendor-analysis $(ARGS) $(filter-out $@,$(MAKECMDGOALS))

# Catch-all to prevent Make treating args as targets
%:
    @:
```

### Usage

**With flags:**
```bash
make vendor-analysis ARGS="sync --vendors-only"
make vendor-analysis ARGS="analyze --top 25"
```

**Without flags:**
```bash
make vendor-analysis sync
make vendor-analysis analyze
```

**Reference:** `/opt/ns/Makefile` (lines 92-103)
```

**Checkpoint:**
- [ ] File created
- [ ] Pattern explained
- [ ] Usage examples shown

**Look-back:** Can developers add Make targets for their CLIs?

---

### Task 3.5: Add Pydantic for Inconsistent APIs
**File:** `.claude/skills/python-cli-engineering/patterns/pydantic-flexible.md` (NEW)
**Priority:** MEDIUM
**Why:** Real-world APIs are inconsistent; need validation strategies

**Content to add:**
```markdown
# Pydantic for Inconsistent APIs

## The Challenge

Real-world APIs return inconsistent data:
- Sometimes null, sometimes empty string, sometimes missing
- Sometimes nested object, sometimes just string
- Field types vary (datetime as string, number as string)

## Configuration Patterns

### Allow Extra Fields

```python
class FlexibleModel(BaseModel):
    id: str
    name: str

    class Config:
        extra = "allow"  # Don't fail on unknown fields
```

### Support Multiple Field Names

```python
class APIModel(BaseModel):
    company_name: str | None = Field(None, alias="companyName")

    class Config:
        populate_by_name = True  # Accept both snake_case and camelCase
```

### Handle Empty Strings

```python
# WRONG - Fails on empty string
tran_date: datetime = Field(...)  # Pydantic expects valid date

# CORRECT - Optional, converts empty → None
tran_date: datetime | None = Field(None)

# With validator
@field_validator("tran_date", mode="before")
@classmethod
def empty_to_none(cls, v):
    return v if v else None
```

### Reference Fields

```python
# NetSuite returns: {"currency": {"id": "1", "refName": "USD"}}

class Vendor(BaseModel):
    currency: str | None = None

    @model_validator(mode="before")
    @classmethod
    def extract_references(cls, data):
        if "currency" in data and isinstance(data["currency"], dict):
            data["currency"] = data["currency"].get("refName") or data["currency"].get("id")
        return data
```

**Reference:** `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/models.py`
```

**Checkpoint:**
- [ ] File created
- [ ] Real-world patterns documented
- [ ] Empty string handling shown
- [ ] Reference extraction included

**Look-back:** Will this prevent Pydantic validation errors on real APIs?

---

### Task 3.6: Add Idempotent Migrations Pattern
**File:** `.claude/skills/python-cli-engineering/reference/database-migrations.md` (NEW OR UPDATE)
**Priority:** MEDIUM
**Why:** Migrations must be safe to run multiple times

**Content to add:**
```markdown
# Database Migrations

## Idempotent Migration Pattern

Migrations should be safe to run multiple times without errors.

### PostgreSQL IF NOT EXISTS Pattern

```sql
-- Add column (safe to re-run)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'vendors' AND column_name = 'custom_fields'
    ) THEN
        ALTER TABLE vendors ADD COLUMN custom_fields JSONB;
        COMMENT ON COLUMN vendors.custom_fields IS 'Custom fields with metadata';
    END IF;
END $$;

-- Create index (safe to re-run)
CREATE INDEX IF NOT EXISTS idx_vendors_custom_gin
ON vendors USING GIN (custom_fields);
```

### Verification Step

```sql
-- Verify migration succeeded
DO $$
BEGIN
    IF NOT EXISTS (...) THEN
        RAISE EXCEPTION 'Migration failed - column not created';
    ELSE
        RAISE NOTICE 'Migration completed successfully';
    END IF;
END $$;
```

### Python Migration Runner

```python
def run_migration(session, migration_file):
    with open(migration_file) as f:
        sql = f.read()

    try:
        session.execute(text(sql))
        session.commit()
        print("✓ Migration successful")
    except Exception as e:
        session.rollback()
        print(f"✗ Migration failed: {e}")
        raise
```

**Reference:** `/opt/ns/apps/vendor-analysis/scripts/migrate_add_custom_fields.sql`
```

**Checkpoint:**
- [ ] File created or updated
- [ ] Idempotent pattern explained
- [ ] Verification shown
- [ ] Python runner pattern included

**Look-back:** Can developers write safe migrations?

---

### Task 3.7: Update SKILL.md with New Patterns
**File:** `.claude/skills/python-cli-engineering/SKILL.md`
**Priority:** HIGH
**Action:** ADD new patterns section

**Content to add (after existing patterns section):**
```markdown
### Data Persistence

**PostgreSQL JSONB:**
- Schema-flexible storage: [patterns/postgresql-jsonb.md](patterns/postgresql-jsonb.md)
- Hybrid typed/JSONB columns
- GIN indexes for performance
- See: vendor-analysis app for real implementation

**Database Migrations:**
- Idempotent migrations: [reference/database-migrations.md](reference/database-migrations.md)
- IF NOT EXISTS patterns
- Verification steps

### API Integration

**Flexible Data Models:**
- Pydantic for inconsistent APIs: [patterns/pydantic-flexible.md](patterns/pydantic-flexible.md)
- Handle empty strings, missing fields, type variations
- Reference field extraction

**Multi-Method Authentication:**
- Factory pattern: [patterns/multi-method-auth.md](patterns/multi-method-auth.md)
- Abstract base class
- Configuration-driven selection

### Build Integration

**Make Commands:**
- CLI integration: [patterns/make-integration.md](patterns/make-integration.md)
- ARGS pattern for flags
- Mono-repo CLI access
```

**Checkpoint:**
- [ ] SKILL.md updated
- [ ] New patterns section added
- [ ] Links to all new patterns

**Look-back:** Are new patterns discoverable?

---

## PHASE 4: MEDIUM - vendor-cost-analytics (4 updates)

### Task 4.1: Update NetSuite Integration
**File:** `.claude/skills/vendor-cost-analytics/integrations/netsuite.md`
**Priority:** MEDIUM
**Action:** ADD 2-step query pattern, custom fields

**Content to add:**
```markdown
## NetSuite Data Fetching

### 2-Step Pattern for Complete Vendor Data

NetSuite REST API requires 2 steps:

[Reference pattern from netsuite-developer/patterns/rest-api-queries.md]

### Custom Vendor Fields

Vendors may have 20-40 custom fields:
- `custentity_payment_method`
- `custentity_region`
- `custentity_credit_rating`
- ... many more

**Don't hardcode field lists** - Use flexible schema:

```python
# Store all fields in JSONB
custom_fields = {k: v for k, v in vendor_data.items() if k.startswith('custentity')}
```

**Reference:** `/opt/ns/apps/vendor-analysis/` implementation
```

**Checkpoint:**
- [ ] File updated
- [ ] 2-step pattern referenced
- [ ] Custom fields warned about

**Look-back:** Will vendor analytics developers fetch complete data?

---

### Task 4.2: Add Custom Field Analysis
**File:** `.claude/skills/vendor-cost-analytics/workflows/custom-field-analysis.md` (NEW)
**Priority:** MEDIUM
**Why:** Custom fields often contain critical vendor metadata

**Content to add:**
```markdown
# Custom Field Analysis

## Discovery

List all custom fields in your vendor data:

```python
from vendor_analysis.db.query_helpers import CustomFieldQuery

fields = CustomFieldQuery.list_all_custom_fields(session)
# Result: {"custentity_region": 5000, "custentity_payment_terms": 4800, ...}
```

## Segmentation by Custom Fields

```python
# Group vendors by custom field
vendors_west = CustomFieldQuery.get_vendor_by_custom_field(
    session, "custentity_region", "West"
)

# Analyze spend by region
spend_by_region = analyze_spend_by_custom_field(session, "custentity_region")
```

## Duplicate Detection with Custom Fields

Custom fields can help identify duplicates:
- Payment method preferences
- Regional coding
- Credit status

```python
# Enhanced duplicate detection
def find_duplicates_with_custom_fields(vendors):
    # Compare company name + custom region
    ...
```

**Reference:** `/opt/ns/apps/vendor-analysis/src/vendor_analysis/db/query_helpers.py`
```

**Checkpoint:**
- [ ] File created
- [ ] Discovery pattern shown
- [ ] Analysis examples included

**Look-back:** Will this expand vendor analysis capabilities?

---

### Task 4.3: Update Data Quality Section
**File:** `.claude/skills/vendor-cost-analytics/reference/data-quality.md`
**Priority:** LOW
**Action:** ADD custom field quality checks

**Content to add (new section):**
```markdown
## Custom Field Completeness

### Checking Field Population

```python
# What % of vendors have each custom field?
fields = CustomFieldQuery.list_all_custom_fields(session)
total_vendors = session.query(VendorRecord).count()

for field_name, count in fields.items():
    percentage = (count / total_vendors) * 100
    print(f"{field_name}: {percentage:.1f}% populated")
```

### Deprecated Field Detection

```python
# Find fields that stopped appearing in syncs
deprecated = CustomFieldQuery.get_deprecated_fields(session, days_threshold=30)

for field_name, vendor_ids in deprecated.items():
    print(f"{field_name}: deprecated in {len(vendor_ids)} vendors")
```
```

**Checkpoint:**
- [ ] Section added
- [ ] Quality checks shown
- [ ] Deprecated field detection included

**Look-back:** Can users assess custom field data quality?

---

### Task 4.4: Update SKILL.md Reference Section
**File:** `.claude/skills/vendor-cost-analytics/SKILL.md`
**Priority:** LOW
**Action:** ADD custom field references

**Content to add:**
```markdown
### Custom Fields
- **Custom Field Analysis**: [workflows/custom-field-analysis.md](workflows/custom-field-analysis.md)
- **NetSuite Custom Fields**: [integrations/netsuite.md#custom-vendor-fields](integrations/netsuite.md#custom-vendor-fields)
```

**Checkpoint:**
- [ ] SKILL.md updated
- [ ] Links added

**Look-back:** Are custom field resources discoverable?

---

## PHASE 5: MEDIUM - netsuite-business-automation (2 updates)

### Task 5.1: Add Custom Field Workflows
**File:** `.claude/skills/netsuite-business-automation/workflows/custom-field-automation.md` (NEW)
**Priority:** MEDIUM
**Why:** Automations often need to read/write custom fields

**Content to add:**
```markdown
# Custom Field Automation

## Reading Custom Fields in SuiteScript

```javascript
// In User Event or Scheduled Script
var region = record.getValue({fieldId: 'custentity_region'});
var paymentMethod = record.getValue({fieldId: 'custentity_payment_method'});

// Check if field exists before reading
if (record.getField({fieldId: 'custentity_new_field'})) {
    var value = record.getValue({fieldId: 'custentity_new_field'});
}
```

## Setting Custom Fields

```javascript
record.setValue({
    fieldId: 'custentity_region',
    value: 'West'
});
```

## Handling Schema Changes

**Defensive pattern:**
```javascript
function getCustomField(record, fieldId, defaultValue) {
    try {
        var field = record.getField({fieldId: fieldId});
        if (field) {
            return record.getValue({fieldId: fieldId}) || defaultValue;
        }
    } catch (e) {
        log.error('Field not found', fieldId);
    }
    return defaultValue;
}

// Usage
var region = getCustomField(vendorRecord, 'custentity_region', 'Unknown');
```
```

**Checkpoint:**
- [ ] File created
- [ ] Read/write patterns shown
- [ ] Defensive handling included

**Look-back:** Can automation scripts handle custom fields safely?

---

### Task 5.2: Update SKILL.md
**File:** `.claude/skills/netsuite-business-automation/SKILL.md`
**Priority:** LOW
**Action:** ADD custom fields section

**Content to add:**
```markdown
### Custom Fields
- **Custom Field Workflows**: [workflows/custom-field-automation.md](workflows/custom-field-automation.md)
- **Schema Flexibility**: Handle field additions/removals gracefully
```

**Checkpoint:**
- [ ] SKILL.md updated

**Look-back:** Are custom field workflows discoverable?

---

## PHASE 6: LOW - financial-analytics (1 update)

### Task 6.1: Add JSONB for Financial Data
**File:** `.claude/skills/financial-analytics/reference/flexible-schemas.md` (NEW)
**Priority:** LOW
**Why:** Financial systems also have custom fields

**Content to add:**
```markdown
# Flexible Schemas for Financial Data

## Use JSONB for Custom Financial Fields

Financial systems often have:
- Custom GL account attributes
- Custom department/location codes
- Custom financial dimensions

**Pattern:**
```python
class FinancialRecord(Base):
    # Standard fields
    account: str
    amount: Decimal

    # Custom fields
    custom_dimensions: JSONB
```

**Reference:** [python-cli-engineering skill](../../python-cli-engineering/patterns/postgresql-jsonb.md)
```

**Checkpoint:**
- [ ] File created
- [ ] Pattern shown
- [ ] Cross-reference included

**Look-back:** Is JSONB usage clear for financial apps?

---

## EXECUTION CHECKLIST

### Pre-Execution
- [ ] Review all 28 tasks above
- [ ] Confirm file paths are correct
- [ ] Understand checkpoint criteria

### During Execution (Iterative)
For each task:
1. Execute the file creation/update
2. Run checkpoint verification
3. Answer look-back question
4. Adjust next task if needed (note in comments)

### Post-Execution
- [ ] All 28 files created/updated
- [ ] All checkpoints passed
- [ ] Test one skill to verify integration
- [ ] Update this plan with any adjustments made

---

## PRIORITY SUMMARY

**MUST DO (Critical gaps):**
- Task 1.2: REST API 2-step query (THE critical gap)
- Task 1.3: OAuth 1.0 signature bug
- Task 1.1: Authentication vernacular
- Task 2.2: Integration REST API update
- Task 3.1: JSONB patterns

**SHOULD DO (High value):**
- Tasks 1.4-1.7: netsuite-developer completion
- Tasks 2.1, 2.3: netsuite-integrations auth & schema
- Tasks 3.2-3.3: python-cli patterns

**NICE TO HAVE (Lower priority):**
- Tasks 3.4-3.7: Make, Pydantic details
- Phase 4-6: Vendor analytics, automation, financial

---

## NOTES FOR EXECUTOR

- Each task is self-contained
- Can pause between phases
- Checkpoints ensure quality
- Look-backs enable adaptation
- Reference implementations in `/opt/ns/apps/vendor-analysis/`

**Start with Phase 1 (CRITICAL)** - These close the biggest gaps.
