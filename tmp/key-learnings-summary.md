# Key Learnings Summary - Quick Reference

## Critical Discoveries (Save Hours of Debugging)

### 1. NetSuite REST API Query Returns IDs ONLY
```python
# ❌ WRONG - Only gets IDs
vendors = client.get('/vendor?limit=100')['items']
# Result: [{"id": "123"}]  ← Missing all fields!

# ✅ CORRECT - 2-step pattern
ids = client.get('/vendor?limit=100')['items']
vendors = [client.get(f'/vendor/{id}') for id in ids]
# Result: Full records with 50+ fields
```

### 2. OAuth 1.0 Signature Must Include Query Params
```python
# ❌ WRONG - 401 error
url = "https://api.com/vendor"
headers = auth(url)
response = get(url, params={"limit": 100}, headers=headers)

# ✅ CORRECT - Build full URL first
url = "https://api.com/vendor?limit=100"
headers = auth(url)  # Signature includes limit=100
response = get(url, headers=headers)
```

### 3. Use CONSUMER not CLIENT for NetSuite Credentials
```bash
# ✅ CORRECT (NetSuite vernacular)
NS_CONSUMER_KEY=...
NS_CONSUMER_SECRET=...

# ❌ WRONG (Confusing)
NS_CLIENT_ID=...
NS_CLIENT_SECRET=...
```

### 4. TBA Requires 4 Credentials, Not 2
```bash
# TBA (OAuth 1.0) - 4 credentials
NS_CONSUMER_KEY=...      # From Integration Record
NS_CONSUMER_SECRET=...   # From Integration Record
NS_TOKEN_ID=...          # From Access Token
NS_TOKEN_SECRET=...      # From Access Token

# OAuth 2.0 - 2 credentials
NS_CONSUMER_KEY=...      # From Integration Record
NS_CONSUMER_SECRET=...   # From Integration Record
```

### 5. Custom Fields Everywhere (Don't Hardcode)
```python
# NetSuite returns 50+ fields:
# - 10 standard (id, companyName, etc.)
# - 21 custom (custentity_*)
# - 19 other (addressBook, links, etc.)

# ❌ WRONG - Hardcode 10 fields, lose 40
class Vendor:
    id: str
    company_name: str
    # Missing 40 fields!

# ✅ CORRECT - Store all fields
class VendorRecord:
    id: str  # Typed column
    company_name: str  # Typed column
    custom_fields: JSONB  # Everything else
    raw_data: JSONB  # Complete response
```

### 6. Schema Resilience (Never Destroy Data)
```sql
-- ✅ SAFE - Add columns only
ALTER TABLE vendors ADD COLUMN custom_fields JSONB;

-- ❌ NEVER - Don't drop based on API changes
ALTER TABLE vendors DROP COLUMN old_field;
```

### 7. Make Integration for CLI Flags
```makefile
# Need ARGS variable for flags
vendor-analysis:
    uv run vendor-analysis $(ARGS) $(filter-out $@,$(MAKECMDGOALS))
%:
    @:

# Usage
make vendor-analysis ARGS="sync --vendors-only"
```

### 8. Pydantic Optional Fields for Inconsistent APIs
```python
# ❌ WRONG - Fails on empty string
tran_date: datetime = Field(...)

# ✅ CORRECT - Optional, handles empty/missing
tran_date: datetime | None = Field(None)
```

---

## Gap Closures by Impact

**CRITICAL (Prevents complete failures):**
1. 2-step query pattern (would only get IDs)
2. OAuth 1.0 signature bug (401 auth failures)
3. 4-credential TBA (incomplete auth setup)

**HIGH (Major data loss/confusion):**
4. Custom field awareness (lose 80% of data)
5. Credential vernacular (naming confusion)
6. Schema resilience (data destruction on changes)

**MEDIUM (Significant improvements):**
7. Diagnostics without UI (troubleshooting help)
8. Performance strategies (avoid 5-hour syncs)

**LOW (Polish):**
9. Make integration (UX improvement)
10. Pydantic edge cases (validation errors)

---

## Files to Reference During Updates

**Authentication:**
- `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/auth_tba.py`
- `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/auth.py`
- `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/auth_factory.py`

**Data Fetching:**
- `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/queries.py`
- `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/client.py`

**Custom Fields:**
- `/opt/ns/apps/vendor-analysis/src/vendor_analysis/core/field_config.py`
- `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/field_processor.py`

**Database:**
- `/opt/ns/apps/vendor-analysis/src/vendor_analysis/db/models.py`
- `/opt/ns/apps/vendor-analysis/src/vendor_analysis/db/query_helpers.py`
- `/opt/ns/apps/vendor-analysis/scripts/migrate_add_custom_fields.sql`

**Sync Logic:**
- `/opt/ns/apps/vendor-analysis/src/vendor_analysis/cli/sync.py`

**Documentation:**
- `/opt/ns/apps/vendor-analysis/SCHEMA_RESILIENCE.md`

**Config:**
- `/opt/ns/.env` (renamed credentials)
- `/opt/ns/apps/vendor-analysis/config.yaml` (auth_method)
- `/opt/ns/Makefile` (vendor-analysis target)

---

**Total Execution Time Estimate:** 3-4 hours
**High-priority only:** 2-3 hours
**Critical gaps only:** 1-2 hours
