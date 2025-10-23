# Salesforce MCP Tools Reference

Complete reference for using Salesforce MCP servers in NetSuite integrations.

## Available MCP Servers

### pdi-salesforce-sse3
Primary Salesforce MCP server with comprehensive CRUD and query capabilities.

### pdi-salesforce-proxy
Alternative Salesforce MCP server with similar functionality.

## Query Operations

### SOQL Query (pdi-salesforce-sse3)

```javascript
mcp__pdi-salesforce-sse3__query({
  soql: "SELECT Id, Name, Email FROM Contact WHERE AccountId = '...'",
  pageSize: 20,          // Optional: Records per page (default: 20, max: 50)
  pageNumber: 1,         // Optional: Page number (1-based, default: 1)
  maxFetch: 1000,        // Optional: Maximum total records to fetch
  includeDeleted: false  // Optional: Include deleted records
})
```

**Returns:**
```json
{
  "success": true,
  "records": [{
    "Id": "003...",
    "Name": "John Doe",
    "Email": "john@example.com"
  }],
  "totalSize": 150,
  "done": false,
  "nextRecordsUrl": "..."
}
```

**Use Cases:**
- Query Salesforce accounts for sync
- Find contacts by criteria
- Get opportunity data
- Custom object queries

### SOQL Query (pdi-salesforce-proxy)

```javascript
mcp__pdi-salesforce-proxy__query({
  soql: "SELECT Id, Name FROM Account WHERE Industry = 'Technology'",
  pageSize: 20,
  pageNumber: 1,
  maxFetch: 500,
  includeDeleted: false
})
```

### SOSL Search

```javascript
mcp__pdi-salesforce-sse3__search({
  sosl: "FIND {John*} IN NAME FIELDS RETURNING Contact(Id, Name, Email), Account(Id, Name)",
  pageSize: 20,
  pageNumber: 1
})
```

**Use Cases:**
- Cross-object searches
- Fuzzy name matching
- Phone number searches
- Email searches

## CRUD Operations

### Retrieve Records

```javascript
mcp__pdi-salesforce-sse3__retrieve({
  sObjectType: "Account",
  ids: ["001...", "001..."],
  fields: ["Id", "Name", "BillingStreet", "BillingCity", "BillingState", "BillingPostalCode"]
})
```

**Returns:**
```json
{
  "success": true,
  "records": [{
    "Id": "001...",
    "Name": "Acme Corp",
    "BillingStreet": "123 Main St",
    "BillingCity": "San Francisco",
    "BillingState": "CA",
    "BillingPostalCode": "94105"
  }]
}
```

### Create Record

```javascript
mcp__pdi-salesforce-sse3__create({
  sObjectType: "Contact",
  record: {
    FirstName: "Jane",
    LastName: "Smith",
    Email: "jane.smith@example.com",
    AccountId: "001...",
    Phone: "555-1234",
    Title: "VP Sales"
  }
})
```

**Returns:**
```json
{
  "success": true,
  "id": "003...",
  "errors": []
}
```

### Update Record

```javascript
mcp__pdi-salesforce-sse3__update({
  sObjectType: "Account",
  id: "001...",
  record: {
    Name: "Acme Corporation",
    Phone: "555-9876",
    Website: "https://acme.com",
    NumberOfEmployees: 500
  }
})
```

**Returns:**
```json
{
  "success": true,
  "id": "001..."
}
```

### Delete Record

```javascript
mcp__pdi-salesforce-sse3__delete({
  sObjectType: "Contact",
  id: "003..."
})
```

**Returns:**
```json
{
  "success": true,
  "id": "003..."
}
```

### Upsert Record

```javascript
mcp__pdi-salesforce-sse3__upsert({
  sObjectType: "Contact",
  externalIdField: "Email__c",
  externalId: "john@example.com",
  record: {
    FirstName: "John",
    LastName: "Doe",
    Phone: "555-4321"
  }
})
```

**Use Cases:**
- Sync without duplicate checking
- Update if exists, create if not
- Use external ID fields

## Bulk Operations

