# Authentication Methods

NetSuite authentication patterns including credential vernacular, TBA (OAuth 1.0), OAuth 2.0, and multi-method support.

## Contents

- Credential Vernacular (NetSuite Standard)
- TBA (Token-Based Authentication) - OAuth 1.0
- OAuth 2.0 Client Credentials
- Multi-Method Factory Pattern
- Configuration Examples

---

## Credential Vernacular (NetSuite Standard)

NetSuite uses specific terminology for authentication credentials. Using incorrect names causes confusion and implementation errors.

### CORRECT Terminology

```bash
# NetSuite standard credential names
NS_CONSUMER_KEY=...       # From Integration Record
NS_CONSUMER_SECRET=...    # From Integration Record
NS_TOKEN_ID=...           # From Access Token (TBA only)
NS_TOKEN_SECRET=...       # From Access Token (TBA only)
```

**Why "CONSUMER" not "CLIENT":**
- NetSuite documentation uses "Consumer Key/Secret"
- Integration Record labels use "Consumer"
- OAuth 1.0 specification uses "Consumer"
- "Client" is OAuth 2.0 terminology, causes confusion

### INCORRECT (Don't Use)

```bash
# ❌ WRONG - Confusing and non-standard
NS_CLIENT_ID=...          # Should be NS_CONSUMER_KEY
NS_CLIENT_SECRET=...      # Should be NS_CONSUMER_SECRET
```

**Impact:** Using CLIENT instead of CONSUMER makes code harder to understand and documentation searches more difficult.

---

## TBA (Token-Based Authentication) - OAuth 1.0

**Status:** DEPRECATED February 2025, but still widely used in existing integrations

### Overview

TBA uses OAuth 1.0 with HMAC-SHA256 signatures to authenticate API requests.

### Required Credentials (4 total)

TBA requires **two credential pairs** from different NetSuite locations:

**1. Consumer Credentials (from Integration Record)**
- Consumer Key - Public identifier for your application
- Consumer Secret - Secret used to sign requests

**2. Token Credentials (from Access Token)**
- Token ID - Identifies specific user/role
- Token Secret - Secret used to sign requests

### Credential Sources

**Integration Record** (Consumer credentials):
1. NetSuite UI: Setup > Integration > Manage Integrations
2. Create or find your integration
3. Copy Consumer Key and Consumer Secret
4. Ensure "Token-Based Authentication" is checked
5. Status must be "Enabled"

**Access Token** (Token credentials):
1. NetSuite UI: Setup > Users/Roles > Access Tokens
2. Create new token for specific user and role
3. Copy Token ID and Token Secret (shown only once!)
4. Token must be "Active" (not Revoked)
5. Role must have required permissions

### Environment Variables

```bash
# NetSuite Account
NS_ACCOUNT_ID=610574

# TBA (OAuth 1.0) - 4 credentials required
# From Integration Record (Setup > Integration > Manage Integrations)
NS_CONSUMER_KEY=bf53d76ed90272357816...
NS_CONSUMER_SECRET=bfde7978f8397e413f2ca145...

# From Access Token (Setup > Users/Roles > Access Tokens)
NS_TOKEN_ID=e6229be96752005bc32fdb...
NS_TOKEN_SECRET=c0e4b2b5dc4c386ba0ef5271...
```

### Authentication Flow

1. Build OAuth 1.0 parameters (consumer key, token, timestamp, nonce)
2. Generate signature base string including URL and query parameters
3. Sign with HMAC-SHA256 using consumer secret and token secret
4. Build Authorization header with signature
5. Make request with Authorization header

### Critical Implementation Detail

**Query parameters MUST be included in signature base string.**

See [oauth-signatures.md](oauth-signatures.md) for complete signature generation pattern.

### Code Example

Reference implementation: `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/auth_tba.py`

```python
class TBAAuthProvider(NetSuiteAuthProvider):
    def get_auth_headers(self, url: str, method: str = "GET") -> dict[str, str]:
        oauth_params = {
            "oauth_consumer_key": self.settings.ns_consumer_key,
            "oauth_token": self.settings.ns_token_id,
            "oauth_signature_method": "HMAC-SHA256",
            "oauth_timestamp": str(int(time.time())),
            "oauth_nonce": self._generate_nonce(),
            "oauth_version": "1.0",
        }

        signature = self._generate_signature(url, method, oauth_params)
        oauth_params["oauth_signature"] = signature

        return {"Authorization": self._build_auth_header(oauth_params)}
```

---

## OAuth 2.0 Client Credentials

**Status:** Required for new integrations 2025+

### Overview

OAuth 2.0 uses simpler bearer token authentication without complex signature generation.

### Required Credentials (2 total)

OAuth 2.0 requires **only consumer credentials**:

**Consumer Credentials (from Integration Record)**
- Consumer Key - Public identifier
- Consumer Secret - Used to obtain access tokens

**No token credentials needed** - OAuth 2.0 doesn't use the 4-credential TBA pattern.

