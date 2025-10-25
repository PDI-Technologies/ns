# Revenue Recognition (Order-to-Cash)

Revenue arrangement creation and tracking within the order-to-cash cycle.

## Overview

Revenue recognition in O2C automates the creation of revenue arrangements when orders are fulfilled and invoiced.

**O2C Revenue Flow:**
1. Sales Order created → Identify performance obligations
2. Order fulfilled → Trigger billing
3. Invoice posted → Create revenue arrangement
4. Revenue recognized → Journal entries created (point-in-time or over time)

**Use Cases:**
- Product sales (immediate recognition)
- Service contracts (deferred recognition)
- Subscription billing (monthly recognition)
- Multi-element arrangements (separate performance obligations)
- Milestone-based projects (recognize on completion)

**Oracle NetSuite Documentation:**
- Revenue Arrangements: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N3211445.html
- See also: [finance/revenue-recognition.md](../finance/revenue-recognition.md) for detailed patterns

## Automatic Revenue Arrangement Creation

### User Event - afterSubmit on Invoice

Create revenue arrangement when invoice is posted.

```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType UserEventScript
 */
define(['N/record', 'N/search'], (record, search) => {

    function afterSubmit(context) {
        if (context.type !== context.UserEventType.CREATE) return;

        const invoice = context.newRecord;
        const salesOrderId = invoice.getValue({ fieldId: 'createdfrom' });

        if (!salesOrderId) return; // No sales order = no arrangement needed

        // Check if arrangement already exists
        if (invoice.getValue({ fieldId: 'custbody_revenue_arrangement' })) return;

        const arrangementId = createRevenueArrangement(invoice, salesOrderId);

        // Link arrangement to invoice
        record.submitFields({
            type: record.Type.INVOICE,
            id: invoice.id,
            values: { 'custbody_revenue_arrangement': arrangementId }
        });
    }

    function createRevenueArrangement(invoice, salesOrderId) {
        // Load sales order to get line items
        const salesOrder = record.load({
            type: record.Type.SALES_ORDER,
            id: salesOrderId,
            isDynamic: false
        });

        // Create arrangement record
        const arrangement = record.create({
            type: 'customrecord_revenue_arrangement',
            isDynamic: false
        });

        arrangement.setValue({ fieldId: 'custrecord_sales_order', value: salesOrderId });
        arrangement.setValue({ fieldId: 'custrecord_invoice', value: invoice.id });
        arrangement.setValue({ fieldId: 'custrecord_customer', value: invoice.getValue({ fieldId: 'entity' }) });
        arrangement.setValue({ fieldId: 'custrecord_total_value', value: invoice.getValue({ fieldId: 'total' }) });
        arrangement.setValue({ fieldId: 'custrecord_status', value: 'ACTIVE' });

        const arrangementId = arrangement.save();

        // Create performance obligations for each line
        const lineCount = salesOrder.getLineCount({ sublistId: 'item' });

        for (let i = 0; i < lineCount; i++) {
            createPerformanceObligation(arrangementId, salesOrder, i);
        }

        return arrangementId;
    }

    function createPerformanceObligation(arrangementId, salesOrder, lineIndex) {
        const itemId = salesOrder.getSublistValue({ sublistId: 'item', fieldId: 'item', line: lineIndex });
        const amount = salesOrder.getSublistValue({ sublistId: 'item', fieldId: 'amount', line: lineIndex });
        const itemType = salesOrder.getSublistValue({ sublistId: 'item', fieldId: 'custcol_revenue_type', line: lineIndex });

        const obligation = record.create({
            type: 'customrecord_performance_obligation',
            isDynamic: false
        });

        obligation.setValue({ fieldId: 'custrecord_arrangement', value: arrangementId });
        obligation.setValue({ fieldId: 'custrecord_item', value: itemId });
        obligation.setValue({ fieldId: 'custrecord_allocated_amount', value: amount });
        obligation.setValue({ fieldId: 'custrecord_recognition_method', value: getRecognitionMethod(itemType) });
        obligation.setValue({ fieldId: 'custrecord_status', value: 'NOT_SATISFIED' });

        return obligation.save();
    }

    function getRecognitionMethod(itemType) {
        const methods = {
            'GOODS': 'POINT_IN_TIME',
            'SERVICE': 'OVER_TIME',
            'SUBSCRIPTION': 'RATABLE',
            'PROJECT': 'MILESTONE'
        };
        return methods[itemType] || 'POINT_IN_TIME';
    }

    return { afterSubmit };
});
```

## Performance Obligation Tracking

### Update Status When Satisfied

