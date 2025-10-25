# Relationship Management

Patterns for linking custom records to standard NetSuite records and managing complex data relationships.

## Overview

Effective relationship management connects custom records with standard NetSuite entities (Customers, Vendors, Items, Transactions) to create integrated business processes.

**Relationship Types:**
- **One-to-One** - Custom record references single standard record
- **One-to-Many** - Standard record has multiple custom records
- **Many-to-Many** - Junction records for complex relationships
- **Parent-Child** - Hierarchical relationships
- **Cross-Record** - Linking across multiple record types

**Common Patterns:**
- Customer → Service Contracts
- Vendor → Compliance Certifications
- Employee → Training Records
- Item → Product Specifications
- Project → Milestones & Deliverables

## One-to-One Relationships

### Simple Reference Field

Link custom record to standard entity.

**Example: Equipment Maintenance Record → Asset (Standard Record)**

```javascript
/**
 * @NApiVersion 2.1
 */

define(['N/record'], (record) => {

    function createMaintenanceRecord(assetId, maintenanceData) {
        const maintenance = record.create({
            type: 'customrecord_equipment_maintenance',
            isDynamic: true
        });

        // Link to asset (standard fixed asset record)
        maintenance.setValue({
            fieldId: 'custrecord_asset',
            value: assetId  // Internal ID of asset record
        });

        maintenance.setValue({
            fieldId: 'custrecord_maintenance_date',
            value: new Date(maintenanceData.date)
        });

        maintenance.setValue({
            fieldId: 'custrecord_maintenance_type',
            value: maintenanceData.type
        });

        maintenance.setValue({
            fieldId: 'custrecord_cost',
            value: maintenanceData.cost
        });

        return maintenance.save();
    }

    return {
        createMaintenanceRecord: createMaintenanceRecord
    };
});
```

### Reverse Lookup

Find all custom records linked to standard record.

```javascript
function getAssetMaintenanceHistory(assetId) {
    const maintenanceSearch = search.create({
        type: 'customrecord_equipment_maintenance',
        filters: [
            ['custrecord_asset', 'is', assetId]
        ],
        columns: [
            'custrecord_maintenance_date',
            'custrecord_maintenance_type',
            'custrecord_cost',
            'custrecord_performed_by'
        ]
    });

    const history = [];
    maintenanceSearch.run().each((result) => {
        history.push({
            date: result.getValue({ name: 'custrecord_maintenance_date' }),
            type: result.getValue({ name: 'custrecord_maintenance_type' }),
            cost: result.getValue({ name: 'custrecord_cost' }),
            performedBy: result.getText({ name: 'custrecord_performed_by' })
        });
        return true;
    });

    return history;
}
```

## One-to-Many Relationships

### Customer Service Contracts

Multiple contracts per customer.

**Custom Record Structure:**
```
customrecord_service_contract
  - custrecord_customer (List/Record → Customer)
  - custrecord_contract_number (Text)
  - custrecord_start_date (Date)
  - custrecord_end_date (Date)
  - custrecord_annual_value (Currency)
  - custrecord_status (List: Active, Expired, Cancelled)
```

**Creating Contracts:**

```javascript
function createServiceContract(customerId, contractData) {
    const contract = record.create({
        type: 'customrecord_service_contract'
    });

    contract.setValue({
        fieldId: 'name',
        value: contractData.contractNumber
    });

    contract.setValue({
        fieldId: 'custrecord_customer',
        value: customerId
    });

    contract.setValue({
        fieldId: 'custrecord_contract_number',
        value: contractData.contractNumber
    });

    contract.setValue({
        fieldId: 'custrecord_start_date',
        value: new Date(contractData.startDate)
    });

    contract.setValue({
        fieldId: 'custrecord_end_date',
        value: new Date(contractData.endDate)
    });

    contract.setValue({
        fieldId: 'custrecord_annual_value',
        value: contractData.annualValue
    });

    contract.setValue({
        fieldId: 'custrecord_status',
        value: STATUS_ACTIVE
    });

    return contract.save();
}
```

**Querying Related Contracts:**

```javascript
function getCustomerContracts(customerId, activeOnly = true) {
    const filters = [
        ['custrecord_customer', 'is', customerId]
    ];

    if (activeOnly) {
        filters.push('AND');
        filters.push(['custrecord_status', 'is', STATUS_ACTIVE]);
    }

    const contractSearch = search.create({
        type: 'customrecord_service_contract',
        filters: filters,
        columns: [
            'custrecord_contract_number',
            'custrecord_start_date',
            'custrecord_end_date',
            'custrecord_annual_value',
            'custrecord_status'
        ]
    });

    return contractSearch.run().getRange({ start: 0, end: 100 });
}
```

