---
name: salesforce-mcp
description: Automatically use for Salesforce tasks involving querying, inserting, updating, or analyzing CRM data via the mcp-pdi-salesforce-proxy. Trigger when the user asks to run SOQL queries (including multi-level relationships), validate or transform field values (picklists, dates, currencies), fetch or join related records, or troubleshoot Salesforce API/tooling limits, Triggers (bulleted, plain language) Query Accounts with related Contacts/Opportunities, Create/Update Account, Contact, Opportunity with valid picklists, Find fields or types for <Object> without using describeSObject/describeGlobal, Join related objects, including multi-level relationships, Handle large org schemas without describe* calls, Migrate/transform records with field normalization.
---

# Salesforce MCP

## Overview

Transform Salesforce MCP interactions from 67% discovery overhead to 90% business logic efficiency. This skill provides curated context and proven workflows based on comprehensive multi-agent testing evidence (29 operations across 3 testing tracks).

**Critical Success Patterns:**
- **Schema Discovery:** search → retrieve → query (only 1/3 agents discovered naturally)
- **Relationship Queries:** Use multi-level (2+ hops) for nested data
- **Data Manipulation:** Bulk operations with partial success handling

**Announce at start:** "I'm using Salesforce MCP Mastery to work efficiently with your Salesforce data."

---

## CRITICAL RULES (Always Follow)

### 1. NEVER Use These Tools (100% Failure Rate)
❌ **describeGlobal** - Returns 1.8M tokens (74x over 25K limit)
❌ **describeSObject** - Returns 289K-606K tokens (11-24x over limit)

**Evidence:** All 3 test agents failed 100% of attempts (5 total failures)

### 2. ALWAYS Use This Discovery Workflow
✅ **Optimal Sequence:** search → retrieve → query

**Why:** Agent 3 used this pattern = 100% success rate, 71% business logic efficiency
**Contrast:** Agent 1 trial-and-error = 62.5% success rate, 25% efficiency

### 3. ALWAYS Validate Empty Results
When queries return 0 results, validate before reporting:
```soql
-- Remove filters to confirm object has data
SELECT Id FROM Object LIMIT 5

-- Test filter field exists
SELECT FilterField FROM Object WHERE FilterField != null LIMIT 5
```

**Why:** 10 empty result situations across agents - distinguish "no data" from "wrong query"

---

## Phase 1: Request Analysis

**Determine workflow based on what you have:**

### Scenario A: You Have a Record Name/Text
→ Start with **search (SOSL)**

### Scenario B: You Have a Record ID
→ Start with **retrieve**

### Scenario C: You Have No Specific Record
→ Start with **query (SOQL)** using context below

---

## Phase 2: Schema Discovery

### Core Object Quick Reference

#### **ChangeRequest__c** (Custom Object)

