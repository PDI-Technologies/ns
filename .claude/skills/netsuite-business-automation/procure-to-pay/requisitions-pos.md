# Purchase Requisitions and Orders

Automated requisition approval, purchase order creation, and vendor management.

## Overview

Requisition and PO automation streamlines procurement from employee request through vendor order placement.

**Workflow Stages:**
1. Employee creates requisition
2. Approval routing (manager → director → procurement)
3. Requisition approved
4. Purchase order auto-generated
5. PO sent to vendor
6. Receiving process begins

**Automation Benefits:**
- 50% faster requisition-to-PO cycle
- Reduced maverick spend
- Budget compliance enforcement
- Audit trail for all purchases

## Requisition Creation

### Auto-Convert Requisition to PO

**Workflow Action Script:**

```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType WorkflowActionScript
 */

define(['N/record'], (record) => {

    function onAction(context) {
        const requisition = context.newRecord;
        const requisitionId = requisition.id;

        // Transform requisition to purchase order
        const purchaseOrder = record.transform({
            fromType: record.Type.PURCHASE_REQUISITION,
            fromId: requisitionId,
            toType: record.Type.PURCHASE_ORDER,
            isDynamic: false
        });

        // Set PO date
        purchaseOrder.setValue({
            fieldId: 'trandate',
            value: new Date()
        });

        // Save PO
        const poId = purchaseOrder.save();

        // Link back to requisition
        record.submitFields({
            type: record.Type.PURCHASE_REQUISITION,
            id: requisitionId,
            values: {
                custbody_linked_po: poId
            }
        });

        log.audit({
            title: 'PO Created from Requisition',
            details: `Requisition ${requisitionId} → PO ${poId}`
        });

        return 'SUCCESS';
    }

    return {
        onAction: onAction
    };
});
```

## Approval Routing

### Budget Validation

Verify budget availability before approval.

**User Event Script (beforeSubmit):**

```javascript
function beforeSubmit(context) {
    if (context.type !== context.UserEventType.CREATE &&
        context.type !== context.UserEventType.EDIT) {
        return;
    }

    const requisition = context.newRecord;
    const department = requisition.getValue({ fieldId: 'department' });
    const total = parseFloat(requisition.getValue({ fieldId: 'total' }));
    const accountingPeriod = requisition.getValue({ fieldId: 'postingperiod' });

    // Check budget availability
    const budgetRemaining = getDepartmentBudgetRemaining(department, accountingPeriod);

    if (total > budgetRemaining) {
        throw error.create({
            name: 'BUDGET_EXCEEDED',
            message: `Requisition amount $${total} exceeds remaining budget $${budgetRemaining} for ${getDepartmentName(department)}`
        });
    }

    // Reserve budget
    reserveBudget(department, accountingPeriod, total);
}
```

### Preferred Vendor Lookup

```javascript
function suggestPreferredVendor(itemId) {
    // Lookup item's preferred vendor
    const itemFields = search.lookupFields({
        type: search.Type.ITEM,
        id: itemId,
        columns: ['preferredvendor', 'cost']
    });

    return {
        vendorId: itemFields.preferredvendor?.[0]?.value,
        vendorName: itemFields.preferredvendor?.[0]?.text,
        cost: parseFloat(itemFields.cost)
    };
}
```

## Purchase Order Management

### Auto-Email PO to Vendor

**User Event Script (afterSubmit):**

