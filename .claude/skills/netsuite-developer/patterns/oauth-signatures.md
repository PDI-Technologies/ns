# OAuth 1.0 Signature Generation (TBA)

Critical patterns for generating correct OAuth 1.0 signatures for NetSuite TBA (Token-Based Authentication), including the query parameter bug that causes 401 errors.

## Contents

- The Critical Bug Pattern
- OAuth 1.0 Signature Components
- Signature Generation Steps
- Common Issues and Solutions
- Working Implementation
- Verification and Testing

---

## The Critical Bug Pattern

OAuth 1.0 signatures **MUST include query parameters** in the signature base string. This is the most common TBA authentication bug.

### ❌ WRONG: Query Params Added After Signature

```python
# Build base URL (without query params)
url = "https://610574.suitetalk.api.netsuite.com/services/rest/record/v1/vendor"

# Generate signature using base URL
headers = auth.get_auth_headers(url, method="GET")

# Add query params AFTER signature generation
params = {"limit": 100, "offset": 0}
response = httpx.get(url, params=params, headers=headers)

# ❌ FAILS with 401 "Invalid login attempt"
# Signature was generated for: /vendor
# But request was sent to: /vendor?limit=100&offset=0
# Signatures don't match!
```

**Why this fails:**
- Signature generated for URL without query params
- Actual request includes query params
- NetSuite recalculates signature with params
- Signatures don't match → 401 error

**Symptom:** 401 "Invalid login attempt" despite correct credentials

### ✅ CORRECT: Full URL with Query Params Before Signature

```python
from urllib.parse import urlencode

# Build COMPLETE URL with query params FIRST
base_url = "https://610574.suitetalk.api.netsuite.com/services/rest/record/v1/vendor"
params = {"limit": 100, "offset": 0}
query_string = urlencode(params)
full_url = f"{base_url}?{query_string}"
# full_url = ".../vendor?limit=100&offset=0"

# Generate signature using FULL URL (includes query params)
headers = auth.get_auth_headers(full_url, method="GET")

# Make request with full URL (params already in URL)
response = httpx.get(full_url, headers=headers)

# ✅ WORKS - Signature includes limit=100&offset=0
```

**Why this works:**
- Signature generated for complete URL including params
- Request sent to exact same URL
- NetSuite recalculates signature with same params
- Signatures match → 200 OK

---

## OAuth 1.0 Signature Components

OAuth 1.0 signatures consist of multiple components that must be combined correctly.

### Required OAuth Parameters

```python
oauth_params = {
    "oauth_consumer_key": "bf53d76ed90272357816...",      # From Integration Record
    "oauth_token": "e6229be96752005bc32fdb...",           # From Access Token
    "oauth_signature_method": "HMAC-SHA256",              # Always HMAC-SHA256 for NetSuite
    "oauth_timestamp": "1706112000",                      # Unix timestamp (seconds)
    "oauth_nonce": "random_unique_string",                # Random nonce
    "oauth_version": "1.0",                               # Always "1.0"
}
```

### Parameter Sources

| Parameter | Source | Description |
|-----------|--------|-------------|
| `oauth_consumer_key` | Integration Record | Consumer Key (public identifier) |
| `oauth_token` | Access Token | Token ID (user/role identifier) |
| `oauth_signature_method` | Fixed | Always "HMAC-SHA256" for NetSuite |
| `oauth_timestamp` | Generated | Current Unix timestamp in seconds |
| `oauth_nonce` | Generated | Random unique string (prevent replay) |
| `oauth_version` | Fixed | Always "1.0" |
| `oauth_signature` | Calculated | HMAC-SHA256 signature (added last) |

### Signing Secrets

OAuth 1.0 uses **two secrets** to generate the signing key:

```python
# Signing key = consumer_secret + "&" + token_secret
consumer_secret = "bfde7978f8397e413f2ca145..."  # From Integration Record
token_secret = "c0e4b2b5dc4c386ba0ef5271..."     # From Access Token

signing_key = f"{consumer_secret}&{token_secret}"
```

**Important:** Both secrets are used, joined with `&` character.

---

## Signature Generation Steps

Complete step-by-step process for generating OAuth 1.0 signatures.

### Step 1: Parse URL into Components

```python
from urllib.parse import urlparse, parse_qsl

url = "https://610574.suitetalk.api.netsuite.com/services/rest/record/v1/vendor?limit=100&offset=0"

parsed_url = urlparse(url)
# scheme: "https"
# netloc: "610574.suitetalk.api.netsuite.com"
# path: "/services/rest/record/v1/vendor"
# query: "limit=100&offset=0"

# Build base URL (without query params)
base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
# base_url = "https://610574.suitetalk.api.netsuite.com/services/rest/record/v1/vendor"
```