## Many-to-Many Relationships

### Junction Records

Link multiple records of different types.

**Example: Items ↔ Vendors (Approved Supplier List)**

```
customrecord_approved_supplier
  - custrecord_item (List/Record → Item)
  - custrecord_vendor (List/Record → Vendor)
  - custrecord_lead_time_days (Integer)
  - custrecord_unit_cost (Currency)
  - custrecord_approved_date (Date)
  - custrecord_status (List: Active, Discontinued)
```

**Creating Junction Record:**

```javascript
function approveVendorForItem(itemId, vendorId, approvalData) {
    const approvedSupplier = record.create({
        type: 'customrecord_approved_supplier'
    });

    approvedSupplier.setValue({
        fieldId: 'custrecord_item',
        value: itemId
    });

    approvedSupplier.setValue({
        fieldId: 'custrecord_vendor',
        value: vendorId
    });

    approvedSupplier.setValue({
        fieldId: 'custrecord_lead_time_days',
        value: approvalData.leadTimeDays
    });

    approvedSupplier.setValue({
        fieldId: 'custrecord_unit_cost',
        value: approvalData.unitCost
    });

    approvedSupplier.setValue({
        fieldId: 'custrecord_approved_date',
        value: new Date()
    });

    approvedSupplier.setValue({
        fieldId: 'custrecord_status',
        value: STATUS_ACTIVE
    });

    return approvedSupplier.save();
}
```

**Querying Junction Data:**

```javascript
// Get all approved vendors for an item
function getApprovedVendorsForItem(itemId) {
    return search.create({
        type: 'customrecord_approved_supplier',
        filters: [
            ['custrecord_item', 'is', itemId],
            'AND',
            ['custrecord_status', 'is', STATUS_ACTIVE]
        ],
        columns: [
            'custrecord_vendor',
            'custrecord_lead_time_days',
            'custrecord_unit_cost'
        ]
    }).run().getRange({ start: 0, end: 100 });
}

// Get all items supplied by a vendor
function getItemsForVendor(vendorId) {
    return search.create({
        type: 'customrecord_approved_supplier',
        filters: [
            ['custrecord_vendor', 'is', vendorId],
            'AND',
            ['custrecord_status', 'is', STATUS_ACTIVE]
        ],
        columns: [
            'custrecord_item',
            'custrecord_lead_time_days',
            'custrecord_unit_cost'
        ]
    }).run().getRange({ start: 0, end: 100 });
}
```

## Transaction Relationships

### Linking Custom Records to Transactions

**Example: Project Time Tracking → Time Entries**

```javascript
function linkProjectToTimeEntry(timeEntryId, projectId, phaseId) {
    record.submitFields({
        type: record.Type.TIME_BILL,
        id: timeEntryId,
        values: {
            custcol_project: projectId,        // Custom transaction column
            custcol_project_phase: phaseId     // Custom transaction column
        }
    });
}

function getProjectTimeEntries(projectId) {
    return search.create({
        type: search.Type.TIME_BILL,
        filters: [
            ['custcol_project', 'is', projectId]
        ],
        columns: [
            'employee',
            'hours',
            'custcol_project_phase',
            'trandate'
        ]
    }).run().getRange({ start: 0, end: 1000 });
}
```

## Cross-Record Linking

### Complex Business Processes

**Example: Order → Shipment → Invoice**

```javascript
function createShipmentFromOrder(salesOrderId) {
    // Load sales order
    const salesOrder = record.load({
        type: record.Type.SALES_ORDER,
        id: salesOrderId
    });

    // Create custom shipment record
    const shipment = record.create({
        type: 'customrecord_shipment',
        isDynamic: true
    });

    shipment.setValue({
        fieldId: 'custrecord_sales_order',
        value: salesOrderId
    });

    shipment.setValue({
        fieldId: 'custrecord_customer',
        value: salesOrder.getValue({ fieldId: 'entity' })
    });

    shipment.setValue({
        fieldId: 'custrecord_ship_date',
        value: new Date()
    });

    const shipmentId = shipment.save();

    // Link shipment back to sales order
    salesOrder.setValue({
        fieldId: 'custbody_shipment_record',
        value: shipmentId
    });
    salesOrder.save();

    return shipmentId;
}
```

## Data Integrity Patterns

### Cascade Delete

