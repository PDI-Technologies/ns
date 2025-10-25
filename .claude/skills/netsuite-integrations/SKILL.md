---
name: netsuite-integrations
description: Builds integrations between NetSuite and external systems including Salesforce (using pdi-salesforce-sse3 MCP), databases (MSSQL, PostgreSQL via mcp), RESTlet APIs, SuiteTalk REST/SOAP, and third-party services. Handles bi-directional data sync, authentication, error handling, and real-time/scheduled integration patterns. Use when connecting NetSuite to CRM, databases, payment gateways, or external applications.
---

# NetSuite Integrations

Comprehensive skill for building integrations between NetSuite and external systems using RESTlets, SuiteTalk, MCP tools, and third-party APIs.

## Quick Start

### Common Integration Patterns
- **Build RESTlet API**: See [restlet-apis/api-design.md](restlet-apis/api-design.md)
- **Salesforce Integration**: See [salesforce/customer-sync.md](salesforce/customer-sync.md)
- **Database Integration**: See [databases/export-to-db.md](databases/export-to-db.md)
- **Use SuiteTalk**: See [suitetalk/rest-api.md](suitetalk/rest-api.md)
- **Call External APIs**: See [external-apis/http-requests.md](external-apis/http-requests.md)

### Integration Decision Matrix

| Scenario | Method | Direction | Best For |
|----------|--------|-----------|----------|
| External system calls NS | RESTlet | Inbound | Real-time API access, Mobile apps |
| NS calls external system | N/https | Outbound | Webhooks, API calls, Notifications |
| External bulk operations | SuiteTalk REST | Inbound | Batch imports, Data warehouse sync |
| NS bulk data export | Scheduled Script + N/https | Outbound | Nightly exports, Reporting |
| Salesforce sync | RESTlet + MCP tools | Bi-directional | CRM integration, Quote-to-cash |
| Database sync | Scheduled Script + SQL MCP | Bi-directional | Data warehouse, Analytics |

### Authentication Method Selection

| Scenario | Method | Timeline | Complexity | Credentials |
|----------|--------|----------|------------|-------------|
| New integration (2025+) | OAuth 2.0 | Long-term | Medium | 2 (Consumer Key/Secret) |
| Existing integration | TBA | Until Feb 2025 | High | 4 (Consumer + Token) |
| Migration in progress | Multi-method | Transition period | Medium | Both sets |
| Testing/Sandbox | Either | Any | Varies | Match production |

**Key points:**
- OAuth 2.0 required for all new integrations as of February 2025
- TBA deprecated but still functional through February 2025
- Use multi-method factory pattern for gradual migration
- See [authentication/tba.md](authentication/tba.md) and [authentication/oauth2.md](authentication/oauth2.md)

### Data Fetching Strategy Selection

| Data Volume | Strategy | API Calls | Time Estimate | Complexity |
|-------------|----------|-----------|---------------|------------|
| < 1000 records | Full sync, sequential | ~1000 | 5-10 min | Low |
| 1000-10000 records | Incremental + batch | 100-10000 | 1-75 min | Medium |
| 10000+ records | Incremental + parallel + cache | 100-1000 | < 10 min | High |
| Real-time needs | Webhooks + RESTlets | Per event | Real-time | Medium |

**Key patterns:**
- **2-step fetch REQUIRED:** Query returns IDs only, must fetch full records individually
- **Incremental sync:** Only fetch changed records (99% API call reduction)
- **Parallel fetching:** 5-10x faster but requires rate limit management
- **Caching:** Avoid redundant fetches (95% reduction for static data)
- See [suitetalk/rest-api.md](suitetalk/rest-api.md) and [patterns/data-fetching.md](patterns/data-fetching.md)

## Knowledge Base Resources

### Local KB Documentation
- **RESTlets Guide**: [/opt/ns/kb/restlets.md](/opt/ns/kb/restlets.md)
- **SuiteTalk REST API**: [/opt/ns/kb/suitetalk-rest-api.md](/opt/ns/kb/suitetalk-rest-api.md)
- **Authentication**: [/opt/ns/kb/authentication.md](/opt/ns/kb/authentication.md)
- **SuiteScript Modules**: [/opt/ns/kb/suitescript-modules.md](/opt/ns/kb/suitescript-modules.md) (N/http, N/https)
- **Third-Party SDKs**: [/opt/ns/kb/third-party-sdks.md](/opt/ns/kb/third-party-sdks.md)

### Archon Vector KB
For NetSuite integration documentation:

