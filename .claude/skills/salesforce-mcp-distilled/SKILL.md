---
name: salesforce-mcp-distilled
description: Optimized Salesforce MCP operations via mcp-pdi-salesforce-proxy. Use for SOQL/SOSL queries, record CRUD, schema discovery, relationship traversal, and picklist validation. Handles ChangeRequest__c, Case, Account with multi-level relationships, bulk operations, and metadata queries. Avoids token-limit failures on describe* tools.
---

# Salesforce MCP - Distilled

## CRITICAL: Never Use

❌ **describeGlobal** - Returns 1.8M tokens (74x limit)
❌ **describeSObject** - Returns 289K-606K tokens (11-24x limit)

## Optimal Workflow

```
search (SOSL) → retrieve → query (SOQL)
```

## Core Objects Quick Reference

### ChangeRequest__c (Custom)
**Fields:** Id, Name (CR#####), Status__c, Priority__c, Subject__c, Description__c, Customer_Impact__c, Account__c (lookup), Product__c, Version__c
**Status Values:** Released (43K), Withdrawn (18K), Completed (11K), Added To Backlog (2.4K), Schedule Pending (740), In Progress (675), New (409), In Review (297), Funding Pending (251), Research (175), Open (111), Waiting on Customer (44), Under Consideration (3), Uncommitted Idea (2)
**Priority Values:** "1 - Critical", "2 - Urgent", "3 - Important", "4 - Minor"

### Case (Standard)
**Fields:** Id, CaseNumber, Subject, Description, Status, Priority, AccountId, OwnerId, IsClosed, CreatedDate
**Status Values:** New, Open, Escalated, Waiting on Customer, Waiting on Vendor, Closed, Dormant
**Relationships:** Account.Name (WHERE only), CaseComment.ParentId, FeedItem.ParentId

### Account (Standard)
**Fields:** Id, Name, ParentId, AccountNumber, Type, Industry, BillingAddress, Phone, Website, OwnerId
**Relationships:** ParentId (self-hierarchy), Opportunity.AccountId, Case.AccountId, Contact.AccountId

## Tool Selection

| Tool | Use Case | Returns |
|------|----------|---------|
| **search** (SOSL) | Find by name/text | Multiple matches with Id, Name |
| **retrieve** | Get ALL fields for schema | Complete field list for 1 record |
| **query** (SOQL) | Filter, aggregate, join | Filtered result set |

## Query Patterns

### Discovery
```soql
-- Find record by name
FIND {PDI Technologies} IN ALL FIELDS RETURNING Account(Id, Name)

-- Get complete schema
retrieve(sObjectType: "Account", ids: ["001..."])

-- Discover picklist values
SELECT Status__c, COUNT(Id) cnt
FROM ChangeRequest__c
GROUP BY Status__c
ORDER BY COUNT(Id) DESC  -- Must use full expression, not alias
```

### Relationships

**Single-Level (WHERE only, not SELECT):**
```soql
-- ❌ Account.Name won't populate in SELECT
SELECT Id, CaseNumber, Account.Name FROM Case WHERE AccountId = '...'

-- ✅ Use in WHERE, return Id in SELECT
SELECT Id, CaseNumber, AccountId
FROM Case
WHERE Account.Name LIKE 'PDI%'
```

**Multi-Level (2+ hops - works in SELECT):**
```soql
-- ✅ Nested JSON structure returned
SELECT Id, Quantity,
       Opportunity.Name,
       Opportunity.Account.Name
FROM OpportunityLineItem
WHERE Opportunity.Account.Name LIKE '%Oil%'
```

### Date Filtering
```soql
WHERE CreatedDate >= LAST_N_DAYS:30
WHERE CreatedDate = TODAY
WHERE CreatedDate >= 2024-10-01T00:00:00Z
  AND CreatedDate <= 2024-12-31T23:59:59Z
```

### Text Matching
```soql
WHERE Subject LIKE '%error%'        -- Contains
WHERE Name LIKE 'Acme%'             -- Starts with
WHERE Name LIKE '%Corporation'      -- Ends with
```

### Aggregation (ORDER BY syntax)
```soql
-- ❌ FAILS
SELECT Status__c, COUNT(Id) cnt
FROM Object
GROUP BY Status__c
ORDER BY cnt DESC  -- Error: no such column

-- ✅ CORRECT
SELECT Status__c, COUNT(Id) cnt
FROM Object
GROUP BY Status__c
ORDER BY COUNT(Id) DESC
```

### Account Hierarchy
```soql
-- Check parent
SELECT Id, ParentId FROM Account WHERE Id = '001...'

-- Find children
SELECT Id, Name, ParentId FROM Account WHERE ParentId = '001...'

-- Multi-level parent
SELECT Id, ParentId, Parent.Name, Parent.ParentId
FROM Account WHERE Id = '001...'
```

### Validation (Empty Results)
```soql
-- Verify data exists
SELECT Id FROM Object LIMIT 5

-- Validate field exists
SELECT FilterField FROM Object WHERE FilterField != null LIMIT 5

-- Multi-field validation
SELECT Field1__c, Field2__c, Field3__c
FROM Object
WHERE Field1__c != null OR Field2__c != null OR Field3__c != null
LIMIT 1
```

## Schema Discovery Alternatives

### FieldDefinition (when describe* fails)
```soql
-- Discover fields
SELECT QualifiedApiName, DataType, Label
FROM FieldDefinition
WHERE EntityDefinitionId = 'Account'
  AND IsActive = true
LIMIT 100

-- Custom fields (if IsCustom unavailable)
SELECT QualifiedApiName, DataType, Label
FROM FieldDefinition
WHERE EntityDefinitionId = 'Opportunity'
  AND QualifiedApiName LIKE '%__c'
LIMIT 50
```

### EntityDefinition
```soql
SELECT QualifiedApiName, Label, PluralLabel
FROM EntityDefinition
WHERE IsCustomizable = true
LIMIT 100
```

### PicklistValueInfo
```soql
SELECT QualifiedApiName, Label, MasterLabel
FROM PicklistValueInfo
WHERE EntityParticleId = 'Account.Type'
```

## Data Manipulation

### Create
```json
{
  "tool": "create",
  "sObjectType": "Account",
  "record": {"Name": "New Company", "Type": "Prospect"}
}
```

### Update
```json
{
  "tool": "update",
  "sObjectType": "Account",
  "id": "001...",
  "record": {"Type": "Customer"}
}
```

### Bulk Operations
```json
{
  "tool": "bulkCreate",
  "sObjectType": "Account",
  "records": [
    {"Name": "Company 1"},
    {"Name": "Company 2"}
  ]
}
```
**Note:** Returns individual success/failure per record. No automatic rollback.

### Upsert
```json
{
  "tool": "upsert",
  "sObjectType": "Account",
  "externalIdField": "External_ID__c",  // Must be configured as External ID
  "externalId": "EXT-12345",
  "record": {"Name": "Updated Name"}
}
```
**Requirement:** Field must be configured as External ID in Salesforce. Standard fields are NOT External IDs by default.

## Anti-Patterns

❌ Single-level relationships in SELECT (use WHERE instead)
❌ Guessing field names (use retrieve first)
❌ ORDER BY with aggregate aliases (use full expression)
❌ Missing LIMIT on discovery queries (add LIMIT 5-100)
❌ Assuming picklist values (use GROUP BY discovery)
❌ Using describe* in large orgs (use FieldDefinition)
❌ Standard field names for External IDs (must be configured)

## Field Naming Conventions

**Standard:** Id, Name, CreatedDate, CreatedById, LastModifiedDate, OwnerId, IsDeleted, SystemModstamp
**Custom:** End with `__c` (Status__c, Priority__c, Account__c)
**Lookups:**
- Standard: End with `Id` (AccountId, OwnerId)
- Custom: End with `__c` (Account__c)
**Relationships:** Use `__r` for custom, dot notation for standard

## Defensive LIMIT Pattern

Always add LIMIT to:
- Discovery queries: `LIMIT 5`
- Schema queries: `LIMIT 100`
- Subqueries: `LIMIT 3`

Not needed for:
- Aggregations (GROUP BY)
- Targeted queries with specific WHERE clauses

## Common Patterns

### Chatter Feed
```soql
SELECT Id, ParentId, Body, CreatedDate, CreatedBy.Name, Type
FROM FeedItem
WHERE ParentId = '<object-id>'
ORDER BY CreatedDate DESC
```

### File Attachments
```soql
SELECT Id, LinkedEntityId, ContentDocumentId
FROM ContentDocumentLink
WHERE LinkedEntityId = '<object-id>'
```

### Field History
```soql
SELECT Id, Field, OldValue, NewValue, CreatedDate, CreatedBy.Name
FROM CaseHistory
WHERE CaseId = '<record-id>'
ORDER BY CreatedDate DESC
```

## System Fields (Always Available)

- CreatedBy.Name
- Owner.Name
- LastModifiedBy.Name
- RecordType.Name (if record types enabled)

## When Empty Results

1. Validate object has data: `SELECT Id FROM Object LIMIT 5`
2. Validate filter field: `SELECT Field FROM Object WHERE Field != null LIMIT 5`
3. Remove filters incrementally
4. Check field name spelling (__c suffix for custom)
5. Verify picklist values with GROUP BY

## State/Country Picklists

⚠️ Require exact org-configured values
- Discover with: `SELECT BillingCountry, BillingState, COUNT(Id) FROM Account WHERE BillingCountry != null GROUP BY BillingCountry, BillingState`
- "CA" ≠ "California", "USA" ≠ "United States"

## Deletion Rules

Cannot delete records with:
- Active Entitlements
- Related Opportunities
- Related Cases
- Related Contacts

Remove dependencies first, then delete parent.