### Step 2: Extract Query Parameters

```python
# Parse query string into key-value pairs
query_params = {}
if parsed_url.query:
    query_params = dict(parse_qsl(parsed_url.query))
# query_params = {"limit": "100", "offset": "0"}
```

### Step 3: Combine OAuth Params with Query Params

**CRITICAL:** This is where the bug happens if you forget query params.

```python
# Start with OAuth parameters
all_params = {
    "oauth_consumer_key": consumer_key,
    "oauth_token": token_id,
    "oauth_signature_method": "HMAC-SHA256",
    "oauth_timestamp": str(int(time.time())),
    "oauth_nonce": generate_nonce(),
    "oauth_version": "1.0",
}

# Add query parameters to signature calculation
all_params.update(query_params)
# all_params now contains:
# {
#   "oauth_consumer_key": "...",
#   "oauth_token": "...",
#   "oauth_signature_method": "HMAC-SHA256",
#   "oauth_timestamp": "1706112000",
#   "oauth_nonce": "...",
#   "oauth_version": "1.0",
#   "limit": "100",        # ← From query string
#   "offset": "0"          # ← From query string
# }
```

**This is the critical step.** If you omit query params here, signature will be wrong.

### Step 4: Sort Parameters Alphabetically

```python
from urllib.parse import quote

# Sort all parameters alphabetically by key
sorted_params = sorted(all_params.items())
# [
#   ("limit", "100"),
#   ("oauth_consumer_key", "..."),
#   ("oauth_nonce", "..."),
#   ("oauth_signature_method", "HMAC-SHA256"),
#   ("oauth_timestamp", "1706112000"),
#   ("oauth_token", "..."),
#   ("oauth_version", "1.0"),
#   ("offset", "0")
# ]
```

### Step 5: Build Parameter String

```python
# URL-encode each key and value, join with &
param_string = "&".join(
    f"{quote(str(k), safe='')}={quote(str(v), safe='')}"
    for k, v in sorted_params
)
# param_string = "limit=100&oauth_consumer_key=...&oauth_nonce=...&oauth_signature_method=HMAC-SHA256&oauth_timestamp=1706112000&oauth_token=...&oauth_version=1.0&offset=0"
```

**Encoding rules:**
- Both keys and values must be URL-encoded
- Use `quote(str, safe='')` to encode all special characters
- No exceptions for alphanumeric characters

### Step 6: Build Signature Base String

```python
# Signature base string format:
# HTTP_METHOD + "&" + URL_ENCODED(BASE_URL) + "&" + URL_ENCODED(PARAM_STRING)

method = "GET"
encoded_base_url = quote(base_url, safe='')
encoded_param_string = quote(param_string, safe='')

signature_base_string = f"{method}&{encoded_base_url}&{encoded_param_string}"
# signature_base_string = "GET&https%3A%2F%2F610574.suitetalk.api.netsuite.com%2Fservices%2Frest%2Frecord%2Fv1%2Fvendor&limit%3D100%26oauth_consumer_key%3D...%26oauth_nonce%3D...%26oauth_signature_method%3DHMAC-SHA256%26oauth_timestamp%3D1706112000%26oauth_token%3D...%26oauth_version%3D1.0%26offset%3D0"
```

**Format:**
- HTTP method (uppercase)
- `&`
- URL-encoded base URL
- `&`
- URL-encoded parameter string

### Step 7: Generate Signing Key

```python
# Signing key = consumer_secret + "&" + token_secret
signing_key = f"{consumer_secret}&{token_secret}"
# signing_key = "bfde7978f8397e413f2ca145...&c0e4b2b5dc4c386ba0ef5271..."
```

### Step 8: Calculate HMAC-SHA256 Signature

```python
import hmac
import hashlib
import base64

# Generate HMAC-SHA256 hash
signature_bytes = hmac.new(
    key=signing_key.encode('utf-8'),
    msg=signature_base_string.encode('utf-8'),
    digestmod=hashlib.sha256
).digest()

# Base64 encode the hash
signature = base64.b64encode(signature_bytes).decode('utf-8')
# signature = "AbCd1234EfGh5678IjKl9012MnOp3456..."
```

### Step 9: Build Authorization Header

```python
# Add signature to OAuth parameters (NOT to query params!)
oauth_params["oauth_signature"] = signature

# Build Authorization header
auth_header_parts = [
    f'{quote(str(k), safe="")}="{quote(str(v), safe="")}"'
    for k, v in sorted(oauth_params.items())
]

auth_header = "OAuth " + ", ".join(auth_header_parts)
# auth_header = 'OAuth oauth_consumer_key="...", oauth_nonce="...", oauth_signature="...", oauth_signature_method="HMAC-SHA256", oauth_timestamp="1706112000", oauth_token="...", oauth_version="1.0"'
```