```javascript
mcp__archon__rag_search_knowledge_base(
  query="SuiteTalk REST API integration",
  match_count=5
)

mcp__archon__rag_search_code_examples(
  query="RESTlet authentication OAuth",
  match_count=3
)
```

## RESTlet APIs (Inbound Integration)

### API Design
See [restlet-apis/api-design.md](restlet-apis/api-design.md)

**Topics:**
- RESTful design principles
- URL structure and routing
- Request/response formats (JSON, XML)
- Versioning strategies
- Rate limiting
- Documentation

### Authentication
See [restlet-apis/authentication.md](restlet-apis/authentication.md)

**Methods:**
- OAuth 2.0 (recommended)
- Token-Based Authentication (TBA)
- NLAuth (deprecated)
- API key patterns
- JWT tokens

### CRUD Patterns
See [restlet-apis/crud-patterns.md](restlet-apis/crud-patterns.md)

**Operations:**
- GET - Retrieve records
- POST - Create records
- PUT - Update records
- DELETE - Delete records
- PATCH - Partial updates
- Batch operations

### Error Handling
See [restlet-apis/error-handling.md](restlet-apis/error-handling.md)

**Patterns:**
- HTTP status codes
- Error response format
- Validation errors
- Business logic errors
- System errors
- Retry mechanisms

## Salesforce Integration

### Overview
NetSuite ↔ Salesforce bi-directional sync using RESTlets and Salesforce MCP tools.

**Available MCP Servers:**
- `pdi-salesforce-sse3` - Salesforce operations via MCP
- `pdi-salesforce-proxy` - Alternative Salesforce MCP

**MCP Tools:**
- See [salesforce/mcp-tools.md](salesforce/mcp-tools.md)

### Customer Synchronization
See [salesforce/customer-sync.md](salesforce/customer-sync.md)

**Pattern:** Salesforce Account ↔ NetSuite Customer

**Sync Fields:**
- Company name
- Billing address
- Contact information
- Custom fields mapping

**MCP Operations:**
```javascript
// Query Salesforce accounts
mcp__pdi-salesforce-sse3__query(
  soql="SELECT Id, Name, BillingStreet, BillingCity FROM Account WHERE LastModifiedDate > YESTERDAY"
)

// Create NetSuite customer from Salesforce account
// Update Salesforce with NetSuite customer ID
```

### Order Synchronization
See [salesforce/order-sync.md](salesforce/order-sync.md)

**Pattern:** Salesforce Opportunity ↔ NetSuite Sales Order

**Workflow:**
1. Salesforce Opportunity marked "Closed Won"
2. Trigger sends data to NetSuite RESTlet
3. NetSuite creates Sales Order
4. NetSuite returns order ID
5. Update Salesforce Opportunity with order reference

### Quote-to-Cash
See [salesforce/quote-to-cash.md](salesforce/quote-to-cash.md)

**Complete Flow:**
1. **Quote** - Salesforce CPQ
2. **Order** - NetSuite Sales Order
3. **Fulfillment** - NetSuite Item Fulfillment
4. **Invoice** - NetSuite Invoice
5. **Payment** - NetSuite Customer Payment
6. **Revenue** - NetSuite Revenue Recognition

### Salesforce MCP Tools
See [salesforce/mcp-tools.md](salesforce/mcp-tools.md)

**Query Operations:**
```javascript
// SOQL queries
mcp__pdi-salesforce-sse3__query(soql="...", pageSize=20)
mcp__pdi-salesforce-proxy__query(soql="...", includeDeleted=false)

// SOSL searches
mcp__pdi-salesforce-sse3__search(sosl="FIND {searchTerm}...")
```

**CRUD Operations:**
```javascript
// Create
mcp__pdi-salesforce-sse3__create(sObjectType="Account", record={Name: "..."})

// Update
mcp__pdi-salesforce-sse3__update(sObjectType="Account", id="...", record={...})

// Delete
mcp__pdi-salesforce-sse3__delete(sObjectType="Account", id="...")

// Retrieve
mcp__pdi-salesforce-sse3__retrieve(sObjectType="Account", ids=["..."], fields=["Name", "..."])
```

**Bulk Operations:**
```javascript
// Bulk create
mcp__pdi-salesforce-sse3__bulkCreate(sObjectType="Contact", records=[{...}, {...}])

// Bulk update
mcp__pdi-salesforce-sse3__bulkUpdate(sObjectType="Contact", records=[{Id: "...", ...}])
```