### Bulk Create

```javascript
mcp__pdi-salesforce-sse3__bulkCreate({
  sObjectType: "Contact",
  records: [
    {
      FirstName: "Alice",
      LastName: "Johnson",
      Email: "alice@example.com",
      AccountId: "001..."
    },
    {
      FirstName: "Bob",
      LastName: "Williams",
      Email: "bob@example.com",
      AccountId: "001..."
    }
  ]
})
```

**Returns:**
```json
{
  "success": true,
  "results": [
    {"success": true, "id": "003..."},
    {"success": true, "id": "003..."}
  ]
}
```

### Bulk Update

```javascript
mcp__pdi-salesforce-sse3__bulkUpdate({
  sObjectType: "Contact",
  records: [
    {
      Id: "003...",
      Phone: "555-1111"
    },
    {
      Id: "003...",
      Phone: "555-2222"
    }
  ]
})
```

**Note:** Records must include Id field.

### Bulk Delete

```javascript
mcp__pdi-salesforce-sse3__bulkDelete({
  sObjectType: "Contact",
  ids: ["003...", "003...", "003..."]
})
```

### Bulk Upsert

```javascript
mcp__pdi-salesforce-sse3__bulkUpsert({
  sObjectType: "Account",
  externalIdField: "External_ID__c",
  records: [
    {
      External_ID__c: "NS-12345",
      Name: "Customer A",
      Phone: "555-0001"
    },
    {
      External_ID__c: "NS-12346",
      Name: "Customer B",
      Phone: "555-0002"
    }
  ]
})
```

## Metadata Operations

### Describe SObject

```javascript
mcp__pdi-salesforce-sse3__describeSObject({
  sObjectType: "Account"
})
```

**Returns:**
```json
{
  "success": true,
  "name": "Account",
  "label": "Account",
  "fields": [
    {
      "name": "Id",
      "type": "id",
      "label": "Account ID",
      "length": 18,
      "unique": true
    },
    {
      "name": "Name",
      "type": "string",
      "label": "Account Name",
      "length": 255,
      "createable": true,
      "updateable": true
    }
  ]
}
```

**Use Cases:**
- Dynamic field mapping
- Validation
- UI generation
- Documentation

### Describe Multiple SObjects

```javascript
mcp__pdi-salesforce-sse3__describeSObjects({
  sObjectTypes: ["Account", "Contact", "Opportunity"]
})
```

### Describe Global

```javascript
mcp__pdi-salesforce-sse3__describeGlobal()
```

**Returns:** List of all available sObjects in the org.

### List Metadata

```javascript
mcp__pdi-salesforce-sse3__listMetadata({
  type: "CustomObject",
  folder: null,
  pageSize: 50,
  pageNumber: 1
})
```

**Metadata Types:**
- ApexClass
- ApexTrigger
- CustomObject
- CustomField
- Workflow
- ValidationRule
- Layout

## Organization Information

### Get Organization Info

```javascript
mcp__pdi-salesforce-sse3__getOrganizationInfo()
```

**Returns:**
```json
{
  "success": true,
  "organizationId": "00D...",
  "organizationName": "Acme Corporation",
  "instanceUrl": "https://acme.my.salesforce.com",
  "organizationType": "Production",
  "isSandbox": false
}
```

### Get Current User

```javascript
mcp__pdi-salesforce-sse3__getCurrentUser()
```

**Returns:**
```json
{
  "success": true,
  "userId": "005...",
  "userName": "integration@acme.com",
  "profileId": "00e...",
  "roleId": "00E..."
}
```

### Get Limits

```javascript
mcp__pdi-salesforce-sse3__getLimits()
```

**Returns:**
```json
{
  "success": true,
  "limits": {
    "DailyApiRequests": {
      "Max": 15000,
      "Remaining": 14500
    },
    "DailyBulkApiRequests": {
      "Max": 5000,
      "Remaining": 4950
    }
  }
}
```

## Integration Patterns

### Customer Sync (NS → SF)

