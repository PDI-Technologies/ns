# Vendor Bill Processing

Automated vendor bill creation, three-way matching, and AP workflow.

## Overview

Vendor bill automation ensures accurate invoice processing from receipt through payment approval.

**Bill Processing Workflow:**
1. Receive vendor invoice (email, EDI, portal)
2. Match to purchase order and receipt (three-way match)
3. Validate pricing and quantities
4. Route for approval
5. Post to AP subledger
6. Schedule for payment

**Automation Benefits:**
- 70% faster invoice processing
- Reduced data entry errors
- Automated exception handling
- Improved payment accuracy

## Three-Way Match

### PO-Receipt-Invoice Matching

**User Event Script (beforeSubmit):**

```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType UserEventScript
 */

define(['N/record', 'N/search', 'N/error'], (record, search, error) => {

    function beforeSubmit(context) {
        if (context.type !== context.UserEventType.CREATE) {
            return;
        }

        const bill = context.newRecord;
        const poId = bill.getValue({ fieldId: 'createdfrom' });

        if (!poId) {
            throw error.create({
                name: 'NO_PO_REFERENCE',
                message: 'Vendor bill must reference a purchase order'
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
                message: 'Cannot create vendor bill without item receipt'
            });
        }

        // Validate bill amounts match PO
        validateBillAmounts(bill, poId);
    }

    function validateBillAmounts(bill, poId) {
        const po = record.load({
            type: record.Type.PURCHASE_ORDER,
            id: poId
        });

        const billTotal = bill.getValue({ fieldId: 'usertotal' });
        const poTotal = po.getValue({ fieldId: 'total' });

        // Allow 5% tolerance
        const variance = Math.abs(billTotal - poTotal);
        const variancePercent = (variance / poTotal) * 100;

        if (variancePercent > 5) {
            // Flag for manual review
            bill.setValue({
                fieldId: 'custbody_requires_review',
                value: true
            });

            bill.setValue({
                fieldId: 'custbody_review_reason',
                value: `Amount variance: ${variancePercent.toFixed(1)}% (Bill: $${billTotal}, PO: $${poTotal})`
            });
        }
    }

    return {
        beforeSubmit: beforeSubmit
    };
});
```

## OCR Invoice Processing

### Extract Data from Invoice PDF

**Map/Reduce Script:**

```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType MapReduceScript
 */

define(['N/file', 'N/record', 'N/https'], (file, record, https) => {

    function getInputData() {
        // Find unprocessed invoice PDFs
        return search.create({
            type: 'file',
            filters: [
                ['folder', 'is', INBOX_FOLDER_ID],
                'AND',
                ['filetype', 'is', 'PDF']
            ]
        });
    }

    function map(context) {
        const fileId = context.value;

        // Call OCR service (external API)
        const ocrData = callOCRService(fileId);

        // Extract invoice data
        const billData = {
            vendorName: ocrData.vendor,
            invoiceNumber: ocrData.invoiceNumber,
            invoiceDate: ocrData.date,
            total: ocrData.total,
            lineItems: ocrData.lineItems
        };

        // Find matching PO
        const poId = findMatchingPO(billData);

        if (poId) {
            // Create vendor bill
            createVendorBillFromOCR(poId, billData, fileId);
            context.write({ key: fileId, value: 'SUCCESS' });
        } else {
            context.write({ key: fileId, value: 'NO_MATCH' });
        }
    }

    function findMatchingPO(billData) {
        // Search for PO by vendor and approximate amount
        const pos = search.create({
            type: search.Type.PURCHASE_ORDER,
            filters: [
                ['entity.entityid', 'contains', billData.vendorName],
                'AND',
                ['status', 'anyof', ['PurchOrd:D', 'PurchOrd:E']],  // Pending Receipt/Partially Received
                'AND',
                ['total', 'between', billData.total * 0.95, billData.total * 1.05]
            ]
        }).run().getRange({ start: 0, end: 1 });

        return pos.length > 0 ? pos[0].id : null;
    }

    return {
        getInputData: getInputData,
        map: map
    };
});
```

## Approval Workflow

### Route Bills for Approval

```javascript
function routeBillForApproval(billId) {
    const bill = record.load({
        type: record.Type.VENDOR_BILL,
        id: billId
    });

    const total = bill.getValue({ fieldId: 'usertotal' });
    const department = bill.getValue({ fieldId: 'department' });

    // Determine approver based on amount and department
    const approver = determineApprover(total, department);

    record.submitFields({
        type: record.Type.VENDOR_BILL,
        id: billId,
        values: {
            custbody_approver: approver.id,
            approvalstatus: 1  // Pending Approval
        }
    });

    // Send approval notification
    sendApprovalNotification(billId, approver.id);
}
```

## Exception Handling

### Price Variance Detection

```javascript
function detectPriceVariance(bill, po) {
    const variances = [];
    const billLineCount = bill.getLineCount({ sublistId: 'item' });

    for (let i = 0; i < billLineCount; i++) {
        const billItem = bill.getSublistValue({ sublistId: 'item', fieldId: 'item', line: i });
        const billRate = bill.getSublistValue({ sublistId: 'item', fieldId: 'rate', line: i });

        // Find matching PO line
        const poRate = getPOLineRate(po, billItem);

        if (poRate && Math.abs(billRate - poRate) / poRate > 0.05) {  // 5% variance
            variances.push({
                item: billItem,
                poRate: poRate,
                billRate: billRate,
                variancePercent: ((billRate - poRate) / poRate * 100).toFixed(1)
            });
        }
    }

    return variances;
}
```

## Best Practices

### Duplicate Bill Prevention

```javascript
function checkForDuplicateBill(context) {
    const bill = context.newRecord;
    const vendorId = bill.getValue({ fieldId: 'entity' });
    const invoiceNumber = bill.getValue({ fieldId: 'tranid' });

    // Search for existing bills with same vendor and invoice number
    const existingBills = search.create({
        type: search.Type.VENDOR_BILL,
        filters: [
            ['entity', 'is', vendorId],
            'AND',
            ['tranid', 'is', invoiceNumber]
        ]
    }).run().getRange({ start: 0, end: 1 });

    if (existingBills.length > 0) {
        throw error.create({
            name: 'DUPLICATE_BILL',
            message: `Vendor bill with invoice number ${invoiceNumber} already exists (ID: ${existingBills[0].id})`
        });
    }
}
```

## Related Documentation

- **[Receiving](receiving.md)** - Item receipt creation
- **[Payments](payments.md)** - Vendor payment processing
- **[Approval Routing](../workflows/approval-routing.md)** - Approval workflows

**External References:**
- [Vendor Bill](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N304300.html)

---

*Generic vendor bill processing and three-way match automation patterns*