**Header format:**
- Prefix: `OAuth `
- Key-value pairs separated by `, `
- Values quoted with `"`
- Only OAuth parameters (not query params!)

---

## Working Implementation

Complete working example from vendor-analysis application.

### TBAAuthProvider Class

```python
import hmac
import hashlib
import base64
import time
import secrets
from urllib.parse import urlparse, parse_qsl, quote

class TBAAuthProvider:
    """OAuth 1.0 authentication provider for NetSuite TBA"""

    def __init__(self, settings):
        self.account_id = settings.ns_account_id
        self.consumer_key = settings.ns_consumer_key
        self.consumer_secret = settings.ns_consumer_secret
        self.token_id = settings.ns_token_id
        self.token_secret = settings.ns_token_secret

    def get_auth_headers(self, url: str, method: str = "GET") -> dict[str, str]:
        """Generate OAuth 1.0 Authorization header

        Args:
            url: Full URL including query parameters
            method: HTTP method (GET, POST, etc.)

        Returns:
            Dictionary with Authorization header
        """
        # OAuth parameters
        oauth_params = {
            "oauth_consumer_key": self.consumer_key,
            "oauth_token": self.token_id,
            "oauth_signature_method": "HMAC-SHA256",
            "oauth_timestamp": str(int(time.time())),
            "oauth_nonce": self._generate_nonce(),
            "oauth_version": "1.0",
        }

        # Generate signature
        signature = self._generate_signature(url, method, oauth_params)
        oauth_params["oauth_signature"] = signature

        # Build Authorization header
        return {"Authorization": self._build_auth_header(oauth_params)}

    def _generate_signature(
        self, url: str, method: str, oauth_params: dict
    ) -> str:
        """Generate OAuth 1.0 signature

        CRITICAL: Includes query parameters from URL in signature calculation

        Args:
            url: Full URL including query params
            method: HTTP method
            oauth_params: OAuth parameters (without signature)

        Returns:
            Base64-encoded HMAC-SHA256 signature
        """
        # Parse URL
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"

        # Combine OAuth params with query params
        all_params = dict(oauth_params)
        if parsed_url.query:
            query_params = parse_qsl(parsed_url.query)
            all_params.update({k: str(v) for k, v in query_params})

        # Build parameter string (sorted alphabetically)
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

        # Generate signing key
        signing_key = f"{self.consumer_secret}&{self.token_secret}"

        # Calculate HMAC-SHA256
        signature_bytes = hmac.new(
            key=signing_key.encode("utf-8"),
            msg=signature_base_string.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()

        # Base64 encode
        return base64.b64encode(signature_bytes).decode("utf-8")

    def _build_auth_header(self, oauth_params: dict) -> str:
        """Build OAuth Authorization header

        Args:
            oauth_params: OAuth parameters including signature

        Returns:
            Authorization header value
        """
        auth_header_parts = [
            f'{quote(str(k), safe="")}="{quote(str(v), safe="")}"'
            for k, v in sorted(oauth_params.items())
        ]
        return "OAuth " + ", ".join(auth_header_parts)

    def _generate_nonce(self) -> str:
        """Generate random nonce for request uniqueness"""
        return secrets.token_hex(16)
```

**Reference:** `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/auth_tba.py`

### Client Integration

```python
class NetSuiteClient:
    def _request(self, method: str, endpoint: str, params=None):
        """Make authenticated request

        CRITICAL: Build full URL before generating auth headers
        """
        # Build full URL including query parameters
        base_url = f"{self.base_url}/{endpoint}"

        if params:
            from urllib.parse import urlencode
            query_string = urlencode(params)
            full_url = f"{base_url}?{query_string}"
        else:
            full_url = base_url

        # Get auth headers using FULL URL (with query params)
        headers = self.auth.get_auth_headers(url=full_url, method=method)
        headers["Accept"] = "application/json"

        # Make request with full URL
        response = self.client.request(method=method, url=full_url, headers=headers)
        return response
```

**Reference:** `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/client.py`

---

## Common Issues and Solutions

### Issue: 401 "Invalid login attempt"

**Possible causes:**

1. **Query params not included in signature** (most common)
   - **Fix:** Build full URL with params before calling `get_auth_headers()`

2. **Wrong HTTP method**
   - **Fix:** Ensure method matches actual request (GET vs POST)

3. **Timestamp drift**
   - **Fix:** Verify system clock is accurate (within a few minutes)

4. **Encoding errors**
   - **Fix:** Use `quote(str, safe='')` for all encoding, no exceptions

5. **Wrong secrets**
   - **Fix:** Verify consumer_secret and token_secret are correct

### Issue: Signature Mismatch on Pagination

