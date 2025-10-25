# Diagnostics Without NetSuite UI Access

Patterns for testing and troubleshooting NetSuite integrations programmatically when you don't have access to NetSuite's web interface.

## Contents

- The Challenge
- Diagnostic Script Pattern
- Testing Authentication
- Admin Checklists for Common Errors
- Credential Verification
- Connection Testing
- Related Patterns

---

## The Challenge

Developers building NetSuite integrations often lack direct access to the NetSuite web UI:

**Common scenarios:**
- External consultants with API credentials only
- CI/CD pipelines with service account credentials
- Debugging production issues without admin access
- Testing integrations in sandbox environments

**Need to diagnose:**
- Are credentials correct?
- Is authentication configured properly in NetSuite?
- Which specific setting is causing 401/403 errors?
- What should the NetSuite admin check?

**Solution:** Programmatic diagnostics that provide actionable information without requiring NetSuite UI access.

---

## Diagnostic Script Pattern

Create standalone diagnostic scripts that test connectivity and provide clear error messages.

### Basic Diagnostic Script

```python
#!/usr/bin/env python3
"""
NetSuite Authentication Diagnostic Tool

Tests authentication configuration and provides actionable error messages
without requiring NetSuite UI access.
"""

import sys
from vendor_analysis.core.config import get_settings
from vendor_analysis.netsuite.client import NetSuiteClient

def mask_credential(cred: str, visible_chars: int = 20) -> str:
    """Mask credential for safe display"""
    if not cred or len(cred) <= visible_chars:
        return cred
    return f"{cred[:visible_chars]}..."

def diagnose_authentication():
    """Test authentication and provide diagnostic information"""
    print("=" * 80)
    print("NetSuite Authentication Diagnostic")
    print("=" * 80)

    # Load configuration
    try:
        settings = get_settings()
        print("✓ Configuration loaded successfully")
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        print("\nCheck:")
        print("  - .env file exists and is readable")
        print("  - config.yaml exists and is valid YAML")
        return

    # Display configuration (masked)
    print("\nConfiguration:")
    print(f"  Account ID: {settings.ns_account_id}")
    print(f"  Auth Method: {settings.yaml_config.application.auth_method}")
    print(f"  Consumer Key: {mask_credential(settings.ns_consumer_key)}")
    print(f"  Consumer Secret: {mask_credential(settings.ns_consumer_secret)}")

    if settings.yaml_config.application.auth_method == "tba":
        print(f"  Token ID: {mask_credential(settings.ns_token_id)}")
        print(f"  Token Secret: {mask_credential(settings.ns_token_secret)}")

    # Test authentication
    print("\nTesting authentication...")

    try:
        client = NetSuiteClient(settings)
        response = client.query_records(record_type="vendor", limit=1, offset=0)

        if response:
            print("✓ Authentication successful!")
            print(f"  Response: {response.get('count', 0)} vendors found")
            print("\n" + "=" * 80)
            print("SUCCESS: Integration is working correctly")
            print("=" * 80)
            return True
        else:
            print("✗ Unexpected empty response")
            return False

    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        print_diagnostic_checklist(e, settings)
        return False

def print_diagnostic_checklist(error: Exception, settings):
    """Print actionable checklist for NetSuite admin"""
    error_str = str(error)

    print("\n" + "=" * 80)
    print("DIAGNOSTIC CHECKLIST FOR NETSUITE ADMIN")
    print("=" * 80)

    if "401" in error_str or "Unauthorized" in error_str:
        print_401_checklist(settings)
    elif "403" in error_str or "Forbidden" in error_str:
        print_403_checklist(settings)
    elif "400" in error_str:
        print_400_checklist(settings)
    else:
        print_general_checklist(settings)

def print_401_checklist(settings):
    """Checklist for 401 Unauthorized errors"""
    print("\n401 UNAUTHORIZED - Authentication credentials rejected")
    print("\nNetSuite admin must verify the following in NetSuite UI:")

    print("\n1. Integration Record (Setup > Integration > Manage Integrations)")
    print(f"   □ Find integration with Consumer Key: {mask_credential(settings.ns_consumer_key)}")
    print("   □ Verify Status = 'Enabled' (not Disabled)")
    if settings.yaml_config.application.auth_method == "tba":
        print("   □ Verify 'Token-Based Authentication' checkbox is CHECKED")
    else:
        print("   □ Verify 'OAuth 2.0' is selected")

    if settings.yaml_config.application.auth_method == "tba":
        print("\n2. Access Token (Setup > Users/Roles > Access Tokens)")
        print(f"   □ Find token with Token ID: {mask_credential(settings.ns_token_id)}")
        print("   □ Verify Status = 'Active' (not Revoked)")
        print("   □ Verify token is for correct user and role")
        print("   □ Verify role has required permissions")

    print("\n3. Login Audit Trail (Setup > Users/Roles > View Login Audit Trail)")
    print("   □ Filter by Integration")
    print("   □ Look for failed login attempts")
    print("   □ Check error message for specific reason")

    print("\n4. Verify Credentials Match")
    print("   □ Consumer Key matches exactly (no extra spaces/characters)")
    print("   □ Consumer Secret matches exactly")
    if settings.yaml_config.application.auth_method == "tba":
        print("   □ Token ID matches exactly")
        print("   □ Token Secret matches exactly")

    print("\n5. Environment Check")
    print(f"   □ Account ID '{settings.ns_account_id}' is correct")
    print("   □ Using correct environment (Production vs Sandbox)")

def print_403_checklist(settings):
    """Checklist for 403 Forbidden errors"""
    print("\n403 FORBIDDEN - Insufficient permissions")
    print("\nNetSuite admin must verify permissions:")

    if settings.yaml_config.application.auth_method == "tba":
        print("\n1. Role Permissions (Setup > Users/Roles > Manage Roles)")
        print("   □ Find role associated with Access Token")
        print("   □ Verify role has 'Web Services' permission")
        print("   □ Verify role has access to Vendor records")
        print("   □ Verify role has 'Lists > View' permission at minimum")
        print("   □ For write operations, verify 'Lists > Create/Edit' permissions")
    else:
        print("\n1. Client Credentials Mapping (OAuth 2.0)")
        print("   □ Verify OAuth 2.0 client credentials are mapped to a role")
        print("   □ Verify mapped role has required permissions")

def print_400_checklist(settings):
    """Checklist for 400 Bad Request errors"""
    print("\n400 BAD REQUEST - Malformed request")
    print("\nPossible causes:")
    print("   □ Invalid query parameters")
    print("   □ Malformed URL")
    print("   □ Unsupported parameters (e.g., expandSubResources)")
    print("   □ Invalid record type")
    print("\nCheck application logs for request details")

def print_general_checklist(settings):
    """General troubleshooting checklist"""
    print("\nGENERAL TROUBLESHOOTING")
    print("\n1. Network Connectivity")
    print("   □ Can reach NetSuite API endpoint")
    print(f"   □ URL: https://{settings.ns_account_id}.suitetalk.api.netsuite.com")

    print("\n2. Credential Verification")
    print("   □ All required credentials present in .env file")
    print("   □ No extra whitespace in credential values")
    print("   □ Credentials not expired or revoked")

    print("\n3. Configuration")
    print("   □ config.yaml auth_method matches credential type")
    print("   □ Account ID is correct")

if __name__ == "__main__":
    success = diagnose_authentication()
    sys.exit(0 if success else 1)
```

