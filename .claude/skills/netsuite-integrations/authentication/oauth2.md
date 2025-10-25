# OAuth 2.0 Authentication

Complete guide to NetSuite OAuth 2.0 Client Credentials authentication for integrations, including migration from TBA and comparison.

## Status and Timeline

**REQUIRED:** OAuth 2.0 is the standard authentication method for NetSuite integrations as of February 2025.

**Timeline:**
- TBA (OAuth 1.0) deprecated February 2025
- All new integrations must use OAuth 2.0
- Existing TBA integrations must migrate before February 2025

---

## OAuth 2.0 Setup

OAuth 2.0 uses simpler bearer token authentication without complex signature generation.

### Required Credentials (2 Only)

OAuth 2.0 requires **only consumer credentials from Integration Record**:

**From Integration Record** (Setup > Integration > Manage Integrations):
1. **Consumer Key** - Public identifier for your application
2. **Consumer Secret** - Used to obtain access tokens

**No token credentials needed** - OAuth 2.0 doesn't require the separate Access Token that TBA does.

### NetSuite UI Steps

**Create Integration Record:**

1. Navigate to Setup > Integration > Manage Integrations > New
2. Fill in integration details:
   - Name: Your integration name
   - State: Enabled
   - Authentication: Select "OAuth 2.0"
3. Save and copy:
   - **Consumer Key** (long hex string)
   - **Consumer Secret** (long hex string, shown only once!)
4. Important: Status must be "Enabled"

### Environment Variables

```bash
# NetSuite Account
NS_ACCOUNT_ID=610574

# OAuth 2.0 - Only 2 credentials needed
# From Integration Record (Setup > Integration > Manage Integrations)
NS_CONSUMER_KEY=bf53d76ed90272357816199b65ab9dab388efa5dee228fefb6f4b9cd1fd706a7
NS_CONSUMER_SECRET=bfde7978f8397e413f2ca145869cd31ef27826204931b1f97b446096795cc444

# No NS_TOKEN_ID or NS_TOKEN_SECRET needed for OAuth 2.0
```

**Credential naming:** Use "CONSUMER" not "CLIENT" - matches NetSuite terminology across both OAuth 2.0 and TBA.

---

## OAuth 2.0 Authentication Flow

### 1. Request Access Token

**Endpoint:** `POST https://{accountId}.suitetalk.api.netsuite.com/services/rest/auth/oauth2/v1/token`

**Request:**
```http
POST /services/rest/auth/oauth2/v1/token HTTP/1.1
Host: 610574.suitetalk.api.netsuite.com
Content-Type: application/x-www-form-urlencoded
Authorization: Basic {base64(consumer_key:consumer_secret)}

grant_type=client_credentials
```

**Python Implementation:**
```python
import httpx
import base64

def get_access_token(account_id, consumer_key, consumer_secret):
    """Request OAuth 2.0 access token

    Returns:
        Access token string
    """
    # Build Authorization header
    credentials = f"{consumer_key}:{consumer_secret}"
    encoded = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {"grant_type": "client_credentials"}

    url = f"https://{account_id}.suitetalk.api.netsuite.com/services/rest/auth/oauth2/v1/token"

    response = httpx.post(url, headers=headers, data=data)
    response.raise_for_status()

    return response.json()["access_token"]
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

**Token lifetime:** 1 hour (3600 seconds)

### 2. Use Access Token

Include token in Authorization header for all API requests:

```python
def make_request(account_id, access_token, endpoint, params=None):
    """Make authenticated request using OAuth 2.0 token

    Args:
        access_token: Token from get_access_token()
        endpoint: API endpoint path
        params: Optional query parameters

    Returns:
        Response JSON
    """
    base_url = f"https://{account_id}.suitetalk.api.netsuite.com"
    url = f"{base_url}/{endpoint}"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }

    response = httpx.get(url, params=params, headers=headers)
    response.raise_for_status()

    return response.json()