**Symptom:** First request succeeds (offset=0), subsequent requests fail (offset=100, 200, etc.)

**Cause:** Offset parameter added after signature generation

**Fix:**
```python
# ❌ WRONG
headers = auth.get_auth_headers(base_url)
for offset in range(0, 1000, 100):
    response = httpx.get(base_url, params={"offset": offset}, headers=headers)
    # Only first request works!

# ✅ CORRECT
for offset in range(0, 1000, 100):
    full_url = f"{base_url}?offset={offset}"
    headers = auth.get_auth_headers(full_url)  # Generate new signature per request
    response = httpx.get(full_url, headers=headers)
```

### Issue: Nonce Collision

**Symptom:** Intermittent 401 errors when making rapid requests

**Cause:** Same nonce used for multiple requests

**Fix:**
```python
def _generate_nonce(self) -> str:
    """Generate cryptographically random nonce"""
    return secrets.token_hex(16)  # Use secrets module, not random
```

### Issue: Timestamp Too Old

**Symptom:** 401 error with "timestamp too old" message

**Cause:** Request took too long, timestamp expired

**Fix:**
- Generate signature immediately before request
- Don't reuse headers across requests
- Check system clock accuracy

---

## Verification and Testing

### Test Signature Generation

```python
def test_signature():
    """Test signature generation with known values"""
    auth = TBAAuthProvider(settings)

    # Test URL with query params
    url = "https://610574.suitetalk.api.netsuite.com/services/rest/record/v1/vendor?limit=10&offset=0"

    headers = auth.get_auth_headers(url, "GET")

    print(f"Authorization header: {headers['Authorization']}")

    # Verify header contains:
    # - oauth_consumer_key
    # - oauth_token
    # - oauth_signature
    # - oauth_timestamp
    # - oauth_nonce
    # - oauth_signature_method
    # - oauth_version

    assert "oauth_signature=" in headers["Authorization"]
    assert "oauth_consumer_key=" in headers["Authorization"]
    print("✓ Signature generated correctly")
```

### Test with Live API

```python
def test_live_request():
    """Test authentication with actual NetSuite request"""
    from vendor_analysis.netsuite.client import NetSuiteClient

    client = NetSuiteClient(settings)

    try:
        # Simple query with parameters
        response = client.query_records(record_type="vendor", limit=1, offset=0)

        if response:
            print("✓ Authentication successful!")
            print(f"  Response: {response}")
        else:
            print("✗ Authentication failed")
    except Exception as e:
        print(f"✗ Error: {e}")
```

### Debug Signature Components

```python
def debug_signature(url, method="GET"):
    """Print all signature components for debugging"""
    auth = TBAAuthProvider(settings)

    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"

    oauth_params = {
        "oauth_consumer_key": auth.consumer_key,
        "oauth_token": auth.token_id,
        "oauth_signature_method": "HMAC-SHA256",
        "oauth_timestamp": str(int(time.time())),
        "oauth_nonce": auth._generate_nonce(),
        "oauth_version": "1.0",
    }

    # Show query params
    query_params = {}
    if parsed_url.query:
        query_params = dict(parse_qsl(parsed_url.query))

    print("=" * 80)
    print("OAuth Signature Debug")
    print("=" * 80)
    print(f"Full URL: {url}")
    print(f"Base URL: {base_url}")
    print(f"Query params: {query_params}")
    print(f"OAuth params: {oauth_params}")

    # Combine params
    all_params = dict(oauth_params)
    all_params.update(query_params)
    print(f"All params (OAuth + Query): {all_params}")

    # Generate signature
    signature = auth._generate_signature(url, method, oauth_params)
    print(f"Signature: {signature}")
    print("=" * 80)
```

**Reference:** `/opt/ns/apps/vendor-analysis/scripts/diagnose_auth.py`

---

## Related Patterns

- **Multi-Method Authentication**: [authentication-methods.md](authentication-methods.md)
- **Diagnostics Without UI Access**: [testing/diagnostics-without-ui.md](../testing/diagnostics-without-ui.md)
- **REST API Query Patterns**: [rest-api-queries.md](rest-api-queries.md) (auth required for all requests)

---

## Summary

**Key Points:**

1. **Query params MUST be in signature** - most common bug
2. **Build full URL before generating signature** - include all params
3. **Generate new signature per request** - don't reuse headers
4. **Use HMAC-SHA256** - only supported method for NetSuite
5. **Both secrets required** - consumer_secret AND token_secret
6. **URL encode everything** - no exceptions
7. **Sort params alphabetically** - critical for signature matching

**This pattern prevents 401 authentication errors caused by query parameter signature bugs, saving hours of debugging time.**

**Reference Implementation:** `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/auth_tba.py`