**Reference:** `/opt/ns/apps/vendor-analysis/scripts/diagnose_auth.py`

---

## Testing Authentication

### Quick Auth Test

```python
def quick_auth_test(settings):
    """Quick test to verify authentication works

    Returns:
        Boolean indicating success
    """
    try:
        client = NetSuiteClient(settings)
        # Simple query with minimal data transfer
        response = client.get('/vendor?limit=1')
        return response.status_code == 200
    except Exception:
        return False
```

### Detailed Auth Test

```python
def detailed_auth_test(settings):
    """Detailed authentication test with diagnostic output

    Returns:
        Dict with test results and diagnostic info
    """
    results = {
        "success": False,
        "auth_method": settings.yaml_config.application.auth_method,
        "account_id": settings.ns_account_id,
        "tests": {}
    }

    # Test 1: Can create client
    try:
        client = NetSuiteClient(settings)
        results["tests"]["client_creation"] = "✓ Pass"
    except Exception as e:
        results["tests"]["client_creation"] = f"✗ Fail: {e}"
        return results

    # Test 2: Can generate auth headers
    try:
        test_url = f"https://{settings.ns_account_id}.suitetalk.api.netsuite.com/services/rest/record/v1/vendor"
        headers = client.auth.get_auth_headers(test_url, "GET")
        results["tests"]["header_generation"] = "✓ Pass"
        results["header_sample"] = {
            k: v[:50] + "..." if len(v) > 50 else v
            for k, v in headers.items()
        }
    except Exception as e:
        results["tests"]["header_generation"] = f"✗ Fail: {e}"
        return results

    # Test 3: Can make actual API request
    try:
        response = client.query_records("vendor", limit=1)
        results["tests"]["api_request"] = "✓ Pass"
        results["response_sample"] = {
            "count": response.get("count"),
            "hasMore": response.get("hasMore")
        }
        results["success"] = True
    except Exception as e:
        results["tests"]["api_request"] = f"✗ Fail: {e}"

    return results
```

