# Token-Based Authentication (TBA)

Complete guide to NetSuite Token-Based Authentication (OAuth 1.0) for integrations, including the critical 4-credential setup and signature generation patterns.

## Status and Timeline

**DEPRECATED:** NetSuite is deprecating TBA in **February 2025**

**Current state:**
- Still widely used in existing integrations
- Supported through February 2025
- Must migrate to OAuth 2.0 before deadline

**Migration path:** See [oauth2.md](oauth2.md) for OAuth 2.0 setup and migration guide

---

## Complete TBA Setup

TBA requires **4 credentials from 2 different NetSuite locations**. Missing any credential will cause authentication to fail.

### Required Credentials

**From Integration Record** (Setup > Integration > Manage Integrations):
1. **Consumer Key** - Public identifier for your application
2. **Consumer Secret** - Secret used to sign requests

**From Access Token** (Setup > Users/Roles > Access Tokens):
3. **Token ID** - Identifies specific user/role
4. **Token Secret** - Secret used to sign requests

### NetSuite UI Steps

**Step 1: Create Integration Record**

1. Navigate to Setup > Integration > Manage Integrations > New
2. Fill in integration details:
   - Name: Your integration name
   - State: Enabled
   - Authentication: Check "Token-Based Authentication"
3. Save and copy:
   - **Consumer Key** (long hex string)
   - **Consumer Secret** (long hex string, shown only once!)
4. Important: Status must be "Enabled"

**Step 2: Create Access Token**

1. Navigate to Setup > Users/Roles > Access Tokens > New
2. Select:
   - Application Name: Your integration (from Step 1)
   - User: User to impersonate
   - Role: Role with required permissions
3. Save and copy:
   - **Token ID** (long hex string)
   - **Token Secret** (long hex string, shown only once!)
4. Important: Status must be "Active" (not Revoked)

### Environment Variables

Store credentials securely in environment variables:

```bash
# NetSuite Account
NS_ACCOUNT_ID=610574

# From Integration Record (Setup > Integration > Manage Integrations)
NS_CONSUMER_KEY=bf53d76ed90272357816199b65ab9dab388efa5dee228fefb6f4b9cd1fd706a7
NS_CONSUMER_SECRET=bfde7978f8397e413f2ca145869cd31ef27826204931b1f97b446096795cc444

# From Access Token (Setup > Users/Roles > Access Tokens)
NS_TOKEN_ID=e6229be96752005bc32fdb193184b2a6509a401b50c22da657d490a6d4ac212e
NS_TOKEN_SECRET=c0e4b2b5dc4c386ba0ef5271deab0bf82d5522e0bceaeefc0578adb8739638b9
```

**Credential naming:** Use "CONSUMER" not "CLIENT" - matches NetSuite terminology. See netsuite-developer skill for credential vernacular details.

---

## OAuth 1.0 Signature Generation

TBA uses OAuth 1.0 with HMAC-SHA256 signatures. This is the most complex part of TBA and source of most authentication bugs.

### Critical Bug Pattern

**Query parameters MUST be included in signature base string.**

This is the #1 cause of TBA authentication failures (401 errors).

**WRONG (causes 401):**
```python
# Build URL without query params
url = "https://610574.suitetalk.api.netsuite.com/services/rest/record/v1/vendor"

# Generate signature
headers = auth.get_auth_headers(url)

# Add query params AFTER signature
response = httpx.get(url, params={"limit": 100}, headers=headers)
# ❌ FAILS - Signature doesn't include limit=100
```

**CORRECT:**
```python
# Build COMPLETE URL with query params FIRST
url = "https://610574.suitetalk.api.netsuite.com/services/rest/record/v1/vendor?limit=100"

# Generate signature using FULL URL
headers = auth.get_auth_headers(url)

# Make request with full URL
response = httpx.get(url, headers=headers)
# ✅ WORKS - Signature includes limit=100
```

### Signature Generation Steps

**1. Build OAuth Parameters:**
```python
oauth_params = {
    "oauth_consumer_key": consumer_key,        # From Integration Record
    "oauth_token": token_id,                   # From Access Token
    "oauth_signature_method": "HMAC-SHA256",   # Always this value
    "oauth_timestamp": str(int(time.time())),  # Current Unix timestamp
    "oauth_nonce": secrets.token_hex(16),      # Random unique string
    "oauth_version": "1.0",                    # Always "1.0"
}
```