```

### 3. Refresh When Expired

Access tokens expire after 1 hour. Request new token when needed:

```python
class OAuth2Auth:
    """OAuth 2.0 authentication with token caching"""

    def __init__(self, account_id, consumer_key, consumer_secret):
        self.account_id = account_id
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = None
        self.token_expiry = None

    def get_token(self):
        """Get valid access token (cached or fresh)"""
        from datetime import datetime, timedelta

        # Check if cached token is still valid
        if self.access_token and self.token_expiry:
            if datetime.now() < self.token_expiry - timedelta(minutes=5):
                return self.access_token

        # Request new token
        self.access_token = self._request_token()
        self.token_expiry = datetime.now() + timedelta(hours=1)

        return self.access_token

    def _request_token(self):
        """Request new access token"""
        credentials = f"{self.consumer_key}:{self.consumer_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        url = f"https://{self.account_id}.suitetalk.api.netsuite.com/services/rest/auth/oauth2/v1/token"

        response = httpx.post(url, headers=headers, data={"grant_type": "client_credentials"})
        response.raise_for_status()

        return response.json()["access_token"]
```

**Reference:** `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/auth.py`

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
| **Migration Required** | Yes, before Feb 2025 | N/A (is the target) |

### Key Differences

**Simpler Setup:**
- OAuth 2.0: 2 credentials from one location
- TBA: 4 credentials from two locations

**No Signature Complexity:**
- OAuth 2.0: Simple bearer token
- TBA: Complex OAuth 1.0 signature with query param bug

**Token Management:**
- OAuth 2.0: Tokens expire (1 hour), must refresh
- TBA: Tokens don't expire

**URL Construction:**
- OAuth 2.0: Query params can be added normally
- TBA: Query params must be in URL before signature generation

---

## Migration from TBA to OAuth 2.0

### Migration Timeline

**Deadline:** February 2025

**Recommended approach:**
1. Create OAuth 2.0 integration in NetSuite (now)
2. Test OAuth 2.0 in sandbox environment
3. Deploy with multi-method support (factory pattern)
4. Switch to OAuth 2.0 in production
5. Monitor and verify
6. Remove TBA code after successful migration

### Multi-Method Support During Migration

Use factory pattern to support both TBA and OAuth 2.0 simultaneously:

```python
# auth_base.py
from abc import ABC, abstractmethod

class NetSuiteAuthProvider(ABC):
    @abstractmethod
    def get_auth_headers(self, url: str, method: str) -> dict[str, str]:
        """Generate authentication headers"""
        pass

# auth_factory.py
def create_auth_provider(settings) -> NetSuiteAuthProvider:
    """Create auth provider based on configuration"""
    auth_method = settings.yaml_config.application.auth_method.lower()

    if auth_method == "tba":
        return TBAAuthProvider(settings)
    elif auth_method == "oauth2":
        return OAuth2AuthProvider(settings)
    else:
        raise ValueError(f"Unknown auth method: {auth_method}")
```

**Configuration:**
```yaml
# config.yaml
application:
  auth_method: oauth2  # Switch from "tba" to "oauth2"