### Credential Source

**Integration Record only:**
1. NetSuite UI: Setup > Integration > Manage Integrations
2. Create or find your integration
3. Copy Consumer Key and Consumer Secret
4. Ensure "OAuth 2.0" is selected
5. Status must be "Enabled"

### Environment Variables

```bash
# NetSuite Account
NS_ACCOUNT_ID=610574

# OAuth 2.0 - 2 credentials only
# From Integration Record (Setup > Integration > Manage Integrations)
NS_CONSUMER_KEY=bf53d76ed90272357816...
NS_CONSUMER_SECRET=bfde7978f8397e413f2ca145...

# No NS_TOKEN_ID or NS_TOKEN_SECRET needed for OAuth 2.0
```

### Authentication Flow

1. Request access token from token endpoint
2. Receive bearer token (valid for 1 hour)
3. Include token in Authorization header
4. Refresh token when expired

### Code Example

Reference implementation: `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/auth.py`

```python
class OAuth2AuthProvider(NetSuiteAuthProvider):
    def get_auth_headers(self, url: str, method: str = "GET") -> dict[str, str]:
        token = self.get_access_token()
        return {"Authorization": f"Bearer {token}"}

    def get_access_token(self) -> str:
        # Request token from NetSuite
        response = httpx.post(
            f"https://{self.account_id}.suitetalk.api.netsuite.com/services/rest/auth/oauth2/v1/token",
            data={"grant_type": "client_credentials"},
            auth=(self.consumer_key, self.consumer_secret)
        )
        return response.json()["access_token"]
```

---

## Multi-Method Factory Pattern

Support multiple authentication methods in a single application using abstraction and factory pattern.

### Why Multi-Method Support

**Common scenarios:**
- Migrating from TBA to OAuth 2.0 before February 2025 deadline
- Supporting different environments (sandbox uses TBA, production uses OAuth 2.0)
- Maintaining backward compatibility during transition

### Abstract Base Class

```python
from abc import ABC, abstractmethod

class NetSuiteAuthProvider(ABC):
    """Abstract base class for NetSuite authentication providers"""

    @abstractmethod
    def get_auth_headers(self, url: str, method: str) -> dict[str, str]:
        """Generate authentication headers for a request

        Args:
            url: Full URL including query parameters (required for OAuth 1.0 signature)
            method: HTTP method (GET, POST, etc.)

        Returns:
            Dictionary of headers to include in request
        """
        pass
```

**Key design decision:** Interface accepts `url` parameter because OAuth 1.0 signatures depend on the full URL including query parameters. OAuth 2.0 implementations can ignore this parameter.

### Concrete Implementations

```python
# auth_tba.py
class TBAAuthProvider(NetSuiteAuthProvider):
    def get_auth_headers(self, url: str, method: str) -> dict[str, str]:
        # Generate OAuth 1.0 signature using url and method
        return {"Authorization": f"OAuth {signature}"}

# auth.py (OAuth 2.0)
class OAuth2AuthProvider(NetSuiteAuthProvider):
    def get_auth_headers(self, url: str, method: str) -> dict[str, str]:
        # URL/method not needed for OAuth 2.0 bearer token
        token = self.get_access_token()
        return {"Authorization": f"Bearer {token}"}
```

### Factory Selection

```python
# auth_factory.py
def create_auth_provider(settings: Settings) -> NetSuiteAuthProvider:
    """Create appropriate auth provider based on configuration

    Args:
        settings: Application settings containing auth_method

    Returns:
        Configured authentication provider

    Raises:
        ValueError: If auth_method is unknown
    """
    auth_method = settings.yaml_config.application.auth_method.lower()

    if auth_method == "tba":
        return TBAAuthProvider(settings)
    elif auth_method == "oauth2":
        return OAuth2AuthProvider(settings)
    else:
        raise ValueError(
            f"Unknown authentication method: {auth_method}. "
            f"Valid options: 'tba', 'oauth2'"
        )
```

### Configuration

**config.yaml:**
```yaml
application:
  log_level: INFO
  auth_method: tba  # or "oauth2"
```

**.env:**
```bash
# Include credentials for your chosen auth method
# For TBA: all 4 credentials
# For OAuth 2.0: only consumer key/secret
NS_ACCOUNT_ID=...
NS_CONSUMER_KEY=...
NS_CONSUMER_SECRET=...
NS_TOKEN_ID=...        # TBA only
NS_TOKEN_SECRET=...    # TBA only
```

### Client Usage

```python
# client.py
class NetSuiteClient:
    def __init__(self, settings: Settings):
        # Factory creates appropriate provider
        self.auth = create_auth_provider(settings)

    def _request(self, method: str, endpoint: str, params=None):
        # Build full URL
        full_url = f"{self.base_url}/{endpoint}"
        if params:
            query_string = urlencode(params)
            full_url = f"{full_url}?{query_string}"

        # Get auth headers (works for both TBA and OAuth 2.0)
        headers = self.auth.get_auth_headers(url=full_url, method=method)
        headers["Accept"] = "application/json"

        return self.http_client.request(method=method, url=full_url, headers=headers)
```

