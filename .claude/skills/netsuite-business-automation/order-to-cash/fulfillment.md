# Order Fulfillment Automation

Automated sales order fulfillment, shipping integration, and inventory allocation.

## Overview

Fulfillment automation manages the process from approved sales order to shipped goods, including inventory allocation, picking, packing, and carrier integration.

**Fulfillment Workflow:**
1. Sales order approved
2. Inventory allocated
3. Pick list generated
4. Items picked and packed
5. Item fulfillment created
6. Shipping label printed
7. Tracking number captured
8. Customer notification sent

**Automation Benefits:**
- 60% faster order-to-ship cycle time
- Reduced picking errors
- Real-time inventory updates
- Automated customer communication

## Auto-Fulfillment

### Automatic Item Fulfillment Creation

Create item fulfillment when sales order is approved.

**User Event Script (afterSubmit on Sales Order):**

```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType UserEventScript
 */

define(['N/record', 'N/search'], (record, search) => {

    function afterSubmit(context) {
        if (context.type !== context.UserEventType.EDIT) {
            return;
        }

        const salesOrder = context.newRecord;
        const oldStatus = context.oldRecord.getValue({ fieldId: 'orderstatus' });
        const newStatus = salesOrder.getValue({ fieldId: 'orderstatus' });

        // Check if status changed to Pending Fulfillment
        if (oldStatus !== 'B' && newStatus === 'B') {
            // Check if auto-fulfillment enabled
            const autoFulfill = salesOrder.getValue({ fieldId: 'custbody_auto_fulfill' });

            if (autoFulfill && hasInventoryAvailable(salesOrder.id)) {
                createItemFulfillment(salesOrder.id);
            }
        }
    }

    function hasInventoryAvailable(salesOrderId) {
        const so = record.load({
            type: record.Type.SALES_ORDER,
            id: salesOrderId
        });

        const lineCount = so.getLineCount({ sublistId: 'item' });

        for (let i = 0; i < lineCount; i++) {
            const itemId = so.getSublistValue({
                sublistId: 'item',
                fieldId: 'item',
                line: i
            });

            const quantity = so.getSublistValue({
                sublistId: 'item',
                fieldId: 'quantity',
                line: i
            });

            // Check available inventory
            const available = getItemAvailability(itemId);

            if (available < quantity) {
                return false;  // Insufficient inventory
            }
        }

        return true;  // All items available
    }

    function createItemFulfillment(salesOrderId) {
        const fulfillment = record.transform({
            fromType: record.Type.SALES_ORDER,
            fromId: salesOrderId,
            toType: record.Type.ITEM_FULFILLMENT,
            isDynamic: true
        });

        // Set ship date to today
        fulfillment.setValue({
            fieldId: 'shipdate',
            value: new Date()
        });

        // Save fulfillment
        const fulfillmentId = fulfillment.save();

        log.audit({
            title: 'Auto-Fulfillment Created',
            details: `Sales Order ${salesOrderId} → Item Fulfillment ${fulfillmentId}`
        });

        return fulfillmentId;
    }

    return {
        afterSubmit: afterSubmit
    };
});
```

## Shipping Integration

### Carrier Integration (UPS/FedEx/USPS)

**RESTlet for shipping API callback:**

```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType Restlet
 */

define(['N/record'], (record) => {

    function post(requestBody) {
        // Receive tracking info from shipping carrier
        const { salesOrderId, carrier, trackingNumber, shipDate, estimatedDelivery } = requestBody;

        // Update item fulfillment
        const fulfillment = findFulfillmentForOrder(salesOrderId);

        if (fulfillment) {
            record.submitFields({
                type: record.Type.ITEM_FULFILLMENT,
                id: fulfillment.id,
                values: {
                    custbody_tracking_number: trackingNumber,
                    custbody_carrier: carrier,
                    shipdate: new Date(shipDate),
                    custbody_estimated_delivery: new Date(estimatedDelivery)
                }
            });

            // Send customer notification
            sendShippingNotification(salesOrderId, trackingNumber, carrier);

            return {
                success: true,
                message: `Tracking updated for order ${salesOrderId}`
            };
        }

        return {
            success: false,
            message: 'Fulfillment not found'
        };
    }

    return {
        post: post
    };
});
```

## Inventory Allocation

### Reserve Inventory on Order Approval

```javascript
function allocateInventory(salesOrderId) {
    const so = record.load({
        type: record.Type.SALES_ORDER,
        id: salesOrderId
    });

    const lineCount = so.getLineCount({ sublistId: 'item' });
    const allocationResults = [];

    for (let i = 0; i < lineCount; i++) {
        const itemId = so.getSublistValue({ sublistId: 'item', fieldId: 'item', line: i });
        const quantity = so.getSublistValue({ sublistId: 'item', fieldId: 'quantity', line: i });
        const location = so.getSublistValue({ sublistId: 'item', fieldId: 'location', line: i });

        const allocated = allocateItemInventory({
            itemId: itemId,
            quantity: quantity,
            location: location,
            salesOrderId: salesOrderId,
            lineNumber: i
        });

        allocationResults.push(allocated);
    }

    return allocationResults;
}
```

## Best Practices

### Drop-Ship Handling

```javascript
function handleDropShipOrder(salesOrderId) {
    const so = record.load({
        type: record.Type.SALES_ORDER,
        id: salesOrderId
    });

    // Check if any line items are drop-ship
    const lineCount = so.getLineCount({ sublistId: 'item' });

    for (let i = 0; i < lineCount; i++) {
        const isDropShip = so.getSublistValue({
            sublistId: 'item',
            fieldId: 'isdropship',
            line: i
        });

        if (isDropShip) {
            // Create linked purchase order to vendor
            createDropShipPO(salesOrderId, i);
        }
    }
}
```

### Partial Fulfillment

```javascript
function createPartialFulfillment(salesOrderId, itemsToShip) {
    const fulfillment = record.transform({
        fromType: record.Type.SALES_ORDER,
        fromId: salesOrderId,
        toType: record.Type.ITEM_FULFILLMENT,
        isDynamic: true
    });

    // Uncheck items not being shipped
    const lineCount = fulfillment.getLineCount({ sublistId: 'item' });

    for (let i = 0; i < lineCount; i++) {
        const itemId = fulfillment.getSublistValue({ sublistId: 'item', fieldId: 'item', line: i });

        const shouldShip = itemsToShip.includes(itemId);

        fulfillment.setSublistValue({
            sublistId: 'item',
            fieldId: 'itemreceive',
            line: i,
            value: shouldShip
        });
    }

    return fulfillment.save();
}
```

## Related Documentation

- **[Sales Orders](sales-orders.md)** - Order creation and validation
- **[Invoicing](invoicing.md)** - Invoice generation from fulfillment
- **[Notification Automation](../workflows/notification-automation.md)** - Shipping notifications

**External References:**
- [Item Fulfillment](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N303700.html)

---

*Generic order fulfillment automation patterns for sales order processing*