Mark performance obligations as satisfied when goods delivered or services rendered.

```javascript
/**
 * User Event on Item Fulfillment - Satisfy performance obligations
 */
function afterSubmit(context) {
    if (context.type !== context.UserEventType.CREATE) return;

    const fulfillment = context.newRecord;
    const salesOrderId = fulfillment.getValue({ fieldId: 'createdfrom' });

    // Find revenue arrangement for this order
    const arrangementId = findArrangementForOrder(salesOrderId);
    if (!arrangementId) return;

    // Mark obligations as satisfied
    const lineCount = fulfillment.getLineCount({ sublistId: 'item' });

    for (let i = 0; i < lineCount; i++) {
        const itemId = fulfillment.getSublistValue({ sublistId: 'item', fieldId: 'item', line: i });
        satisfyPerformanceObligation(arrangementId, itemId);
    }
}

function satisfyPerformanceObligation(arrangementId, itemId) {
    // Find obligation for this item
    const obligationSearch = search.create({
        type: 'customrecord_performance_obligation',
        filters: [
            ['custrecord_arrangement', 'is', arrangementId],
            'AND',
            ['custrecord_item', 'is', itemId],
            'AND',
            ['custrecord_status', 'is', 'NOT_SATISFIED']
        ]
    });

    let obligationId = null;
    obligationSearch.run().each((result) => {
        obligationId = result.id;
        return false; // First result
    });

    if (obligationId) {
        record.submitFields({
            type: 'customrecord_performance_obligation',
            id: obligationId,
            values: {
                'custrecord_status': 'SATISFIED',
                'custrecord_satisfaction_date': new Date()
            }
        });
    }
}
```

## Transaction Price Allocation

### Allocate Based on Standalone Selling Price

Allocate transaction price across performance obligations per ASC 606.

```javascript
function allocateTransactionPrice(arrangementId, totalPrice) {
    // Get all performance obligations
    const obligations = [];

    const obligationSearch = search.create({
        type: 'customrecord_performance_obligation',
        filters: [['custrecord_arrangement', 'is', arrangementId]],
        columns: ['custrecord_item', 'custrecord_standalone_price']
    });

    obligationSearch.run().each((result) => {
        obligations.push({
            id: result.id,
            itemId: result.getValue({ name: 'custrecord_item' }),
            standalonePrice: parseFloat(result.getValue({ name: 'custrecord_standalone_price' }))
        });
        return true;
    });

    // Calculate total standalone selling price
    const totalStandalone = obligations.reduce((sum, obl) => sum + obl.standalonePrice, 0);

    // Allocate proportionally
    for (const obligation of obligations) {
        const allocationPercent = obligation.standalonePrice / totalStandalone;
        const allocatedAmount = totalPrice * allocationPercent;

        record.submitFields({
            type: 'customrecord_performance_obligation',
            id: obligation.id,
            values: {
                'custrecord_allocated_amount': allocatedAmount,
                'custrecord_allocation_percent': allocationPercent * 100
            }
        });
    }
}
```

## Best Practices

### ASC 606 Compliance
- Create revenue arrangement for all multi-element contracts
- Identify distinct performance obligations
- Use standalone selling prices for allocation
- Track satisfaction status for each obligation
- Document contract modifications

### Automation Triggers
- **Invoice creation** → Create revenue arrangement
- **Fulfillment** → Satisfy product obligations
- **Service completion** → Satisfy service obligations
- **Milestone completion** → Recognize milestone revenue
- **Monthly schedule** → Recognize ratable revenue

### Data Model
- Link arrangements to sales orders and invoices
- Track performance obligations separately
- Maintain recognition schedules for deferred items
- Store standalone selling prices for allocation
- Audit all status changes

## Testing Checklist

1. **Single Element** - Product invoice → Immediate recognition
2. **Multi-Element** - Product + Service → Separate obligations, allocation
3. **Subscription** - Create schedule → Monthly recognition over 12 months
4. **Milestone** - Project milestones → Recognize on completion
5. **Contract Modification** - Add items → Adjust allocation

## Related Documentation

- **[Revenue Recognition (Finance)](../finance/revenue-recognition.md)** - Detailed ASC 606 patterns
- **[Journal Entries](../finance/journal-entries.md)** - Revenue JE creation
- **[Invoicing](invoicing.md)** - Invoice creation triggers

**Oracle NetSuite:**
- Revenue Arrangements: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N3211445.html
- ASC 606 Compliance: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/bridgehead_N3046713.html

---

*ASC 606 revenue recognition patterns for order-to-cash automation*