## Database Integration

### Export to Database
See [databases/export-to-db.md](databases/export-to-db.md)

**Pattern:** NetSuite → External Database (Data Warehouse)

**Methods:**
- Scheduled Script with N/search + MCP SQL
- Map/Reduce for large datasets
- SuiteTalk REST API + External ETL

**Use Cases:**
- Financial reporting database
- Analytics/BI systems
- Data warehousing
- Backup/archive

### Import from Database
See [databases/import-from-db.md](databases/import-from-db.md)

**Pattern:** External Database → NetSuite

**Methods:**
- RESTlet API receiving database data
- Scheduled Script pulling from database via MCP
- CSV import from database export

**Use Cases:**
- Product catalog sync
- Pricing updates
- Master data management

### Scheduled Synchronization
See [databases/scheduled-sync.md](databases/scheduled-sync.md)

**Patterns:**
- Nightly full sync
- Incremental sync (changes only)
- Real-time CDC (Change Data Capture)

### Database MCP Tools
See [databases/mcp-tools.md](databases/mcp-tools.md)

**MSSQL Operations:**
```javascript
// Execute SQL query
mcp__mssql__query(
  query="SELECT * FROM customers WHERE modified_date > @date",
  host="db.server.com",
  database="analytics",
  username="ns_integration",
  password="***",
  dbType="mssql"
)

// Manage sessions
mcp__mssql__manage_session(action="create", sessionId="ns-sync")
```

**PostgreSQL Operations:**
```javascript
mcp__mssql__query(
  query="INSERT INTO ns_customers (id, name, email) VALUES ($1, $2, $3)",
  host="postgres.server.com",
  port=5432,
  database="datawarehouse",
  username="ns_user",
  password="***",
  dbType="postgres",
  sslMode="require"
)
```

**MySQL Operations:**
```javascript
mcp__mssql__query(
  query="UPDATE products SET netsuite_id = ? WHERE sku = ?",
  host="mysql.server.com",
  port=3306,
  database="ecommerce",
  username="integration",
  password="***",
  dbType="mysql",
  timezone="+00:00"
)
```

## SuiteTalk (NetSuite REST API)

### REST API Basics
See [suitetalk/rest-api.md](suitetalk/rest-api.md)

**Base URL:**
```
https://{accountId}.suitetalk.api.netsuite.com/services/rest/record/v1
```

**Authentication:**
- OAuth 2.0
- Token-Based Authentication (TBA)

**Operations:**
- GET /record/{recordType}/{id}
- POST /record/{recordType}
- PATCH /record/{recordType}/{id}
- DELETE /record/{recordType}/{id}

### SOAP API
See [suitetalk/soap-api.md](suitetalk/soap-api.md)

**Use Cases:**
- Legacy integrations
- Operations not available in REST
- Bulk operations
- Complex search queries

### Bulk Operations
See [suitetalk/bulk-operations.md](suitetalk/bulk-operations.md)

**Methods:**
- **SuiteQL** - Use for fetching 10+ records
- REST API batching
- SOAP getList/addList/updateList
- CSV imports

## External APIs (Outbound Integration)

### HTTP Requests
See [external-apis/http-requests.md](external-apis/http-requests.md)

**SuiteScript Modules:**
- N/https (server-side)
- N/http (client-side)

**Patterns:**
- GET requests
- POST requests with JSON
- Authentication headers
- Error handling
- Retry logic

**Example:**
```javascript
define(['N/https', 'N/log'], (https, log) => {
    function callExternalAPI() {
        const response = https.post({
            url: 'https://api.external.com/endpoint',
            headers: {
                'Authorization': 'Bearer ' + getAuthToken(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                customer_id: customerId,
                order_total: total
            })
        });

        if (response.code === 200) {
            const data = JSON.parse(response.body);
            return data;
        } else {
            throw new Error('API call failed: ' + response.code);
        }
    }
});
```

### Webhook Handlers
See [external-apis/webhook-handlers.md](external-apis/webhook-handlers.md)

**Pattern:** External System → NetSuite RESTlet (Webhook endpoint)

**Use Cases:**
- Shopify order webhooks
- Stripe payment webhooks
- Salesforce platform events
- Custom system notifications

## Authentication Patterns

### OAuth 2.0
See [authentication/oauth2.md](authentication/oauth2.md)

**Flow:**
1. Registration in NetSuite
2. Authorization code exchange
3. Access token generation
4. Token refresh