---

## Admin Checklists for Common Errors

### 401 Unauthorized (TBA)

**Admin must check in NetSuite UI:**

**Integration Record** (Setup > Integration > Manage Integrations):
- Find integration with matching Consumer Key
- Status must be "Enabled"
- "Token-Based Authentication" must be checked
- Callback URL (if required) must be correct

**Access Token** (Setup > Users/Roles > Access Tokens):
- Find token with matching Token ID
- Status must be "Active" (not Revoked)
- Token must be associated with correct application
- Token must be for user with sufficient permissions

**Login Audit Trail** (Setup > Users/Roles > View Login Audit Trail):
- Filter by Integration
- Look for failed login attempts with specific Token ID
- Error message will indicate specific problem

### 403 Forbidden

**Role Permissions** (Setup > Users/Roles > Manage Roles):
- Find role associated with token
- Required permissions:
  - "Web Services" must be checked
  - "Lists" > "Vendors" > "View" (minimum)
  - Additional permissions for other operations

**Restrictions** (Setup > Company > Company Information):
- Check if IP restrictions are enabled
- Verify requesting IP is whitelisted

### 400 Bad Request

**Common causes:**
- Unsupported query parameters (e.g., `expandSubResources`)
- Invalid record type
- Malformed request body

**Not a NetSuite configuration issue** - Fix in application code.

---

## Credential Verification

### Verify Credentials Loaded

```python
def verify_credentials(settings):
    """Verify all required credentials are present"""
    errors = []

    # Always required
    if not settings.ns_account_id:
        errors.append("Missing NS_ACCOUNT_ID")
    if not settings.ns_consumer_key:
        errors.append("Missing NS_CONSUMER_KEY")
    if not settings.ns_consumer_secret:
        errors.append("Missing NS_CONSUMER_SECRET")

    # TBA specific
    if settings.yaml_config.application.auth_method == "tba":
        if not settings.ns_token_id:
            errors.append("Missing NS_TOKEN_ID (required for TBA)")
        if not settings.ns_token_secret:
            errors.append("Missing NS_TOKEN_SECRET (required for TBA)")

    if errors:
        print("✗ Credential verification failed:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("✓ All required credentials present")
        return True
```

### Verify Credential Format

```python
def verify_credential_format(settings):
    """Verify credentials have expected format"""
    warnings = []

    # Account ID should be numeric
    if not settings.ns_account_id.isdigit():
        warnings.append(f"Account ID '{settings.ns_account_id}' is not numeric (is this correct?)")

    # Credentials should be hex strings (typically)
    import re
    hex_pattern = re.compile(r'^[a-f0-9]+$', re.IGNORECASE)

    if not hex_pattern.match(settings.ns_consumer_key):
        warnings.append("Consumer Key doesn't look like hex string (unexpected format)")

    if settings.yaml_config.application.auth_method == "tba":
        if not hex_pattern.match(settings.ns_token_id):
            warnings.append("Token ID doesn't look like hex string (unexpected format)")

    if warnings:
        print("⚠ Credential format warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    else:
        print("✓ Credential formats look correct")

    return len(warnings) == 0
```

---

## Connection Testing

