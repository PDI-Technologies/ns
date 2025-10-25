# Custom Record Type Design

Design patterns for NetSuite custom record types to extend data model beyond standard records.

## Overview

Custom Record Types enable modeling business-specific entities not covered by NetSuite's standard records (Customer, Vendor, Item, etc.).

**Common Use Cases:**
- Assets and equipment tracking
- Project tracking with custom attributes
- Contract lifecycle management
- Compliance and regulatory data
- Custom approval workflows
- Third-party system integrations

**Design Considerations:**
- Record hierarchy and parent-child relationships
- Field types and validation rules
- User permissions and access controls
- Search and reporting requirements
- Performance and scalability

## Custom Record Structure

### Basic Record Definition

Custom records include:
- **Record Type ID** - Internal identifier (e.g., `customrecord_asset`)
- **Record Name** - Display name
- **Fields** - Custom fields attached to record
- **Sublists** - Child line items (if enabled)
- **Parent Records** - Hierarchical relationships

**Example: Asset Management Record**

```
Record Type: customrecord_asset
Fields:
  - custrecord_asset_id (Text, unique identifier)
  - custrecord_asset_name (Text)
  - custrecord_asset_type (List: Equipment, Vehicle, Furniture)
  - custrecord_purchase_date (Date)
  - custrecord_purchase_cost (Currency)
  - custrecord_depreciation_method (List: Straight-Line, Declining Balance)
  - custrecord_assigned_employee (List/Record: Employee)
  - custrecord_location (List/Record: Location)
  - custrecord_status (List: In Use, Available, Retired)
```

### Field Types

**Available Field Types:**
- **Free-Form Text** - Short text (up to 4,000 characters)
- **Text Area** - Long text
- **Check Box** - Boolean
- **Integer** - Whole numbers
- **Decimal** - Floating point
- **Currency** - Monetary values
- **Date** - Date only
- **DateTime** - Date with time
- **List/Record** - Select from standard or custom records
- **Multiple Select** - Multi-select list
- **Document** - File attachment
- **Image** - Image upload
- **Email Address** - Email validation
- **Phone** - Phone number
- **URL** - Web address

## Accessing Custom Records via SuiteScript

### Creating Records

```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType UserEventScript
 */

define(['N/record'], (record) => {

    function createAssetRecord(assetData) {
        const assetRecord = record.create({
            type: 'customrecord_asset',
            isDynamic: true
        });

        assetRecord.setValue({
            fieldId: 'name',  // Record name field
            value: assetData.assetName
        });

        assetRecord.setValue({
            fieldId: 'custrecord_asset_id',
            value: assetData.assetId
        });

        assetRecord.setValue({
            fieldId: 'custrecord_asset_type',
            value: assetData.assetType  // Internal ID of list value
        });

        assetRecord.setValue({
            fieldId: 'custrecord_purchase_date',
            value: new Date(assetData.purchaseDate)
        });

        assetRecord.setValue({
            fieldId: 'custrecord_purchase_cost',
            value: assetData.cost
        });

        assetRecord.setValue({
            fieldId: 'custrecord_assigned_employee',
            value: assetData.employeeId
        });

        const recordId = assetRecord.save();
        return recordId;
    }

    return {
        createAssetRecord: createAssetRecord
    };
});
```

### Loading and Updating Records

```javascript
function updateAssetStatus(assetId, newStatus) {
    const assetRecord = record.load({
        type: 'customrecord_asset',
        id: assetId
    });

    assetRecord.setValue({
        fieldId: 'custrecord_status',
        value: newStatus
    });

    assetRecord.save();
}

function assignAssetToEmployee(assetId, employeeId) {
    record.submitFields({
        type: 'customrecord_asset',
        id: assetId,
        values: {
            custrecord_assigned_employee: employeeId,
            custrecord_status: STATUS_IN_USE
        }
    });
}
```

### Searching Custom Records