**Essential Fields (Always Safe to Query):**
- `Id` (String) - Salesforce record ID
- `Name` (String) - CR number (format: CR#####)
- `Status__c` (Picklist) - See status values below
- `Priority__c` (Picklist) - Values: "1 - Critical", "2 - Urgent", "3 - Important", "4 - Minor"
- `Subject__c` (String) - Short description
- `Description__c` (Text) - Detailed description
- `Customer_Impact__c` (Text) - Impact description
- `Account__c` (Lookup → Account) - Related customer account
- `Product__c` (String) - Product name
- `Version__c` (String) - Version affected
- `CreatedDate`, `LastModifiedDate`, `OwnerId` - System fields

**Status__c Values (14 total):**
- **Open States:** "Open" (111 records), "New" (409), "In Progress" (675), "In Review" (297)
- **Pending States:** "Schedule Pending" (740), "Funding Pending" (251), "Waiting on Customer" (44), "Under Consideration" (3)
- **Closed States:** "Completed" (11,093), "Released" (43,491), "Withdrawn" (18,024)
- **Other:** "Added To Backlog" (2,435), "Research" (175), "Uncommitted Idea" (2), "Dormant" (varies)

**Relationships:**
- `Account__c` → Account (lookup, use in WHERE and SELECT)
- `FeedItem.ParentId` → ChangeRequest__c.Id (Chatter comments)
- `ContentDocumentLink.LinkedEntityId` → ChangeRequest__c.Id (file attachments)

**Common Queries:**
```soql
-- Find open CRs for an account
SELECT Id, Name, Status__c, Priority__c, Subject__c, CreatedDate
FROM ChangeRequest__c
WHERE Account__c = '001...' AND Status__c IN ('Open', 'New', 'In Progress')
ORDER BY Priority__c, CreatedDate DESC

-- Discover all status values with counts
SELECT Status__c, COUNT(Id) cnt
FROM ChangeRequest__c
GROUP BY Status__c
ORDER BY cnt DESC

-- Find high priority CRs created in last 30 days
SELECT Id, Name, Status__c, Subject__c, Account__c
FROM ChangeRequest__c
WHERE Priority__c IN ('1 - Critical', '2 - Urgent')
  AND CreatedDate >= LAST_N_DAYS:30
```

---

#### **Case** (Standard Object)

**Essential Fields:**
- `Id`, `CaseNumber` (String) - Auto-generated number
- `Subject` (String), `Description` (Text)
- `Status` (Picklist) - Values: "New", "Open", "Escalated", "Waiting on Customer", "Waiting on Vendor", "Closed", "Dormant"
- `Priority` (Picklist) - Values vary by org
- `AccountId` (Lookup → Account) - Related account
- `OwnerId` (Lookup → User)
- `IsClosed` (Boolean) - True if Status = "Closed"
- `CreatedDate`, `LastModifiedDate`

**Relationships:**
- `AccountId` → Account
  - ⚠️ **IMPORTANT:** `Account.Name` works in WHERE but may NOT populate in SELECT
  - **Workaround:** Use `AccountId` in SELECT, filter by `Account.Name` in WHERE
- `CaseComment.ParentId` → Case.Id (legacy comments)
- `FeedItem.ParentId` → Case.Id (Chatter feed)
- `CaseHistory.CaseId` → Case.Id (field history)

**Common Queries:**
```soql
-- Find open cases for account (using relationship filter)
SELECT Id, CaseNumber, Subject, Status, Priority, AccountId
FROM Case
WHERE Account.Name LIKE '%Acme%' AND IsClosed = false
ORDER BY Priority DESC, CreatedDate DESC

-- Cases created in Q4 2024
SELECT Id, CaseNumber, Subject, Status, CreatedDate
FROM Case
WHERE CreatedDate >= 2024-10-01T00:00:00Z
  AND CreatedDate <= 2024-12-31T23:59:59Z

-- Cases with text match
SELECT Id, CaseNumber, Subject, Status
FROM Case
WHERE Subject LIKE '%integration error%'
```

---

#### **Account** (Standard Object)

**Essential Fields:**
- `Id`, `Name` (String)
- `ParentId` (Lookup → Account) - Account hierarchy
- `AccountNumber` (String)
- `Type` (Picklist) - e.g., "Customer", "Prospect", "Partner"
- `Industry` (Picklist)
- `BillingAddress`, `ShippingAddress` (Compound fields)
- `Phone`, `Website`
- `OwnerId` (Lookup → User)
- `CreatedDate`, `LastModifiedDate`

**Relationships:**
- `ParentId` → Account (self-referential hierarchy)
- `Opportunity.AccountId` → Account.Id (child relationship)
- `Contract.AccountId` → Account.Id (child relationship)
- `Case.AccountId` → Account.Id (child relationship)
- `Contact.AccountId` → Account.Id (child relationship)

**Common Queries:**
```soql
-- Find account by name (use SOSL instead for better results)
FIND {PDI Technologies} IN ALL FIELDS RETURNING Account(Id, Name)

-- Account Hierarchy Discovery (3-step validation)
-- Step 1: Check if account HAS a parent
SELECT Id, Name, ParentId
FROM Account
WHERE Id = '001...'
-- If ParentId not null, account has a parent

-- Step 2: Find child accounts
SELECT Id, Name, ParentId
FROM Account
WHERE ParentId = '001...'
-- Empty result = no children (standalone account)

-- Step 3: Multi-level parent traversal
SELECT Id, Name, ParentId, Parent.Name, Parent.ParentId
FROM Account
WHERE Id = '001...'
-- Check both directions to understand position in hierarchy

-- Find all opportunities for account
SELECT Id, Name, Amount, StageName, CloseDate
FROM Opportunity
WHERE AccountId = '001...'
ORDER BY CloseDate DESC
```

---

#### **Standard Object Patterns**

**Chatter Feed Items:**
```soql
-- Get comments/posts on any object
SELECT Id, ParentId, Body, CreatedDate, CreatedBy.Name, Type
FROM FeedItem
WHERE ParentId = '<any-object-id>'
ORDER BY CreatedDate DESC
```

**File Attachments:**
```soql
-- Find files attached to any object
SELECT Id, LinkedEntityId, ContentDocumentId
FROM ContentDocumentLink
WHERE LinkedEntityId = '<any-object-id>'

-- Get file details (requires join)
SELECT Id, Title, FileType, ContentSize, CreatedDate
FROM ContentDocument
WHERE Id = '<content-document-id>'
```

**Field History (if enabled):**
```soql
-- Track field changes over time
SELECT Id, Field, OldValue, NewValue, CreatedDate, CreatedBy.Name
FROM <Object>History  -- e.g., CaseHistory, AccountHistory
WHERE <Object>Id = '<record-id>'
ORDER BY CreatedDate DESC
```

---

## Phase 3: Tool Selection Guide

### Tool Comparison Matrix

| Tool | Use When | Returns | Success Rate | Evidence |
|------|----------|---------|--------------|----------|
| **search (SOSL)** | Finding by name/text | Multiple matches with Id, Name | 100% | 3/3 agents successful |
| **retrieve** | Schema discovery, getting all fields | ALL fields for 1 record | 100% | 2/2 uses, but only 4% of attempts |
| **query (SOQL)** | Filtering, aggregating, relationships | Filtered result set | 100% | 33/33 executions (some empty) |
| **describeSObject** | NEVER | Token limit error | 0% | 3/3 failed (289K-606K tokens) |
| **describeGlobal** | NEVER | Token limit error | 0% | 2/2 failed (1.8M tokens) |

### Optimal Workflows

#### Workflow A: "I have a name, need details"
```
1. search (SOSL) → Find record(s) by name → Get Id
2. retrieve → Get ALL fields for that Id → See complete schema
3. query (SOQL) → Filter/aggregate based on discovered fields
```

**Example:**
```sosl
-- Step 1: Find account
FIND {PDI Technologies} IN ALL FIELDS RETURNING Account(Id, Name)
-- Result: Id = 001Us00000GsN5LIAV

-- Step 2: Get complete schema
retrieve(sObjectType: "Account", ids: ["001Us00000GsN5LIAV"])
-- Result: 300+ fields including ParentId, Industry, Type, etc.

-- Step 3: Query related data
SELECT Id, Name, ParentId FROM Account WHERE ParentId = '001Us00000GsN5LIAV'
```

**Success Evidence:** Agent 3 used this pattern = 100% success rate, only 7 attempts total

---

#### Workflow B: "I need to filter/aggregate data"
```
1. Use context above to identify object name and fields
2. query (SOQL) → Build filtered query
3. If empty results → Validate (see Phase 4)
```

**Example:**
```soql
-- Step 1: Know from context that ChangeRequest__c has Status__c field
-- Step 2: Query directly
SELECT Id, Name, Status__c, Priority__c, CreatedDate
FROM ChangeRequest__c
WHERE Status__c IN ('Open', 'New', 'In Progress')
  AND Account__c = '001...'
ORDER BY Priority__c, CreatedDate DESC
```

---

#### Workflow C: "I need to discover picklist values"
```
Use aggregation to see all values and distribution:
SELECT PicklistField, COUNT(Id) cnt
FROM Object
GROUP BY PicklistField
ORDER BY cnt DESC
```

**Example (discovered by Agent 1):**
```soql
SELECT Status__c, COUNT(Id) cnt
FROM ChangeRequest__c
GROUP BY Status__c
ORDER BY cnt DESC
-- Returns: 14 status values with record counts
```

**Why this works:** Shows all possible values + distribution for confidence

---

## Phase 4: Query Construction Patterns

### Date Filtering
```soql
-- Specific date range
WHERE CreatedDate >= 2024-10-01T00:00:00Z
  AND CreatedDate <= 2024-12-31T23:59:59Z

-- Relative date range (preferred for dynamic queries)
WHERE CreatedDate >= LAST_N_DAYS:30
WHERE CreatedDate = TODAY
WHERE CreatedDate = THIS_WEEK
WHERE CreatedDate = THIS_QUARTER
```

### Text Matching
```soql
-- Case-insensitive partial match (% = wildcard)
WHERE Subject LIKE '%error%'          -- Contains "error"
WHERE Name LIKE 'Acme%'               -- Starts with "Acme"
WHERE Name LIKE '%Corporation'        -- Ends with "Corporation"
```

### Relationship Queries

#### ⚠️ CRITICAL: Single-Level vs Multi-Level Relationships

**SINGLE-LEVEL RELATIONSHIPS (DO NOT WORK in SELECT):**
```soql
-- ❌ Parent-to-child subqueries return NO data
SELECT Id, Name, (SELECT Id, FirstName FROM Contacts) FROM Account

-- ❌ Child-to-parent lookups return NO data
SELECT Id, LastName, Account.Name FROM Contact

-- ✅ BUT they WORK PERFECTLY in WHERE clauses
SELECT Id, LastName, AccountId FROM Contact WHERE Account.Name LIKE 'PDI%'
```

**MULTI-LEVEL RELATIONSHIPS (WORK PERFECTLY - 2+ Hops):**
```soql
-- ✅ Junction/child objects with 2+ relationship hops return FULL nested data
SELECT Id, Quantity, UnitPrice,
       Opportunity.Name,
       Opportunity.Account.Name,
       Opportunity.Account.Industry
FROM OpportunityLineItem
WHERE Opportunity.Account.Name LIKE '%Oil%'

-- Result includes complete nested structure:
{
  "Id": "00k...",
  "Quantity": 100,
  "Opportunity": {
    "Name": "Abbott Oil - Forms Sale",
    "Account": {
      "Name": "Abbott Oil Company, Inc.",
      "Industry": "Energy"
    }
  }
}
```

**BREAKTHROUGH PATTERN:**
Query from junction/child objects to get multi-level relationship data:
- OpportunityLineItem → Opportunity → Account ✅
- OpportunityContactRole → Opportunity → Account ✅
- TaskRelation → Task → Who/What ✅
- AccountContactRelation → Account + Contact ✅

**Workarounds for Single-Level Relationships:**
```soql
-- Option 1: Use WHERE filtering only
SELECT Id, CaseNumber, Subject, AccountId
FROM Case
WHERE Account.Name LIKE 'PDI%'

-- Option 2: Query from the other direction
SELECT Id, Name, (SELECT Id FROM Cases) FROM Account WHERE Id = '001...'
-- Note: Subquery may not return data, use separate query instead

-- Option 3: Make separate queries
-- Step 1: Get AccountId
SELECT AccountId FROM Case WHERE Id = '500...'
-- Step 2: Query Account
SELECT Id, Name FROM Account WHERE Id = '001...'
```

**Standard Relationship Fields (These DO work):**
```soql
-- System relationship fields always work
SELECT Id, CreatedBy.Name, Owner.Name, LastModifiedBy.Name FROM Case
```

### Aggregation for Discovery
```soql
-- Find all picklist values with counts
SELECT Status__c, COUNT(Id) cnt
FROM Case
GROUP BY Status__c
ORDER BY COUNT(Id) DESC  -- MUST use full expression, not alias

-- Find all priority levels
SELECT Priority__c, COUNT(Id) cnt
FROM ChangeRequest__c
WHERE Priority__c != null
GROUP BY Priority__c
ORDER BY COUNT(Id) DESC
```

**⚠️ CRITICAL: Aggregation ORDER BY Syntax**
```soql
-- ❌ FAILS: Cannot use alias in ORDER BY
SELECT Status__c, COUNT(Id) cnt
FROM Object
GROUP BY Status__c
ORDER BY cnt DESC  -- ERROR: "No such column 'cnt'"

-- ✅ CORRECT: Use full aggregate expression
SELECT Status__c, COUNT(Id) cnt
FROM Object
GROUP BY Status__c
ORDER BY COUNT(Id) DESC
```

### Validation Queries (Empty Results)
```soql
-- When query returns 0 results, validate:

-- 1. Does object have any data?
SELECT Id FROM Object LIMIT 5

-- 2. Does filter field exist and have values?
SELECT FilterField FROM Object WHERE FilterField != null LIMIT 5

-- 3. Validate multiple fields in single query
SELECT FilterField1__c, FilterField2__c, FilterField3__c
FROM Object
WHERE FilterField1__c != null
   OR FilterField2__c != null
   OR FilterField3__c != null
LIMIT 1

-- 4. Remove filters one by one to narrow down issue
```

### Defensive LIMIT Clauses
**Pattern:** Always add LIMIT to exploratory queries to prevent timeouts and excessive API usage.

```soql
-- ✅ Discovery queries (sample data)
SELECT Id, Name FROM Object LIMIT 5

-- ✅ Subqueries (limit related records)
SELECT Id, Name,
       (SELECT Id, Subject FROM Cases LIMIT 3)
FROM Account

-- ✅ Schema discovery (prevent overwhelming results)
SELECT QualifiedApiName FROM FieldDefinition
WHERE EntityDefinitionId = 'Account'
LIMIT 100

-- ✅ Aggregations generally don't need LIMIT (return summary)
SELECT Status__c, COUNT(Id) FROM Case GROUP BY Status__c
```

### Schema Discovery with Metadata Objects

**When describe* tools fail (large orgs), use metadata object queries:**

```soql
-- Discover objects in the org (instead of describeGlobal)
SELECT QualifiedApiName, Label, PluralLabel
FROM EntityDefinition
WHERE IsCustomizable = true
ORDER BY QualifiedApiName
LIMIT 100

-- Discover fields on an object (instead of describeSObject)
SELECT QualifiedApiName, DataType, Label
FROM FieldDefinition
WHERE EntityDefinitionId = 'Account'
  AND IsActive = true
ORDER BY QualifiedApiName
LIMIT 100

-- Discover picklist values for a field
SELECT QualifiedApiName, Label, MasterLabel
FROM PicklistValueInfo
WHERE EntityParticleId = 'Account.Type'
ORDER BY Label
```

**Pattern-Based Custom Field Discovery (when IsCustom unavailable):**
```soql
-- ❌ May FAIL in some orgs:
SELECT QualifiedApiName, DataType, Label
FROM FieldDefinition
WHERE EntityDefinitionId = 'Opportunity'
  AND IsCustom = true  -- Field may not exist

-- ✅ WORKAROUND - Use naming convention:
SELECT QualifiedApiName, DataType, Label
FROM FieldDefinition
WHERE EntityDefinitionId = 'Opportunity'
  AND QualifiedApiName LIKE '%__c'  -- All custom fields end with __c
ORDER BY QualifiedApiName
LIMIT 50
```

**Benefits:**
- Works in large orgs (returns manageable result sets)
- Supports LIMIT clauses for pagination
- Allows filtering to specific objects/fields
- Much faster than describe* tools

**Limitations:**
- Cannot use all SOQL features (no complex WHERE clauses)
- Field names vary between metadata objects
- Pagination metadata may be unreliable

---

## Phase 5: Data Manipulation Patterns

### Create Operations
```json
// Basic create - always returns new record ID
{
  "tool": "mcp__mcp-pdi-salesforce-proxy__create",
  "parameters": {
    "sObjectType": "Account",
    "record": {
      "Name": "New Company",
      "Type": "Prospect",
      "Industry": "Technology"
    }
  }
}
// Response: {"id": "001...", "success": true, "errors": []}
```

### Update Operations
```json
// Update requires record ID + fields to change
{
  "tool": "mcp__mcp-pdi-salesforce-proxy__update",
  "parameters": {
    "sObjectType": "Account",
    "id": "001...",
    "record": {
      "Type": "Customer",
      "NumberOfEmployees": 500
    }
  }
}
```

**⚠️ CRITICAL: Picklist Validation**
- State/Country picklists require EXACT values from the org's configuration
- "CA" ≠ "California", "USA" ≠ "United States"
- Use GROUP BY to discover valid values first
- Validation errors are specific: "There's a problem with this state"

### Bulk Operations
```json
// Bulk create - process multiple records in one call
{
  "tool": "mcp__mcp-pdi-salesforce-proxy__bulkCreate",
  "parameters": {
    "sObjectType": "Account",
    "records": [
      {"Name": "Company 1", "Type": "Prospect"},
      {"Name": "Company 2", "Type": "Customer"}
    ]
  }
}
// Returns array with individual success/failure per record
```

**Key Pattern: Partial Success**
- Bulk operations can succeed for some records and fail for others
- Each record gets individual success/failure in response
- Failed records include detailed error messages
- No automatic rollback - handle partial failures explicitly

### Upsert Operations
```json
// Upsert requires configured External ID field
{
  "tool": "mcp__mcp-pdi-salesforce-proxy__upsert",
  "parameters": {
    "sObjectType": "Account",
    "externalIdField": "External_ID__c",  // Must be configured as External ID
    "externalId": "EXT-12345",
    "record": {
      "Name": "Updated Name"
    }
  }
}
```

**⚠️ CRITICAL: External ID Configuration**
- Fields must be explicitly configured as "External ID" in Salesforce
- Standard fields (AccountNumber, Email) are NOT external IDs by default
- Cannot use standard Id field for upsert
- Error: "Provided external ID field does not exist or is not accessible"

### Delete Operations
```json
// Simple delete by ID
{
  "tool": "mcp__mcp-pdi-salesforce-proxy__delete",
  "parameters": {
    "sObjectType": "Account",
    "id": "001..."
  }
}
```

**⚠️ CRITICAL: Referential Integrity**
- Cannot delete records with dependent relationships
- Common blockers: Entitlements, Opportunities, Cases, Contacts
- Error messages specify what's blocking deletion
- Must remove dependencies before deleting parent records

---

## Phase 6: Common Anti-Patterns (Evidence-Based)

### ❌ Anti-Pattern 1: Starting with describe* Tools
**What Agent 1 did:** Tried describeGlobal → describeSObject → 2 failures, forced 18 attempts of field guessing
**What Agent 3 did:** search → retrieve → 2 attempts, complete schema, 100% success
**Impact:** 91% efficiency difference

### ❌ Anti-Pattern 2: Using FIELDS(ALL) for Schema Discovery
```soql
SELECT FIELDS(ALL) FROM ChangeRequest__c LIMIT 1
```
**Problem:** Only returns 13 fields instead of 80+ fields
**Better:** Use `retrieve` tool to get ALL fields

### ❌ Anti-Pattern 3: Testing Fields One by One
**What Agent 1 did:** 8 attempts testing individual field names (Customer__c, Business_Justification__c, etc.)
**Better:** Use `retrieve` once to see all 80+ fields instantly

### ❌ Anti-Pattern 4: Assuming Empty Results = Wrong Query
**What happened:** Agents got 10 empty result situations
**Problem:** Couldn't distinguish "no data" from "syntax error"
**Solution:** Always validate with LIMIT 5 query (see Phase 4)

### ❌ Anti-Pattern 5: Guessing Object Names Without Context
**What Agent 1 tried:** Project__c, ChangeRequestComment__c, Affected_Customer__c
**Result:** All 3 failed (objects don't exist)
**Better:** Use context above to know which objects exist

### ❌ Anti-Pattern 6: Using Single-Level Relationships in SELECT
```soql
-- ❌ WRONG: Expecting relationship data in response
SELECT Id, Account.Name, Account.Industry FROM Contact

-- ✅ CORRECT: Use multi-level query or WHERE clause
SELECT Id, Opportunity.Name, Opportunity.Account.Name
FROM OpportunityLineItem
WHERE Opportunity.Account.Industry = 'Technology'
```
**Problem:** Single-level relationship fields are silently omitted from responses
**Solution:** Use multi-level queries (2+ hops) or filter with WHERE clause

### ❌ Anti-Pattern 7: Assuming Standard Field Values for Picklists
```json
// ❌ WRONG: Assuming standard abbreviations
{
  "BillingState": "CA",
  "BillingCountry": "USA"
}

// ✅ CORRECT: Query for exact values first
SELECT BillingCountry, BillingState, COUNT(Id)
FROM Account
WHERE BillingCountry != null
GROUP BY BillingCountry, BillingState
```
**Problem:** Orgs may require exact picklist values like "United States" not "USA"
**Solution:** Always discover valid values before updating address fields

### ❌ Anti-Pattern 8: Attempting Upsert Without External ID Configuration
```json
// ❌ WRONG: Using fields that aren't configured as External IDs
{
  "externalIdField": "AccountNumber",  // Not configured as External ID
  "externalId": "ACC-12345"
}
```
**Problem:** Standard fields are not External IDs by default
**Solution:** Query FieldDefinition to discover configured External ID fields, or use create/update

---

## Phase 6: Field Naming Conventions

### Standard Fields (No Suffix)
- Universal across all objects
- Examples: `Id`, `Name`, `CreatedDate`, `CreatedById`, `LastModifiedDate`, `LastModifiedById`, `OwnerId`, `SystemModstamp`, `IsDeleted`

### Custom Fields (End with __c)
- Vary by organization
- Examples: `Status__c`, `Priority__c`, `Subject__c`, `Account__c`

### Relationship Fields
- Standard lookups: Usually end with `Id` (e.g., `AccountId`, `OwnerId`)
- Custom lookups: End with `__c` (e.g., `Account__c`)
- Parent relationships: Use `ParentId` for hierarchies

### Relationship Traversal (End with __r for custom, dot notation for standard)
- Standard: `Account.Name`, `Owner.Name`, `CreatedBy.Name`
- Custom: `Account__r.Name` (though behavior varies)

---

## Phase 7: Testing Evidence & Validation

### Latest Testing Results (Run2 - October 2025)

**Three-Agent Comprehensive Testing:**
- **29 total operations** across relationship queries, data manipulation, and schema discovery
- **65.5% initial success rate** → **85% final success rate** (after adaptations)
- **3 breakthrough discoveries** that fundamentally changed best practices

**Agent Performance:**

| Agent | Focus Area | Operations | Success Rate | Key Discovery |
|-------|-----------|-----------|--------------|---------------|
| Agent 1 | Relationship Queries | 10 | 100% execution | Multi-level relationships work |
| Agent 2 | Data Manipulation | 13 | 69% → 100% | Bulk partial success pattern |
| Agent 3 | Schema Discovery | 6 | 50% → 100% | FieldDefinition queries |

**Critical Findings:**
1. **Multi-level relationships** (2+ hops) return full nested JSON structures
2. **WHERE clause filtering** works perfectly for single-level relationships
3. **FieldDefinition queries** enable schema discovery in large orgs (vs 0% success with describe*)
4. **State/Country picklists** require exact org-configured values
5. **External ID fields** must be explicitly configured for upsert operations

### Breakthrough Discovery: Multi-Level Relationships

**Query 7 from Agent 1 Testing:**
```soql
SELECT Id, Quantity, UnitPrice,
       Opportunity.Name,
       Opportunity.Account.Name
FROM OpportunityLineItem
WHERE Opportunity.Account.Name LIKE '%Oil%'
```

**Result:** Full nested structure returned (unlike single-level queries):
```json
{
  "Id": "00k1N00000kUpwUQAS",
  "Quantity": 100,
  "UnitPrice": 50.00,
  "Opportunity": {
    "attributes": {...},
    "Name": "Abbott Oil - Forms Sale",
    "Account": {
      "attributes": {...},
      "Name": "Abbott Oil Company, Inc."
    }
  }
}
```

**Impact:** Changed from "relationships don't work" to "use multi-level queries for relationship data"

---

## Phase 8: Execution Checklist

Before running any query, verify:

1. ✅ **Tool Selection**
   - [ ] If finding by name → using `search` (SOSL)?
   - [ ] If need schema → using `retrieve` after finding Id?
   - [ ] If filtering data → using `query` (SOQL)?
   - [ ] NOT using describe* tools?

2. ✅ **Field Names**
   - [ ] Using fields from context above?
   - [ ] Following naming conventions (__c for custom)?
   - [ ] Not guessing field names?

3. ✅ **Relationships**
   - [ ] Using AccountId (not Account.Name) in SELECT?
   - [ ] Using relationship fields in WHERE only?
   - [ ] Expecting relationship fields might not populate?

4. ✅ **Empty Results Plan**
   - [ ] Ready to validate with LIMIT 5 query?
   - [ ] Will test without filters if needed?

---

## Remember

### 💡 Core Principles (Updated with Run2 Findings)
1. **Discovery overhead is the enemy** - Use context to minimize trial-and-error
2. **retrieve is your friend** - Most effective schema discovery tool
3. **Multi-level relationships work** - Query from junction objects for nested data (2+ hops)
4. **Single-level relationships need workarounds** - Use WHERE clauses or separate queries
5. **Empty results are valid** - Don't assume error, validate instead
6. **Aggregation discovers values** - GROUP BY shows picklist options
7. **Bulk operations can partially succeed** - Always check individual results
8. **External IDs must be configured** - Cannot use arbitrary fields for upsert

### 📊 Success Metrics (Evidence-Based)

**Original Testing (2024):**
- **Baseline (no context):** 67% discovery overhead, 75.6% success rate, 5 avg queries/request
- **With skill v1:** 10% discovery overhead, 95% success rate, 1.5 avg queries/request
- **Efficiency gain:** 85% reduction in wasted attempts

**Run2 Comprehensive Testing (October 2025):**
- **Initial success rate:** 65.5% (19/29 operations)
- **Final success rate:** 85% (after adaptations)
- **Learning curve:** 50% → 75% → 85% across three phases
- **Breakthrough discoveries:** 3 (multi-level relationships, FieldDefinition, bulk patterns)
- **Documentation:** 4,269 lines across 4 comprehensive reports

### 🎯 When to Use This Skill
- **ALWAYS** when working with Salesforce data
- At the start of any Salesforce request (proactive context loading)
- When you encounter describe* tool failures
- When queries return unexpected empty results
- When unsure which tool to use

---

## Related Skills

**If dealing with complex data transformations:**
- Data analysis and aggregation techniques

**If encountering unexpected behaviors:**
- Systematic debugging approaches

**If building reports/dashboards:**
- Data visualization and summary patterns

---

**Use this skill proactively for every Salesforce interaction.**

**End of Skill**