**Best For:**
- Third-party applications
- User-delegated access
- Modern integrations

### Token-Based Authentication (TBA)
See [authentication/tba.md](authentication/tba.md)

**Setup:**
1. Create integration record
2. Generate token ID and secret
3. Use in HMAC signatures
4. Rotate periodically

**Best For:**
- Server-to-server
- Scheduled jobs
- Internal integrations

### API Keys
See [authentication/api-keys.md](authentication/api-keys.md)

**Custom Pattern:**
- Generate unique keys in NetSuite
- Store in custom record
- Validate in RESTlet
- Rate limit by key

## Integration Patterns

### Real-Time Sync
**Characteristics:**
- Event-driven (webhooks, triggers)
- Immediate data transfer
- RESTlet endpoints
- Low latency

**Use Cases:**
- Order processing
- Inventory updates
- Payment processing
- Critical notifications

### Scheduled Sync
**Characteristics:**
- Time-based (Scheduled Scripts)
- Batch processing
- Configurable frequency
- Efficient for large volumes

**Use Cases:**
- Nightly data exports
- Daily reconciliation
- Weekly reporting
- Monthly aggregations

### Hybrid Sync
**Characteristics:**
- Real-time for critical data
- Scheduled for bulk data
- Error queue for retries
- Monitoring and alerts

**Use Cases:**
- E-commerce integration
- ERP synchronization
- Multi-system orchestration

## Error Handling

### Retry Mechanisms
See [authentication/retry-patterns.md](authentication/retry-patterns.md)

**Strategies:**
- Exponential backoff
- Circuit breaker
- Dead letter queue
- Manual intervention queue

### Logging and Monitoring
See [authentication/logging.md](authentication/logging.md)

**Practices:**
- Log all integration attempts
- Track success/failure rates
- Monitor latency
- Alert on failures
- Audit trail compliance

## Code Examples

### Complete RESTlet Integration
See [examples/restlet-integration.md](examples/restlet-integration.md)

**Includes:**
- Authentication
- CRUD operations
- Error handling
- Response formatting
- Testing

### Salesforce Bi-Directional Sync
See [examples/salesforce-bidirectional.md](examples/salesforce-bidirectional.md)

**Includes:**
- Customer sync
- Order sync
- Real-time webhooks
- Scheduled batch sync
- Conflict resolution

### Database Export Pipeline
See [examples/database-export.md](examples/database-export.md)

**Includes:**
- Scheduled Script
- Large dataset handling
- SQL MCP operations
- Error recovery
- Performance optimization

## Reference Documentation

### Complete File Index

**RESTlet APIs:**
- [restlet-apis/api-design.md](restlet-apis/api-design.md)
- [restlet-apis/authentication.md](restlet-apis/authentication.md)
- [restlet-apis/crud-patterns.md](restlet-apis/crud-patterns.md)
- [restlet-apis/error-handling.md](restlet-apis/error-handling.md)

**Salesforce Integration:**
- [salesforce/customer-sync.md](salesforce/customer-sync.md)
- [salesforce/order-sync.md](salesforce/order-sync.md)
- [salesforce/quote-to-cash.md](salesforce/quote-to-cash.md)
- [salesforce/mcp-tools.md](salesforce/mcp-tools.md)

**Database Integration:**
- [databases/export-to-db.md](databases/export-to-db.md)
- [databases/import-from-db.md](databases/import-from-db.md)
- [databases/scheduled-sync.md](databases/scheduled-sync.md)
- [databases/mcp-tools.md](databases/mcp-tools.md)

**SuiteTalk:**
- [suitetalk/rest-api.md](suitetalk/rest-api.md)
- [suitetalk/soap-api.md](suitetalk/soap-api.md)
- [suitetalk/bulk-operations.md](suitetalk/bulk-operations.md)

**External APIs:**
- [external-apis/http-requests.md](external-apis/http-requests.md)
- [external-apis/webhook-handlers.md](external-apis/webhook-handlers.md)

**Authentication:**
- [authentication/oauth2.md](authentication/oauth2.md)
- [authentication/tba.md](authentication/tba.md)
- [authentication/api-keys.md](authentication/api-keys.md)
- [authentication/retry-patterns.md](authentication/retry-patterns.md)
- [authentication/logging.md](authentication/logging.md)

**Examples:**
- [examples/restlet-integration.md](examples/restlet-integration.md)
- [examples/salesforce-bidirectional.md](examples/salesforce-bidirectional.md)
- [examples/database-export.md](examples/database-export.md)