```

**Benefits:**
- Easy toggle between methods
- Test OAuth 2.0 without removing TBA code
- Quick rollback if issues arise
- Gradual migration across environments

**Reference:** `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/auth_factory.py`

### Migration Checklist

**Pre-Migration:**
- [ ] Create OAuth 2.0 Integration Record in NetSuite
- [ ] Copy Consumer Key and Consumer Secret
- [ ] Test OAuth 2.0 in sandbox environment
- [ ] Implement token refresh logic
- [ ] Implement multi-method factory pattern

**Migration:**
- [ ] Deploy code with OAuth 2.0 support
- [ ] Update configuration to use OAuth 2.0
- [ ] Verify all API calls work correctly
- [ ] Monitor for 401/403 errors
- [ ] Check token refresh logic works

**Post-Migration:**
- [ ] Confirm all integrations using OAuth 2.0
- [ ] Remove TBA credentials from secrets
- [ ] Remove TBA code from codebase
- [ ] Update documentation

---

## Troubleshooting

### 401 Unauthorized

**Possible causes:**

1. **Integration Record disabled**
   - Check: Setup > Integration > Manage Integrations
   - Verify: Status = "Enabled"
   - Verify: "OAuth 2.0" is selected

2. **Wrong credentials**
   - Verify Consumer Key matches Integration Record
   - Verify Consumer Secret matches
   - Check for extra whitespace

3. **Expired token**
   - OAuth 2.0 tokens expire after 1 hour
   - Request new token

4. **Wrong environment**
   - Production credentials with Sandbox account (or vice versa)
   - Verify account ID matches environment

### 403 Forbidden

**Cause:** Insufficient permissions

**Fix:**
1. OAuth 2.0 Client Credentials must be mapped to a role
2. Check Setup > Integration > Manage Integrations > OAuth 2.0
3. Verify role has required permissions:
   - "Web Services" permission
   - Access to required records
   - Required operation permissions (View, Create, Edit, Delete)

### Token Refresh Failures

**Symptom:** Frequent 401 errors, especially after 1 hour

**Cause:** Token not refreshed before expiry

**Fix:** Implement token caching with expiry tracking:

```python
# Cache token and refresh 5 minutes before expiry
if datetime.now() > self.token_expiry - timedelta(minutes=5):
    self.access_token = self._request_token()
    self.token_expiry = datetime.now() + timedelta(hours=1)
```

---

## Best Practices

1. **Cache access tokens**
   - Don't request new token for every API call
   - Cache for up to 1 hour
   - Refresh 5 minutes before expiry

2. **Store secrets securely**
   - Use environment variables or secure vault
   - Never commit secrets to version control
   - Consumer Secret shown only once in NetSuite

3. **Handle token expiry gracefully**
   - Implement automatic refresh
   - Retry 401 errors with fresh token
   - Log token refresh events

4. **Plan multi-method support**
   - Support both TBA and OAuth 2.0 during migration
   - Use factory pattern for flexibility
   - Easy configuration toggle

5. **Test thoroughly**
   - Test in sandbox before production
   - Test token refresh logic
   - Test long-running operations (> 1 hour)

6. **Monitor token usage**
   - Log token requests
   - Alert on frequent token refresh
   - Track 401 error rates

---

## Related Documentation

**This Skill:**
- [tba.md](tba.md) - TBA authentication (deprecated)
- [../suitetalk/rest-api.md](../suitetalk/rest-api.md) - REST API usage
- [../patterns/data-fetching.md](../patterns/data-fetching.md) - Data fetching strategies

**NetSuite Developer Skill:**
- `patterns/authentication-methods.md` - Multi-method auth patterns
- `examples/vendor-sync-complete.md` - OAuth 2.0 in production

**Local KB:**
- `/opt/ns/kb/authentication.md` - NetSuite authentication overview

**Reference Implementation:**
- `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/auth.py` - OAuth 2.0 implementation
- `/opt/ns/apps/vendor-analysis/src/vendor_analysis/netsuite/auth_factory.py` - Multi-method factory

**NetSuite Documentation:**
- OAuth 2.0 setup guide
- Client Credentials flow
- Integration Record configuration

---

## Summary

**Key Points:**

1. **OAuth 2.0 required 2025+** - TBA deprecated February 2025
2. **Only 2 credentials needed** - Consumer Key/Secret from Integration Record
3. **Bearer token authentication** - No complex signatures
4. **Tokens expire after 1 hour** - Must implement refresh logic
5. **Simpler than TBA** - No query param signature bugs
6. **Multi-method support recommended** - Enables gradual migration
7. **Test in sandbox first** - Verify OAuth 2.0 before production

**OAuth 2.0 is simpler and more secure than TBA. All NetSuite integrations must migrate before February 2025.**
