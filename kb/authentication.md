# NetSuite Authentication

## OAuth 2.0 (Recommended 2025+)

### Setup Steps
1. Navigate to Setup > Integration > Manage Integrations > New - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_161942084079
2. Provide integration name and description
3. Enable state as "Enabled"
4. On Authentication tab, configure OAuth 2.0 settings
5. Generate SSL certificate and upload public key to NetSuite
6. Save and note Consumer Key and Consumer Secret
7. Configure callback/redirect URI (for authorization code grant flow)

### Token Request (Client Credentials Flow)
```http
POST /rest/oauth2/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&client_id={CONSUMER_KEY}&client_secret={CONSUMER_SECRET}
```
https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N250541

### Response Format
```json
{
  "access_token": "YOUR_ACCESS_TOKEN",
  "token_type": "bearer",
  "expires_in": 3600
}
```
https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N250541

### Token Revocation
```http
POST /rest/oauth2/revoke
Content-Type: application/x-www-form-urlencoded

token={ACCESS_TOKEN}
```
https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N250541

### Headers Format
```
Authorization: Bearer {access_token}
```

### Token Lifespan
3600 seconds (1 hour) - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N250541

### Authentication Flows
- **Authorization Code Grant Flow**: Interactive user delegation with consent via login redirect
- **Client Credentials Flow**: Machine-to-machine integration without user interaction

### Certificate-Based Authentication
- Requires SSL certificate generation
- Upload public key to NetSuite Integration Record
- Only machines with correct private key can access APIs
- Enhanced security for CI/CD pipelines and automated deployments

## Token-Based Authentication (TBA)

### Deprecation Notice
**DEPRECATED as of February 2025** - OAuth 2.0 is now mandatory for all NetSuite integrations
- 2024.2 release: TBA removed for SuiteCloud SDK in CI environments
- February 2025: TBA and OAuth 1.0 functionality completely removed from SuiteCloud SDK
- Migration to OAuth 2.0 required immediately

### Setup Steps (Legacy)
1. Navigate to Setup > Integration > Manage Integrations > New - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_161942084079
2. Provide Name and Description for integration
3. Enable state as "Enabled"
4. On Authentication tab, check "Token-based Authentication" box
5. Save to generate Consumer Key and Consumer Secret - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_161942084079
6. Enable Token-based Authentication feature - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4830376716
7. Set Up Token-based Authentication Roles - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4247337262
8. Assign Users to Token-based Authentication Roles - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4247337262
9. Create token and token secret for user - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4636903496

### Components
- **Consumer Key**: Generated from Integration Record, identifies the application
- **Consumer Secret**: Generated from Integration Record, used to sign requests
- **Token ID**: User-specific token generated for authentication
- **Token Secret**: Secret paired with Token ID for signature generation

### Signature Generation (OAuth 1.0 Specification)
```
Authorization: OAuth realm="{accountId}",
oauth_consumer_key="...",
oauth_token="...",
oauth_signature_method="HMAC-SHA256",
oauth_timestamp="...",
oauth_nonce="...",
oauth_version="1.0",
oauth_signature="..."
```
https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4624454249

### TokenPassport (SOAP Web Services)
```xml
<TokenPassport>
  <account>1234567</account>
  <consumerKey>your_consumer_key</consumerKey>
  <token>your_token</token>
  <nonce>random_string</nonce>
  <timestamp>1678886400</timestamp>
  <signature>your_signature</signature>
</TokenPassport>
```
https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N3452954

### Environment-Specific Tokens
Tokens are NOT copied between environments:
- Production account tokens don't transfer to Release Preview or Sandbox
- Must create new tokens in each environment
- Sandbox refresh requires new token generation
https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4254801119

### Supported Services
- RESTlets - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4624454249
- SOAP Web Services - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4381113277
- SuiteAnalytics Connect - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_163240582544

### Tracking Integration Activity
Integration records at Setup > Integration > Manage Integrations track:
- RESTlet calls authenticated by consumer key
- Application blocking capability
- Consumer key/secret regeneration
- RESTlets execution log
- Integration record ownership and change tracking
https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4567507062

## NLAuth (Deprecated)

### Status
**DEPRECATED** - Slated for complete deprecation, replaced by OAuth 2.0

### Format
Basic username/password authentication for NetSuite web services

### Security Concerns
- Low security compared to token-based methods
- Password expiration issues
- Risk of credential compromise
- Not recommended for new integrations

## Comparison Table

| Method | Use Case | Security | Deprecated | Status 2025+ |
|--------|----------|----------|------------|--------------|
| OAuth 2.0 | Modern apps, CI/CD, machine-to-machine | High (certificate-based) | No | **Required** |
| TBA (OAuth 1.0) | Server-to-server (legacy) | Medium | **Yes (Feb 2025)** | Removed |
| NLAuth | Legacy web services | Low | Yes (2021.1+) | Not supported |

## Official Documentation URLs

### OAuth 2.0
- REST Token Services: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N250541
- OAuth 2.0 Overview: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4247337262
- Integration Record Setup: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_161942084079

### Token-Based Authentication (Deprecated)
- TBA Overview: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4247337262
- Enable TBA Feature: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4830376716
- TBA Setup Steps: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4247337262
- RESTlet TBA Authentication: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4624454249
- TBA Setup Requirements: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4636903496
- TokenPassport Complex Type: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N3452954
- SOAP Web Services TBA: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4381113277
- TBA for RESTlets: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4254801119
- Integration Management: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_161942084079
- Track RESTlet Calls: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4567507062
- SuiteAnalytics Connect TBA: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_163240582544

### RESTlet Authentication
- RESTlet Authentication Overview: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4623992425
- External RESTlet Authentication: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4624454249

### Integration Records
- Create Integration Records: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4247337262
- Manage Integrations: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_161942084079