```javascript
// In NetSuite RESTlet or Scheduled Script
define(['N/record', 'N/search'], (record, search) => {

    function syncCustomerToSalesforce(customerId) {
        // Load NetSuite customer
        const customer = record.load({
            type: record.Type.CUSTOMER,
            id: customerId
        });

        // Prepare Salesforce account data
        const sfAccount = {
            Name: customer.getValue({ fieldId: 'companyname' }),
            BillingStreet: customer.getValue({ fieldId: 'billaddr1' }),
            BillingCity: customer.getValue({ fieldId: 'billcity' }),
            BillingState: customer.getValue({ fieldId: 'billstate' }),
            BillingPostalCode: customer.getValue({ fieldId: 'billzip' }),
            BillingCountry: customer.getValue({ fieldId: 'billcountry' }),
            Phone: customer.getValue({ fieldId: 'phone' }),
            Website: customer.getValue({ fieldId: 'url' }),
            NetSuite_ID__c: customerId.toString()
        };

        // Check if account exists in Salesforce
        const sfId = customer.getValue({ fieldId: 'custentity_sf_account_id' });

        let result;
        if (sfId) {
            // Update existing
            result = mcp__pdi-salesforce-sse3__update({
                sObjectType: 'Account',
                id: sfId,
                record: sfAccount
            });
        } else {
            // Create new
            result = mcp__pdi-salesforce-sse3__create({
                sObjectType: 'Account',
                record: sfAccount
            });

            // Save Salesforce ID back to NetSuite
            if (result.success) {
                record.submitFields({
                    type: record.Type.CUSTOMER,
                    id: customerId,
                    values: {
                        custentity_sf_account_id: result.id
                    }
                });
            }
        }

        return result;
    }

    return { syncCustomerToSalesforce };
});
```

### Order Sync (SF → NS)

```javascript
// NetSuite RESTlet to receive Salesforce opportunity data
define(['N/record'], (record) => {

    function post(requestBody) {
        try {
            const sfOpportunity = JSON.parse(requestBody);

            // Query Salesforce for full opportunity details
            const sfData = mcp__pdi-salesforce-sse3__query({
                soql: `SELECT Id, Name, Amount, CloseDate, AccountId,
                       Account.NetSuite_ID__c,
                       (SELECT Product2Id, Quantity, UnitPrice FROM OpportunityLineItems)
                       FROM Opportunity WHERE Id = '${sfOpportunity.Id}'`
            });

            if (!sfData.success || sfData.records.length === 0) {
                return {
                    success: false,
                    error: 'Opportunity not found'
                };
            }

            const opp = sfData.records[0];

            // Create NetSuite Sales Order
            const salesOrder = record.create({
                type: record.Type.SALES_ORDER,
                isDynamic: true
            });

            // Set customer (from Salesforce Account)
            const nsCustomerId = opp.Account.NetSuite_ID__c;
            salesOrder.setValue({
                fieldId: 'entity',
                value: nsCustomerId
            });

            // Set order date
            salesOrder.setValue({
                fieldId: 'trandate',
                value: new Date(opp.CloseDate)
            });

            // Set custom field for Salesforce ID
            salesOrder.setValue({
                fieldId: 'custbody_sf_opportunity_id',
                value: opp.Id
            });

            // Add line items
            opp.OpportunityLineItems.records.forEach(lineItem => {
                salesOrder.selectNewLine({ sublistId: 'item' });

                // Map Salesforce product to NetSuite item
                const nsItemId = mapSfProductToNsItem(lineItem.Product2Id);

                salesOrder.setCurrentSublistValue({
                    sublistId: 'item',
                    fieldId: 'item',
                    value: nsItemId
                });

                salesOrder.setCurrentSublistValue({
                    sublistId: 'item',
                    fieldId: 'quantity',
                    value: lineItem.Quantity
                });

                salesOrder.setCurrentSublistValue({
                    sublistId: 'item',
                    fieldId: 'rate',
                    value: lineItem.UnitPrice
                });

                salesOrder.commitLine({ sublistId: 'item' });
            });

            const salesOrderId = salesOrder.save();

            // Update Salesforce opportunity with NetSuite order ID
            mcp__pdi-salesforce-sse3__update({
                sObjectType: 'Opportunity',
                id: opp.Id,
                record: {
                    NetSuite_Order_ID__c: salesOrderId.toString()
                }
            });

            return {
                success: true,
                salesOrderId: salesOrderId,
                message: 'Sales order created successfully'
            };

        } catch (e) {
            return {
                success: false,
                error: e.message
            };
        }
    }

    return { post };
});
```