```javascript
/**
 * User Event beforeDelete
 * Delete related custom records when parent is deleted
 */
function beforeDelete(context) {
    const parentId = context.newRecord.id;

    // Find all child records
    const childRecords = search.create({
        type: 'customrecord_child',
        filters: [
            ['custrecord_parent', 'is', parentId]
        ]
    }).run();

    // Delete each child
    childRecords.each((result) => {
        record.delete({
            type: 'customrecord_child',
            id: result.id
        });
        return true;
    });
}
```

### Referential Integrity

```javascript
/**
 * Prevent deletion if custom records reference this entity
 */
function beforeDelete(context) {
    const customerId = context.newRecord.id;

    // Check for active contracts
    const activeContracts = search.create({
        type: 'customrecord_service_contract',
        filters: [
            ['custrecord_customer', 'is', customerId],
            'AND',
            ['custrecord_status', 'is', STATUS_ACTIVE]
        ]
    }).runPaged().count;

    if (activeContracts > 0) {
        throw error.create({
            name: 'CANNOT_DELETE_CUSTOMER',
            message: `Customer has ${activeContracts} active contracts. Cannot delete.`
        });
    }
}
```

## Performance Optimization

### Joined Searches

```javascript
// Efficient: Single search with joins
function getContractsWithCustomerDetails() {
    return search.create({
        type: 'customrecord_service_contract',
        filters: [
            ['custrecord_status', 'is', STATUS_ACTIVE]
        ],
        columns: [
            'custrecord_contract_number',
            'custrecord_annual_value',
            search.createColumn({
                name: 'companyname',
                join: 'custrecord_customer'  // Join to Customer record
            }),
            search.createColumn({
                name: 'email',
                join: 'custrecord_customer'
            })
        ]
    }).run().getRange({ start: 0, end: 1000 });
}

// Inefficient: Separate lookups
function getContractsWithCustomerDetailsInefficient() {
    const contracts = search.create({
        type: 'customrecord_service_contract'
    }).run().getRange({ start: 0, end: 1000 });

    return contracts.map((contract) => {
        const customerId = contract.getValue({ name: 'custrecord_customer' });

        // Separate lookup for each contract!
        const customer = record.load({
            type: record.Type.CUSTOMER,
            id: customerId
        });

        return {
            contractNumber: contract.getValue({ name: 'custrecord_contract_number' }),
            customerName: customer.getValue({ fieldId: 'companyname' }),
            customerEmail: customer.getValue({ fieldId: 'email' })
        };
    });
}
```

### Batch Processing

```javascript
function updateContractStatuses(contractIds, newStatus) {
    for (const contractId of contractIds) {
        try {
            record.submitFields({
                type: 'customrecord_service_contract',
                id: contractId,
                values: {
                    custrecord_status: newStatus
                }
            });
        } catch (e) {
            log.error({
                title: 'Update Failed',
                details: `Contract ${contractId}: ${e.message}`
            });
        }
    }
}
```

## Best Practices

### Naming Conventions

```javascript
// Relationship Fields
custrecord_[entity]          // custrecord_customer, custrecord_vendor
custrecord_parent_[entity]   // custrecord_parent_project
custrecord_related_[entity]  // custrecord_related_transaction
```

### Bidirectional Links

```javascript
// Link custom record to transaction
function linkCustomRecordToTransaction(customRecordId, transactionId) {
    // Update custom record
    record.submitFields({
        type: 'customrecord_project_milestone',
        id: customRecordId,
        values: {
            custrecord_invoice: transactionId
        }
    });

    // Update transaction
    record.submitFields({
        type: record.Type.INVOICE,
        id: transactionId,
        values: {
            custbody_project_milestone: customRecordId
        }
    });
}
```

### Null Handling

```javascript
function getRelatedRecord(customRecordId, relationshipField) {
    const relatedId = search.lookupFields({
        type: 'customrecord_type',
        id: customRecordId,
        columns: [relationshipField]
    })[relationshipField];

    // Handle empty relationship
    if (!relatedId || relatedId.length === 0) {
        return null;
    }

    // If multi-select, relatedId is array
    return Array.isArray(relatedId) ? relatedId[0].value : relatedId;
}
```

## Related Documentation

- **[Custom Record Design](record-design.md)** - Designing custom record structure
- **[Sales Orders](../order-to-cash/sales-orders.md)** - Transaction relationships

**External References:**
- [NetSuite Custom Records](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N294843.html)
- [Search Joins](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N3477018.html)

---

*Generic relationship management patterns for linking custom and standard NetSuite records*