### Test Network Connectivity

```python
import httpx

def test_connectivity(account_id):
    """Test basic network connectivity to NetSuite API"""
    url = f"https://{account_id}.suitetalk.api.netsuite.com"

    try:
        response = httpx.get(url, timeout=10.0)
        # Even 401 is good - means we can reach the server
        if response.status_code in (200, 401, 403):
            print(f"✓ Can reach NetSuite API at {url}")
            return True
        else:
            print(f"⚠ Unexpected response code: {response.status_code}")
            return False
    except httpx.TimeoutException:
        print(f"✗ Connection timeout to {url}")
        print("  Check network connectivity and firewall rules")
        return False
    except Exception as e:
        print(f"✗ Connection error: {e}")
        return False
```

### Test TBA Signature Generation

```python
def test_signature_generation(settings):
    """Test OAuth 1.0 signature generation"""
    if settings.yaml_config.application.auth_method != "tba":
        print("⊘ Skipping signature test (not using TBA)")
        return True

    from vendor_analysis.netsuite.auth_tba import TBAAuthProvider

    try:
        auth = TBAAuthProvider(settings)

        test_url = "https://example.com/test?param1=value1&param2=value2"
        headers = auth.get_auth_headers(test_url, "GET")

        # Verify header structure
        auth_header = headers.get("Authorization", "")
        required_params = [
            "oauth_consumer_key",
            "oauth_token",
            "oauth_signature",
            "oauth_signature_method",
            "oauth_timestamp",
            "oauth_nonce",
            "oauth_version"
        ]

        for param in required_params:
            if param not in auth_header:
                print(f"✗ Missing {param} in Authorization header")
                return False

        print("✓ Signature generation looks correct")
        print(f"  Header sample: {auth_header[:100]}...")
        return True

    except Exception as e:
        print(f"✗ Signature generation failed: {e}")
        return False
```

---

## Actionable Error Messages

### Pattern: Specific, Actionable Errors

**WRONG:**
```python
# Generic, unhelpful
raise Exception("Authentication failed")
```

**CORRECT:**
```python
if response.status_code == 401:
    error_msg = (
        f"401 Unauthorized: NetSuite rejected authentication credentials.\n"
        f"\n"
        f"Possible causes:\n"
        f"1. Integration record is disabled\n"
        f"2. Access token is revoked\n"
        f"3. Wrong environment (Production vs Sandbox)\n"
        f"4. Credentials don't match integration setup\n"
        f"\n"
        f"Have NetSuite admin check:\n"
        f"- Setup > Integration > Manage Integrations\n"
        f"  Consumer Key: {settings.ns_consumer_key[:20]}...\n"
        f"  Status must be 'Enabled'\n"
        f"\n"
        f"- Setup > Users/Roles > Access Tokens\n"
        f"  Token ID: {settings.ns_token_id[:20]}...\n"
        f"  Status must be 'Active' (not Revoked)\n"
        f"\n"
        f"- Setup > Users/Roles > View Login Audit Trail\n"
        f"  Filter by integration to see specific error\n"
    )
    raise NetSuiteAuthError(error_msg)
```

**Benefits:**
- User knows exactly what to check
- Admin knows where to look in NetSuite UI
- Includes masked credentials for identification
- Lists specific settings to verify

---

## Related Patterns

- **Authentication Methods**: [patterns/authentication-methods.md](../patterns/authentication-methods.md)
- **OAuth Signatures**: [patterns/oauth-signatures.md](../patterns/oauth-signatures.md)
- **Error Handling**: [patterns/error-handling.md](../patterns/error-handling.md)

---

## Summary

**Key Points:**

1. **Create diagnostic scripts** that test auth without UI access
2. **Provide admin checklists** with specific NetSuite UI paths
3. **Mask credentials** for safe display (first 20 characters)
4. **Test incrementally** (config load → client creation → auth headers → API request)
5. **Actionable errors** that tell admins exactly what to check
6. **Verify connectivity** before assuming auth issues

**This pattern enables troubleshooting NetSuite integrations without requiring NetSuite UI access, saving hours of back-and-forth with admins.**

**Reference Implementation:** `/opt/ns/apps/vendor-analysis/scripts/diagnose_auth.py`