**2. Parse URL and Extract Query Params:**
```python
from urllib.parse import urlparse, parse_qsl

parsed_url = urlparse(url)
base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"

# Extract query params from URL
query_params = {}
if parsed_url.query:
    query_params = dict(parse_qsl(parsed_url.query))
```

**3. Combine OAuth Params with Query Params (CRITICAL):**
```python
# This is where the bug happens if you forget query params!
all_params = dict(oauth_params)
all_params.update(query_params)  # Include query params!
```

**4. Sort and Build Parameter String:**
```python
from urllib.parse import quote

# Sort alphabetically
params = sorted(all_params.items())

# URL-encode and join
param_string = "&".join(
    f"{quote(str(k), safe='')}={quote(str(v), safe='')}"
    for k, v in params
)
```

**5. Build Signature Base String:**
```python
signature_base_string = (
    f"{method.upper()}&"
    f"{quote(base_url, safe='')}&"
    f"{quote(param_string, safe='')}"
)
```

**6. Generate HMAC-SHA256 Signature:**
```python
import hmac, hashlib, base64

# Signing key = consumer_secret + "&" + token_secret
signing_key = f"{consumer_secret}&{token_secret}"

# Calculate signature
signature_bytes = hmac.new(
    key=signing_key.encode("utf-8"),
    msg=signature_base_string.encode("utf-8"),
    digestmod=hashlib.sha256
).digest()

signature = base64.b64encode(signature_bytes).decode("utf-8")
```

**7. Build Authorization Header:**
```python
oauth_params["oauth_signature"] = signature

auth_header = "OAuth " + ", ".join(
    f'{quote(k, safe="")}="{quote(v, safe="")}"'
    for k, v in sorted(oauth_params.items())
)
# Result: 'OAuth oauth_consumer_key="...", oauth_nonce="...", ...'
```

For complete implementation, see netsuite-developer skill: `patterns/oauth-signatures.md`

---

## Python Implementation Example

```python
import hmac
import hashlib
import base64
import time
import secrets
from urllib.parse import urlparse, parse_qsl, quote, urlencode
import httpx

class TBAAuth:
    """TBA (OAuth 1.0) authentication for NetSuite"""

    def __init__(self, account_id, consumer_key, consumer_secret, token_id, token_secret):
        self.account_id = account_id
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.token_id = token_id
        self.token_secret = token_secret
        self.base_url = f"https://{account_id}.suitetalk.api.netsuite.com"

    def make_request(self, method, endpoint, params=None):
        """Make authenticated request to NetSuite

        IMPORTANT: Build full URL with params before generating signature
        """
        # Build full URL
        url = f"{self.base_url}/{endpoint}"
        if params:
            query_string = urlencode(params)
            url = f"{url}?{query_string}"

        # Generate auth headers using FULL URL
        headers = self._get_auth_headers(url, method)
        headers["Accept"] = "application/json"

        # Make request
        response = httpx.request(method=method, url=url, headers=headers)
        response.raise_for_status()
        return response.json()

    def _get_auth_headers(self, url, method):
        """Generate OAuth 1.0 Authorization header"""
        oauth_params = {
            "oauth_consumer_key": self.consumer_key,
            "oauth_token": self.token_id,
            "oauth_signature_method": "HMAC-SHA256",
            "oauth_timestamp": str(int(time.time())),
            "oauth_nonce": secrets.token_hex(16),
            "oauth_version": "1.0",
        }

        signature = self._generate_signature(url, method, oauth_params)
        oauth_params["oauth_signature"] = signature

        auth_header = "OAuth " + ", ".join(
            f'{quote(str(k), safe="")}="{quote(str(v), safe="")}"'
            for k, v in sorted(oauth_params.items())
        )

        return {"Authorization": auth_header}

    def _generate_signature(self, url, method, oauth_params):
        """Generate OAuth 1.0 signature"""
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"

        # Combine OAuth params with query params
        all_params = dict(oauth_params)
        if parsed_url.query:
            query_params = parse_qsl(parsed_url.query)
            all_params.update({k: str(v) for k, v in query_params})

        # Build parameter string
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

        # Generate HMAC-SHA256 signature
        signing_key = f"{self.consumer_secret}&{self.token_secret}"
        signature_bytes = hmac.new(
            key=signing_key.encode("utf-8"),
            msg=signature_base_string.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()

        return base64.b64encode(signature_bytes).decode("utf-8")

# Usage
auth = TBAAuth(
    account_id="610574",
    consumer_key=os.getenv("NS_CONSUMER_KEY"),
    consumer_secret=os.getenv("NS_CONSUMER_SECRET"),
    token_id=os.getenv("NS_TOKEN_ID"),
    token_secret=os.getenv("NS_TOKEN_SECRET")
)

# Fetch vendors
vendors = auth.make_request("GET", "services/rest/record/v1/vendor", {"limit": 10})
```