```javascript
function afterSubmit(context) {
    if (context.type !== context.UserEventType.CREATE) {
        return;
    }

    const purchaseOrder = context.newRecord;
    const vendorId = purchaseOrder.getValue({ fieldId: 'entity' });

    // Get vendor email
    const vendorEmail = search.lookupFields({
        type: search.Type.VENDOR,
        id: vendorId,
        columns: ['email']
    }).email;

    if (vendorEmail) {
        sendPOToVendor(purchaseOrder.id, vendorEmail);
    }
}

function sendPOToVendor(purchaseOrderId, vendorEmail) {
    const po = record.load({
        type: record.Type.PURCHASE_ORDER,
        id: purchaseOrderId
    });

    const poNumber = po.getValue({ fieldId: 'tranid' });

    // Render PO as PDF
    const pdfFile = render.transaction({
        entityId: purchaseOrderId,
        printMode: render.PrintMode.PDF
    });

    email.send({
        author: PURCHASING_MANAGER_ID,
        recipients: vendorEmail,
        subject: `Purchase Order ${poNumber}`,
        body: `Please find attached purchase order ${poNumber}.\n\nPlease confirm receipt and estimated delivery date.`,
        attachments: [pdfFile],
        relatedRecords: {
            transactionId: purchaseOrderId
        }
    });

    // Mark PO as emailed
    record.submitFields({
        type: record.Type.PURCHASE_ORDER,
        id: purchaseOrderId,
        values: {
            custbody_po_emailed: true,
            custbody_po_email_date: new Date()
        }
    });
}
```

## Vendor Selection

### Competitive Bidding

```javascript
function requestQuotesFromVendors(requisitionId, vendorIds) {
    const requisition = record.load({
        type: record.Type.PURCHASE_REQUISITION,
        id: requisitionId
    });

    const quoteRequests = [];

    for (const vendorId of vendorIds) {
        // Create quote request (custom record)
        const quoteRequest = record.create({
            type: 'customrecord_rfq'
        });

        quoteRequest.setValue({ fieldId: 'custrecord_requisition', value: requisitionId });
        quoteRequest.setValue({ fieldId: 'custrecord_vendor', value: vendorId });
        quoteRequest.setValue({ fieldId: 'custrecord_due_date', value: getDueDateForQuote() });

        const quoteId = quoteRequest.save();
        quoteRequests.push(quoteId);

        // Email RFQ to vendor
        sendRFQToVendor(vendorId, requisitionId);
    }

    return quoteRequests;
}
```

## Best Practices

### Three-Way Match Enforcement

```javascript
function enforceThreeWayMatch(vendorBillId) {
    const bill = record.load({
        type: record.Type.VENDOR_BILL,
        id: vendorBillId
    });

    const poId = bill.getValue({ fieldId: 'createdfrom' });

    if (!poId) {
        throw error.create({
            name: 'NO_PO',
            message: 'Vendor bill must reference a purchase order (three-way match required)'
        });
    }

    // Verify receipt exists
    const receipts = search.create({
        type: search.Type.ITEM_RECEIPT,
        filters: [
            ['createdfrom', 'is', poId]
        ]
    }).run().getRange({ start: 0, end: 1 });

    if (receipts.length === 0) {
        throw error.create({
            name: 'NO_RECEIPT',
            message: 'Cannot process vendor bill without item receipt (three-way match required)'
        });
    }
}
```

### PO Change Management

```javascript
function trackPOChanges(context) {
    if (context.type !== context.UserEventType.EDIT) {
        return;
    }

    const oldPO = context.oldRecord;
    const newPO = context.newRecord;

    const changes = [];

    // Check for amount changes
    const oldTotal = oldPO.getValue({ fieldId: 'total' });
    const newTotal = newPO.getValue({ fieldId: 'total' });

    if (oldTotal !== newTotal) {
        changes.push({
            field: 'Total',
            oldValue: oldTotal,
            newValue: newTotal,
            variance: newTotal - oldTotal
        });
    }

    // Log changes
    if (changes.length > 0) {
        createPOChangeLog(newPO.id, changes);

        // Require re-approval if total increased significantly
        if (newTotal > oldTotal * 1.1) {  // 10% increase
            newPO.setValue({
                fieldId: 'custbody_approval_status',
                value: 'Pending Re-Approval'
            });
        }
    }
}
```

## Related Documentation

- **[Receiving](receiving.md)** - Goods receipt processing
- **[Vendor Bills](vendor-bills.md)** - Three-way match
- **[Approval Routing](../workflows/approval-routing.md)** - Approval workflows

**External References:**
- [Purchase Order](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N304375.html)

---

*Generic requisition and purchase order automation patterns*