```javascript
function findAvailableAssets(assetType) {
    const assetSearch = search.create({
        type: 'customrecord_asset',
        filters: [
            ['custrecord_status', 'is', STATUS_AVAILABLE],
            'AND',
            ['custrecord_asset_type', 'is', assetType]
        ],
        columns: [
            'name',
            'custrecord_asset_id',
            'custrecord_purchase_date',
            'custrecord_location'
        ]
    });

    const results = [];
    assetSearch.run().each((result) => {
        results.push({
            id: result.id,
            name: result.getValue({ name: 'name' }),
            assetId: result.getValue({ name: 'custrecord_asset_id' }),
            purchaseDate: result.getValue({ name: 'custrecord_purchase_date' }),
            location: result.getText({ name: 'custrecord_location' })
        });
        return true;  // Continue iteration
    });

    return results;
}
```

## Parent-Child Relationships

### Hierarchical Records

Custom records can have parent-child hierarchies.

**Example: Project → Task → Subtask**

```javascript
// Parent: Project
const project = record.create({
    type: 'customrecord_project'
});
project.setValue({ fieldId: 'name', value: 'Website Redesign' });
const projectId = project.save();

// Child: Task
const task = record.create({
    type: 'customrecord_task'
});
task.setValue({ fieldId: 'name', value: 'Design Homepage' });
task.setValue({
    fieldId: 'custrecord_parent_project',  // Parent field
    value: projectId
});
const taskId = task.save();

// Grandchild: Subtask
const subtask = record.create({
    type: 'customrecord_subtask'
});
subtask.setValue({ fieldId: 'name', value: 'Create Wireframes' });
subtask.setValue({
    fieldId: 'custrecord_parent_task',
    value: taskId
});
subtask.save();
```

### Querying Hierarchies

```javascript
function getProjectTasks(projectId) {
    return search.create({
        type: 'customrecord_task',
        filters: [
            ['custrecord_parent_project', 'is', projectId]
        ],
        columns: ['name', 'custrecord_status', 'custrecord_due_date']
    }).run().getRange({ start: 0, end: 1000 });
}
```

## Sublist (Line-Level) Data

Custom records can have sublists for one-to-many relationships.

**Example: Contract with Line Items**

```javascript
function createContractWithLineItems(contractData) {
    const contract = record.create({
        type: 'customrecord_contract',
        isDynamic: true
    });

    contract.setValue({ fieldId: 'name', value: contractData.contractName });
    contract.setValue({ fieldId: 'custrecord_customer', value: contractData.customerId });

    // Add line items
    for (const item of contractData.lineItems) {
        contract.selectNewLine({ sublistId: 'recmachcustrecord_contract_line_parent' });

        contract.setCurrentSublistValue({
            sublistId: 'recmachcustrecord_contract_line_parent',
            fieldId: 'custrecord_item',
            value: item.itemId
        });

        contract.setCurrentSublistValue({
            sublistId: 'recmachcustrecord_contract_line_parent',
            fieldId: 'custrecord_quantity',
            value: item.quantity
        });

        contract.setCurrentSublistValue({
            sublistId: 'recmachcustrecord_contract_line_parent',
            fieldId: 'custrecord_rate',
            value: item.rate
        });

        contract.commitLine({ sublistId: 'recmachcustrecord_contract_line_parent' });
    }

    return contract.save();
}
```

## Data Validation

### Field Validation

```javascript
function validateAssetData(context) {
    const newRecord = context.newRecord;

    // Validate purchase cost is positive
    const cost = newRecord.getValue({ fieldId: 'custrecord_purchase_cost' });
    if (cost && cost <= 0) {
        throw error.create({
            name: 'INVALID_COST',
            message: 'Purchase cost must be greater than zero'
        });
    }

    // Validate purchase date not in future
    const purchaseDate = newRecord.getValue({ fieldId: 'custrecord_purchase_date' });
    if (purchaseDate && new Date(purchaseDate) > new Date()) {
        throw error.create({
            name: 'INVALID_DATE',
            message: 'Purchase date cannot be in the future'
        });
    }

    // Validate required fields based on status
    const status = newRecord.getValue({ fieldId: 'custrecord_status' });
    if (status === STATUS_IN_USE) {
        const assignedEmployee = newRecord.getValue({ fieldId: 'custrecord_assigned_employee' });
        if (!assignedEmployee) {
            throw error.create({
                name: 'MISSING_EMPLOYEE',
                message: 'Asset must be assigned to an employee when status is In Use'
            });
        }
    }
}
```

