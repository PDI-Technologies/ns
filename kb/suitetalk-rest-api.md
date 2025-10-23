# SuiteTalk REST API

## Base URLs
- Production: `https://{account_id}.suitetalk.api.netsuite.com`
- Format: `https://{account_id}.suitetalk.api.netsuite.com/services/rest/record/v1/{record_type}`

## Endpoints

### Record Operations
- **GET** `/services/rest/record/v1/{recordType}/{id}` - Retrieve record by ID
  - Ref: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4567627367
- **POST** `/services/rest/record/v1/{recordType}` - Create new record
  - Ref: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4567627367
- **PUT** `/services/rest/record/v1/{recordType}/{id}` - Update existing record
  - HTTP Method: PUT
- **PATCH** `/services/rest/record/v1/{recordType}/{id}` - Partial update
  - HTTP Method: PATCH
- **DELETE** `/services/rest/record/v1/{recordType}/{id}` - Delete record
  - HTTP Method: DELETE

### Query Operations
- **POST** `/services/rest/query/v1/suiteql` - Execute SuiteQL query
  - Body: `{"q": "SELECT field1, field2 FROM recordType WHERE condition"}`

## Request/Response Format

### Request Headers
```http
Content-Type: application/json
Accept: application/json
Authorization: OAuth realm="{account_id}", oauth_consumer_key="{key}", ...
```

### GET Example (Retrieve Customer)
```javascript
// Endpoint
GET /services/rest/record/v1/customer/{customerId}

// Response (200 OK)
{
  "id": "123",
  "companyName": "Example Corp",
  "email": "contact@example.com",
  // ... additional fields
}
```

### POST Example (Create Record)
```json
{
  "companyName": "Example Corp",
  "email": "contact@example.com"
}
```

### SuiteQL Example
```json
POST /services/rest/query/v1/suiteql
{
  "q": "SELECT id, tranid, total, entity FROM transaction WHERE type = 'VendBill' AND datecreated >= ADD_MONTHS(SYSDATE, -1)"
}
```

## Authentication
- **Method**: OAuth 1.0a (HMAC-SHA256)
- **Required Credentials**:
  - Consumer Key
  - Consumer Secret
  - Token Key
  - Token Secret
- **Signature Method**: HMAC-SHA256
- Auto-included via `https.requestSuiteTalkRest()` in SuiteScript 2.x

## Rate Limits
- Concurrency limits apply per account
- Governed by NetSuite governance framework
- View limits: `getAccountGovernanceInfo` operation
- Integration governance tracking available

## Supported Record Types

### Standard Records
- `customer` - Customer records
- `contact` - Contact records
- `salesOrder` - Sales orders
- `invoice` - Invoices (requires SuiteTax for tax operations)
- `cashSale` - Cash sales (requires SuiteTax for tax operations)
- `vendorBill` - Vendor bills
- `inventoryItem` - Inventory items
- `employee` - Employee records
- `account` - Chart of accounts
- `transaction` - Transaction records

### Custom Records
- `customrecord_{customrecord_id}` - Custom record types
- Format: `/services/rest/record/v1/customrecord_{id}`

### Record Availability
- As of 2024.1 release: All standard record types available via REST
- 2025.2: REST Web Services Supported Records documentation
- Ref: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_161487969808

## CRUD Operations Mapping

| Operation | HTTP Method | SOAP Equivalent |
|-----------|-------------|-----------------|
| Create | POST | add, addList |
| Read | GET | get, getList |
| Update | PUT/PATCH | update, updateList |
| Delete | DELETE | delete, deleteList |
| Upsert | POST (special) | upsert, upsertList |

## Error Codes

### HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

### NetSuite-Specific Error Response
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Error description"
  }
}
```

## SOAP Web Services Operations (Reference)
Available operations via SOAP (for comparison):
- add, addList
- attach, detach
- delete, deleteList
- get, getList
- update, updateList
- upsert, upsertList
- search, searchMoreWithId
- initialize, initializeList
- getDataCenterUrls
- checkAsyncStatus, getAsyncResult

Ref: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N3523074

## Data Center URLs
Use `getDataCenterUrls` SOAP operation to dynamically retrieve:
- REST endpoint URL
- SOAP endpoint URL
- File cabinet URL

## Important Notes
- REST web services do not support legacy tax features
- SuiteTax feature required for taxation operations
- REST API enforces NetSuite business rules and permissions
- Triggers associated scripts and workflows
- Use REST API Browser for detailed field exploration

## Official Documentation URLs
- **SuiteTalk Web Services**: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N3203557
- **SuiteTalk REST Web Services API Guide**: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N3748057
- **https.requestSuiteTalkRest Function**: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4567627367
- **SOAP Operations Overview**: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N3523074
- **getDataCenterUrls Operation**: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N3494684
- **Cash Sale Record**: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_161487969808
- **Invoice Record**: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_161488248489
- **N/https Module Methods**: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4619219272
- **Send HTTPS Request**: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4418229131