For production implementation with retry logic, error handling, and multi-method support, see: `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/`

---

## Troubleshooting

### 401 Unauthorized

**Possible causes:**

1. **Query params not in signature** (most common)
   - Fix: Build full URL with params before calling signature generation
   - See "Critical Bug Pattern" above

2. **Integration Record disabled**
   - Check: Setup > Integration > Manage Integrations
   - Verify: Status = "Enabled"

3. **Access Token revoked**
   - Check: Setup > Users/Roles > Access Tokens
   - Verify: Status = "Active" (not Revoked)

4. **Wrong credentials**
   - Verify all 4 credentials match NetSuite UI
   - Check for extra whitespace or truncation

5. **Wrong environment**
   - Production account ID with Sandbox credentials (or vice versa)
   - Verify account ID matches environment

**Diagnostic approach:**

If you don't have NetSuite UI access, use diagnostic script pattern:

See netsuite-developer skill: `testing/diagnostics-without-ui.md`

### 403 Forbidden

**Cause:** Insufficient permissions

**Fix:**
1. Check role associated with Access Token
2. Verify role has:
   - "Web Services" permission
   - Access to required records (e.g., Vendors > View)
   - Required operation permissions (View, Create, Edit, Delete)

### Signature Mismatch on Pagination

**Symptom:** First request works (offset=0), subsequent fail (offset=100, 200, etc.)

**Cause:** Offset parameter added after signature generation

**Fix:** Generate new signature for each request with different parameters

```python
# ❌ WRONG
headers = auth.get_auth_headers(base_url)
for offset in [0, 100, 200]:
    response = httpx.get(base_url, params={"offset": offset}, headers=headers)
    # Only first request works!

# ✅ CORRECT
for offset in [0, 100, 200]:
    url = f"{base_url}?offset={offset}"
    headers = auth.get_auth_headers(url)  # New signature per request
    response = httpx.get(url, headers=headers)
```

---

## Best Practices

1. **Store secrets securely**
   - Use environment variables or secure vault
   - Never commit secrets to version control
   - Consumer Secret and Token Secret shown only once in NetSuite

2. **Build full URL before signature**
   - Include all query parameters in URL
   - Pass complete URL to signature generation
   - This prevents the query param bug

3. **Generate fresh signature per request**
   - Don't reuse headers across requests
   - Each request needs unique nonce and timestamp
   - Different query params = different signature

4. **Use cryptographically secure random for nonce**
   - Use `secrets.token_hex()` not `random`
   - Prevents nonce collision

5. **Handle 401 errors gracefully**
   - Log the request details (URL, method, timestamp)
   - Provide actionable error messages
   - Include admin checklist for troubleshooting

6. **Plan migration to OAuth 2.0**
   - TBA deprecated February 2025
   - Test OAuth 2.0 in sandbox
   - Support both methods during transition (factory pattern)

---

## Migration to OAuth 2.0

See [oauth2.md](oauth2.md) for:
- OAuth 2.0 setup (only 2 credentials needed)
- TBA vs OAuth 2.0 comparison
- Migration timeline and strategy
- Multi-method authentication pattern

---

## Related Documentation

**NetSuite Developer Skill:**
- `patterns/authentication-methods.md` - Multi-method auth, credential vernacular
- `patterns/oauth-signatures.md` - Detailed signature generation
- `testing/diagnostics-without-ui.md` - Testing without NetSuite access

**Local KB:**
- `/opt/ns/kb/authentication.md` - NetSuite authentication overview

**Example Implementation:**
- `/opt/ns/apps/vendor-analysis/` - Production TBA implementation with multi-method support

**NetSuite Documentation:**
- Token-Based Authentication setup guide
- OAuth 1.0 specification
- Integration Record configuration
- Access Token management