## Access Control

### Record-Level Permissions

**Permission Levels:**
- None
- View
- Create
- Edit
- Full

**Role-Based Access:**
```
Administrator: Full
Manager: Edit
Employee: View
```

### Field-Level Permissions

```javascript
// Check if user has permission to view/edit field
function checkFieldPermission(recordType, fieldId, userId) {
    // NetSuite handles this automatically based on role permissions
    // Can also use custom logic for dynamic permissions

    const userRole = runtime.getCurrentUser().role;

    if (fieldId === 'custrecord_purchase_cost' && userRole !== FINANCE_ROLE) {
        return false;  // Hide cost from non-finance users
    }

    return true;
}
```

## Performance Optimization

### Indexing

**Enable Search Indexing on:**
- Fields used in search filters
- Parent/child relationship fields
- Fields used in joins

**Example:**
```
custrecord_asset_id - Indexed (frequently searched)
custrecord_status - Indexed (filter criteria)
custrecord_assigned_employee - Indexed (join field)
```

### Caching

```javascript
// Cache custom record lookups
const ASSET_TYPE_CACHE = {};

function getAssetType(assetId) {
    if (ASSET_TYPE_CACHE[assetId]) {
        return ASSET_TYPE_CACHE[assetId];
    }

    const assetType = search.lookupFields({
        type: 'customrecord_asset',
        id: assetId,
        columns: ['custrecord_asset_type']
    }).custrecord_asset_type;

    ASSET_TYPE_CACHE[assetId] = assetType;
    return assetType;
}
```

## Best Practices

### Naming Conventions

```javascript
// Record Types
customrecord_[purpose]              // customrecord_asset
customrecord_[entity]_[qualifier]   // customrecord_contract_renewal

// Fields
custrecord_[descriptive_name]       // custrecord_purchase_date
custrecord_[record]_[field]         // custrecord_asset_status

// Lists
[descriptive_name]                  // Asset Type, Contract Status
```

### Data Migration

```javascript
// Bulk create custom records from CSV
function importAssets(csvData) {
    const assets = parseCSV(csvData);

    for (const assetData of assets) {
        try {
            createAssetRecord(assetData);
        } catch (e) {
            log.error({
                title: 'Import Failed',
                details: `Asset ${assetData.assetId}: ${e.message}`
            });
        }
    }
}
```

### Audit Trail

```javascript
// Track changes to custom records
function beforeSubmit(context) {
    if (context.type === context.UserEventType.EDIT) {
        const oldRecord = context.oldRecord;
        const newRecord = context.newRecord;

        const oldStatus = oldRecord.getValue({ fieldId: 'custrecord_status' });
        const newStatus = newRecord.getValue({ fieldId: 'custrecord_status' });

        if (oldStatus !== newStatus) {
            // Log status change
            createAuditLog({
                recordId: newRecord.id,
                field: 'Status',
                oldValue: oldStatus,
                newValue: newStatus,
                changedBy: runtime.getCurrentUser().id,
                changedDate: new Date()
            });
        }
    }
}
```

## Related Documentation

- **[Relationship Management](relationship-management.md)** - Linking custom records to standard records
- **[Journal Entries](../finance/journal-entries.md)** - Using custom records in JE automation

**External References:**
- [NetSuite Custom Records](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N294843.html)
- [SuiteScript Record API](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4267255379.html)

---

*Generic custom record design patterns for NetSuite data model extensions*