**Reference implementation:** `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/`

---

## TBA vs OAuth 2.0 Comparison

| Aspect | TBA (OAuth 1.0) | OAuth 2.0 |
|--------|----------------|-----------|
| **Status** | Deprecated Feb 2025 | Required 2025+ |
| **Credentials** | 4 (Consumer + Token) | 2 (Consumer only) |
| **Credential Sources** | Integration Record + Access Token | Integration Record only |
| **Signature** | HMAC-SHA256 with URL/params | None (bearer token) |
| **Token Lifetime** | No expiration | 1 hour (refresh required) |
| **Implementation Complexity** | High (signature calculation) | Medium (token refresh) |
| **Query Param Handling** | Must include in signature | No signature required |
| **Migration Path** | Must migrate by Feb 2025 | N/A (is the target) |

---

## Common Errors and Solutions

### Error: "Invalid login attempt" (401)

**Possible causes:**
1. Query parameters not included in OAuth 1.0 signature (TBA)
2. Integration record is disabled
3. Access token is revoked
4. Wrong account ID or environment (Production vs Sandbox)

**Solutions:**
1. Ensure full URL with query params used for signature - see [oauth-signatures.md](oauth-signatures.md)
2. Check Integration Record status in NetSuite UI
3. Check Access Token status (must be Active, not Revoked)
4. Verify account ID matches environment

### Error: "400 invalid_request" (OAuth 2.0)

**Possible causes:**
1. Using CLIENT_ID/CLIENT_SECRET instead of CONSUMER_KEY/SECRET
2. Missing credentials in request
3. Integration not configured for OAuth 2.0

**Solutions:**
1. Rename credentials to use CONSUMER terminology
2. Verify all required credentials present in environment
3. Check Integration Record has OAuth 2.0 enabled

### Error: Incomplete credentials

**Symptoms:** Application fails to start with missing credential error

**Cause:** TBA requires 4 credentials; OAuth 2.0 requires 2

**Solution:**
- For TBA: Ensure all 4 credentials present (CONSUMER_KEY, CONSUMER_SECRET, TOKEN_ID, TOKEN_SECRET)
- For OAuth 2.0: Only CONSUMER_KEY and CONSUMER_SECRET needed

---

## Diagnostic Tools

When authentication fails and you don't have NetSuite UI access, use programmatic diagnostics.

See [testing/diagnostics-without-ui.md](../testing/diagnostics-without-ui.md) for complete diagnostic patterns.

**Quick diagnostic script:**

```python
def diagnose_auth():
    """Test authentication and provide actionable error messages"""
    print(f"Account: {account_id}")
    print(f"Auth Method: {auth_method}")
    print(f"Consumer Key: {consumer_key[:20]}...")

    try:
        response = client.get('/vendor?limit=1')
        if response.status_code == 200:
            print("✓ Authentication successful!")
        else:
            print(f"✗ Auth failed: {response.status_code}")
            print_admin_checklist(response.status_code)
    except Exception as e:
        print(f"✗ Request failed: {e}")
```

Reference: `/opt/ns/apps/vendor-analysis/scripts/diagnose_auth.py`

---

## Migration Path: TBA to OAuth 2.0

### Timeline

NetSuite deprecates TBA in February 2025. All integrations must migrate to OAuth 2.0 by this date.

### Migration Steps

1. **Create OAuth 2.0 integration record** in NetSuite
2. **Update configuration** to support both methods (use factory pattern)
3. **Test OAuth 2.0** in sandbox environment
4. **Deploy with config toggle** to easily switch between methods
5. **Monitor and verify** OAuth 2.0 works in production
6. **Switch config** from TBA to OAuth 2.0
7. **Remove TBA credentials** after successful migration

### Backward Compatibility During Migration

Use the multi-method factory pattern to support both during transition:

```yaml
# config.yaml - Easy toggle for testing
application:
  auth_method: tba  # Switch to "oauth2" when ready
```

This allows quick rollback if OAuth 2.0 has issues in production.

---

## Reference Implementations

**Complete working examples:**
- Factory pattern: `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/auth_factory.py`
- TBA provider: `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/auth_tba.py`
- OAuth 2.0 provider: `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/auth.py`
- Base abstraction: `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/auth_base.py`
- Client integration: `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/client.py`
- Configuration: `/opt/ns/apps/vendor-analysis/src/vendor_analysis/core/config.py`
- Diagnostics: `/opt/ns/apps/vendor-analysis/scripts/diagnose_auth.py`

---

## Related Patterns

- **OAuth 1.0 Signature Generation**: [oauth-signatures.md](oauth-signatures.md)
- **Diagnostics Without UI Access**: [testing/diagnostics-without-ui.md](../testing/diagnostics-without-ui.md)
- **Configuration Management**: See python-cli-engineering skill for dual config pattern (YAML + .env)
