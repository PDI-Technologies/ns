# Item Receipt Automation

Automated goods receipt processing, inspection workflows, and inventory updates.

## Overview

Receiving automation manages the process of recording goods received from vendors, updating inventory, and enabling three-way match for vendor bill processing.

**Receiving Workflow:**
1. Purchase order issued to vendor
2. Goods arrive at warehouse
3. Physical inspection and quality check
4. Item receipt created in NetSuite
5. Inventory updated
6. Vendor bill matching enabled

**Automation Benefits:**
- Real-time inventory visibility
- Reduced receiving errors
- Faster vendor bill processing
- Quality control tracking

## Auto-Receipt Creation

### Mobile Barcode Scanning Integration

**RESTlet for mobile app:**

```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType Restlet
 */

define(['N/record'], (record) => {

    function post(requestBody) {
        const { purchaseOrderId, receivedItems, inspectionNotes } = requestBody;

        // Create item receipt
        const receipt = record.transform({
            fromType: record.Type.PURCHASE_ORDER,
            fromId: purchaseOrderId,
            toType: record.Type.ITEM_RECEIPT,
            isDynamic: true
        });

        // Set receipt date
        receipt.setValue({
            fieldId: 'trandate',
            value: new Date()
        });

        // Mark received items
        const lineCount = receipt.getLineCount({ sublistId: 'item' });

        for (let i = 0; i < lineCount; i++) {
            const itemId = receipt.getSublistValue({
                sublistId: 'item',
                fieldId: 'item',
                line: i
            });

            const receivedItem = receivedItems.find(ri => ri.itemId === itemId);

            if (receivedItem) {
                receipt.selectLine({ sublistId: 'item', line: i });

                receipt.setCurrentSublistValue({
                    sublistId: 'item',
                    fieldId: 'itemreceive',
                    value: true
                });

                receipt.setCurrentSublistValue({
                    sublistId: 'item',
                    fieldId: 'quantity',
                    value: receivedItem.quantityReceived
                });

                receipt.commitLine({ sublistId: 'item' });
            }
        }

        // Add inspection notes
        receipt.setValue({
            fieldId: 'memo',
            value: inspectionNotes || 'Items received and inspected'
        });

        const receiptId = receipt.save();

        return {
            success: true,
            receiptId: receiptId,
            message: `Item receipt ${receiptId} created`
        };
    }

    return {
        post: post
    };
});
```

## Quality Inspection

### Inspection Workflow

```javascript
function performQualityInspection(receiptId) {
    const receipt = record.load({
        type: record.Type.ITEM_RECEIPT,
        id: receiptId
    });

    const lineCount = receipt.getLineCount({ sublistId: 'item' });
    const inspectionResults = [];

    for (let i = 0; i < lineCount; i++) {
        const itemId = receipt.getSublistValue({ sublistId: 'item', fieldId: 'item', line: i });
        const quantity = receipt.getSublistValue({ sublistId: 'item', fieldId: 'quantity', line: i });

        // Perform inspection (this would integrate with quality system)
        const inspectionPassed = performItemInspection(itemId, quantity);

        if (!inspectionPassed) {
            // Mark line as rejected
            receipt.setSublistValue({
                sublistId: 'item',
                fieldId: 'custcol_inspection_status',
                line: i,
                value: 'Failed'
            });

            inspectionResults.push({
                itemId: itemId,
                status: 'Failed',
                action: 'Return to vendor'
            });
        } else {
            receipt.setSublistValue({
                sublistId: 'item',
                fieldId: 'custcol_inspection_status',
                line: i,
                value: 'Passed'
            });

            inspectionResults.push({
                itemId: itemId,
                status: 'Passed',
                action: 'Accept'
            });
        }
    }

    receipt.save();

    return inspectionResults;
}
```

## Partial Receipts

### Handle Partial Deliveries

```javascript
function createPartialReceipt(purchaseOrderId, receivedItems) {
    const receipt = record.transform({
        fromType: record.Type.PURCHASE_ORDER,
        fromId: purchaseOrderId,
        toType: record.Type.ITEM_RECEIPT,
        isDynamic: true
    });

    const lineCount = receipt.getLineCount({ sublistId: 'item' });

    for (let i = 0; i < lineCount; i++) {
        const itemId = receipt.getSublistValue({ sublistId: 'item', fieldId: 'item', line: i });
        const orderedQty = receipt.getSublistValue({ sublistId: 'item', fieldId: 'quantity', line: i });

        const receivedItem = receivedItems.find(ri => ri.itemId === itemId);

        if (receivedItem && receivedItem.quantityReceived > 0) {
            receipt.selectLine({ sublistId: 'item', line: i });

            receipt.setCurrentSublistValue({
                sublistId: 'item',
                fieldId: 'itemreceive',
                value: true
            });

            receipt.setCurrentSublistValue({
                sublistId: 'item',
                fieldId: 'quantity',
                value: receivedItem.quantityReceived
            });

            receipt.commitLine({ sublistId: 'item' });
        } else {
            // Don't receive this line
            receipt.setSublistValue({
                sublistId: 'item',
                fieldId: 'itemreceive',
                line: i,
                value: false
            });
        }
    }

    return receipt.save();
}
```

## Vendor Performance Tracking

### Track Receipt Timeliness

```javascript
function trackVendorDeliveryPerformance(receiptId) {
    const receipt = record.load({
        type: record.Type.ITEM_RECEIPT,
        id: receiptId
    });

    const poId = receipt.getValue({ fieldId: 'createdfrom' });
    const vendorId = receipt.getValue({ fieldId: 'entity' });
    const receiptDate = receipt.getValue({ fieldId: 'trandate' });

    // Get PO expected receipt date
    const po = record.load({
        type: record.Type.PURCHASE_ORDER,
        id: poId
    });

    const expectedDate = po.getValue({ fieldId: 'expectedreceiptdate' });

    if (expectedDate) {
        const daysDiff = Math.floor(
            (new Date(receiptDate) - new Date(expectedDate)) / (1000 * 60 * 60 * 24)
        );

        // Create vendor performance record
        createVendorPerformanceLog({
            vendorId: vendorId,
            purchaseOrderId: poId,
            expectedDate: expectedDate,
            actualDate: receiptDate,
            daysDifference: daysDiff,
            onTime: daysDiff <= 0
        });
    }
}
```

## Best Practices

### Receipt Validation

```javascript
function validateReceipt(context) {
    const receipt = context.newRecord;

    // Verify at least one item is being received
    const lineCount = receipt.getLineCount({ sublistId: 'item' });
    let hasReceivedItems = false;

    for (let i = 0; i < lineCount; i++) {
        const itemReceive = receipt.getSublistValue({
            sublistId: 'item',
            fieldId: 'itemreceive',
            line: i
        });

        if (itemReceive) {
            hasReceivedItems = true;
            break;
        }
    }

    if (!hasReceivedItems) {
        throw error.create({
            name: 'NO_ITEMS_RECEIVED',
            message: 'At least one item must be marked as received'
        });
    }
}
```

## Related Documentation

- **[Requisitions/POs](requisitions-pos.md)** - PO creation
- **[Vendor Bills](vendor-bills.md)** - Three-way match
- **[Approval Routing](../workflows/approval-routing.md)** - Approval workflows

**External References:**
- [Item Receipt](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N304250.html)

---

*Generic receiving and item receipt automation patterns*