### Batch Sync (Scheduled)

```javascript
// Scheduled Script for nightly sync
define(['N/search'], (search) => {

    function execute(context) {
        try {
            // Find customers modified in last 24 hours
            const customerSearch = search.create({
                type: search.Type.CUSTOMER,
                filters: [
                    ['lastmodifieddate', 'within', 'today']
                ],
                columns: ['internalid', 'companyname']
            });

            const customers = [];
            customerSearch.run().each(result => {
                customers.push({
                    id: result.getValue({ name: 'internalid' }),
                    name: result.getValue({ name: 'companyname' })
                });
                return true;
            });

            // Prepare bulk sync to Salesforce
            const accounts = customers.map(customer => ({
                NetSuite_ID__c: customer.id,
                Name: customer.name
                // ... other fields
            }));

            // Bulk upsert to Salesforce
            const result = mcp__pdi-salesforce-sse3__bulkUpsert({
                sObjectType: 'Account',
                externalIdField: 'NetSuite_ID__c',
                records: accounts
            });

            log.audit('Batch Sync Complete', {
                totalCustomers: customers.length,
                successCount: result.results.filter(r => r.success).length,
                errorCount: result.results.filter(r => !r.success).length
            });

        } catch (e) {
            log.error('Batch Sync Error', e);
        }
    }

    return { execute };
});
```

## Error Handling

### Check Response Status

```javascript
const result = mcp__pdi-salesforce-sse3__create({...});

if (result.success) {
    log.audit('Created', 'Salesforce ID: ' + result.id);
} else {
    log.error('Creation Failed', result.errors);
    // Handle errors
}
```

### Handle Bulk Operation Errors

```javascript
const bulkResult = mcp__pdi-salesforce-sse3__bulkCreate({...});

bulkResult.results.forEach((result, index) => {
    if (!result.success) {
        log.error('Bulk Create Error', {
            index: index,
            errors: result.errors
        });
        // Retry individually or log for manual review
    }
});
```

### Retry Pattern

```javascript
function retryMcpCall(mcpFunction, maxRetries = 3) {
    let attempts = 0;
    let lastError;

    while (attempts < maxRetries) {
        try {
            const result = mcpFunction();
            if (result.success) {
                return result;
            }
            lastError = result.errors;
        } catch (e) {
            lastError = e;
        }

        attempts++;
        if (attempts < maxRetries) {
            // Wait before retry (exponential backoff)
            const waitTime = Math.pow(2, attempts) * 1000;
            // In real implementation, use appropriate delay mechanism
        }
    }

    throw new Error(`Failed after ${maxRetries} attempts: ${lastError}`);
}
```

## Best Practices

### Query Optimization
- Use selective filters
- Limit fields returned
- Use pagination for large result sets
- Avoid querying in loops

### Bulk Operations
- Batch records (50-200 per batch)
- Handle partial failures
- Log all operations
- Monitor API limits

### Error Handling
- Always check success flag
- Log all errors with context
- Implement retry logic
- Handle rate limiting

### Security
- Use OAuth 2.0 when possible
- Rotate credentials regularly
- Limit field access
- Validate all inputs

### Performance
- Cache metadata when possible
- Use bulk operations for > 10 records
- Monitor API usage
- Optimize SOQL queries

## Related Documentation
- [Customer Sync Pattern](customer-sync.md)
- [Order Sync Pattern](order-sync.md)
- [Quote-to-Cash Flow](quote-to-cash.md)
- [Local KB: Authentication](/opt/ns/kb/authentication.md)
