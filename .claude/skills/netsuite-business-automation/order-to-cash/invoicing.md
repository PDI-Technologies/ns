# Invoice Generation Automation

Automated invoice creation, billing schedules, and invoice delivery.

## Overview

Invoice automation streamlines the billing process from fulfillment to customer payment, reducing manual effort and improving cash flow.

**Invoicing Scenarios:**
- Invoice from fulfilled orders
- Recurring subscription billing
- Progress billing (milestone-based)
- Time and expense billing
- Consolidated billing (multiple orders)

**Automation Benefits:**
- Same-day invoicing after shipment
- Reduced billing errors
- Improved DSO (days sales outstanding)
- Automated invoice delivery

## Auto-Invoice from Fulfillment

### Create Invoice When Order Ships

**User Event Script (afterSubmit on Item Fulfillment):**

```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType UserEventScript
 */

define(['N/record'], (record) => {

    function afterSubmit(context) {
        if (context.type !== context.UserEventType.CREATE) {
            return;
        }

        const fulfillment = context.newRecord;
        const salesOrderId = fulfillment.getValue({ fieldId: 'createdfrom' });

        // Check if auto-invoice enabled for this customer
        const autoInvoice = checkAutoInvoiceEnabled(salesOrderId);

        if (autoInvoice) {
            createInvoiceFromFulfillment(fulfillment.id);
        }
    }

    function createInvoiceFromFulfillment(fulfillmentId) {
        const invoice = record.transform({
            fromType: record.Type.ITEM_FULFILLMENT,
            fromId: fulfillmentId,
            toType: record.Type.INVOICE,
            isDynamic: false
        });

        // Set invoice date to today
        invoice.setValue({
            fieldId: 'trandate',
            value: new Date()
        });

        // Set due date based on payment terms
        const terms = invoice.getValue({ fieldId: 'terms' });
        const dueDate = calculateDueDate(new Date(), terms);
        invoice.setValue({
            fieldId: 'duedate',
            value: dueDate
        });

        const invoiceId = invoice.save();

        log.audit({
            title: 'Auto-Invoice Created',
            details: `Fulfillment ${fulfillmentId} → Invoice ${invoiceId}`
        });

        // Send invoice to customer
        sendInvoiceEmail(invoiceId);

        return invoiceId;
    }

    return {
        afterSubmit: afterSubmit
    };
});
```

## Recurring Billing

### Subscription Invoice Generation

**Scheduled Script (monthly on 1st):**

```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType ScheduledScript
 */

define(['N/record', 'N/search'], (record, search) => {

    function execute(context) {
        // Find active subscription contracts
        const subscriptions = search.create({
            type: 'customrecord_subscription',
            filters: [
                ['custrecord_subscription_status', 'is', 'Active'],
                'AND',
                ['custrecord_next_billing_date', 'onorbefore', 'today']
            ],
            columns: [
                'custrecord_customer',
                'custrecord_monthly_amount',
                'custrecord_billing_day',
                'custrecord_subscription_items'
            ]
        }).run();

        subscriptions.each((subscription) => {
            const customerId = subscription.getValue({ name: 'custrecord_customer' });
            const amount = parseFloat(subscription.getValue({ name: 'custrecord_monthly_amount' }));

            // Create invoice
            createSubscriptionInvoice({
                subscriptionId: subscription.id,
                customerId: customerId,
                amount: amount
            });

            // Update next billing date
            updateNextBillingDate(subscription.id);

            return true;
        });
    }

    function createSubscriptionInvoice(data) {
        const invoice = record.create({
            type: record.Type.INVOICE,
            isDynamic: true
        });

        invoice.setValue({ fieldId: 'entity', value: data.customerId });
        invoice.setValue({ fieldId: 'trandate', value: new Date() });
        invoice.setValue({ fieldId: 'custbody_subscription', value: data.subscriptionId });

        // Add subscription line item
        invoice.selectNewLine({ sublistId: 'item' });
        invoice.setCurrentSublistValue({ sublistId: 'item', fieldId: 'item', value: SUBSCRIPTION_ITEM_ID });
        invoice.setCurrentSublistValue({ sublistId: 'item', fieldId: 'rate', value: data.amount });
        invoice.setCurrentSublistValue({ sublistId: 'item', fieldId: 'quantity', value: 1 });
        invoice.commitLine({ sublistId: 'item' });

        return invoice.save();
    }

    return {
        execute: execute
    };
});
```

## Progress Billing

### Milestone-Based Invoicing

```javascript
function createProgressInvoice(projectId, milestoneId) {
    const milestone = record.load({
        type: 'customrecord_project_milestone',
        id: milestoneId
    });

    const customerId = milestone.getValue({ fieldId: 'custrecord_customer' });
    const billingAmount = milestone.getValue({ fieldId: 'custrecord_billing_amount' });
    const billingPercent = milestone.getValue({ fieldId: 'custrecord_billing_percent' });

    const invoice = record.create({
        type: record.Type.INVOICE,
        isDynamic: true
    });

    invoice.setValue({ fieldId: 'entity', value: customerId });
    invoice.setValue({ fieldId: 'custbody_project', value: projectId });
    invoice.setValue({ fieldId: 'custbody_milestone', value: milestoneId });

    // Add progress billing line
    invoice.selectNewLine({ sublistId: 'item' });
    invoice.setCurrentSublistValue({ sublistId: 'item', fieldId: 'item', value: PROGRESS_BILLING_ITEM });
    invoice.setCurrentSublistValue({ sublistId: 'item', fieldId: 'description', value: `Progress billing - ${billingPercent}% complete` });
    invoice.setCurrentSublistValue({ sublistId: 'item', fieldId: 'rate', value: billingAmount });
    invoice.setCurrentSublistValue({ sublistId: 'item', fieldId: 'quantity', value: 1 });
    invoice.commitLine({ sublistId: 'item' });

    const invoiceId = invoice.save();

    // Mark milestone as billed
    record.submitFields({
        type: 'customrecord_project_milestone',
        id: milestoneId,
        values: {
            custrecord_billing_status: 'Billed',
            custrecord_invoice: invoiceId
        }
    });

    return invoiceId;
}
```

## Consolidated Billing

### Multiple Orders to Single Invoice

```javascript
function createConsolidatedInvoice(salesOrderIds) {
    if (salesOrderIds.length === 0) {
        return null;
    }

    // Get customer from first order
    const firstOrder = record.load({
        type: record.Type.SALES_ORDER,
        id: salesOrderIds[0]
    });

    const customerId = firstOrder.getValue({ fieldId: 'entity' });

    const invoice = record.create({
        type: record.Type.INVOICE,
        isDynamic: true
    });

    invoice.setValue({ fieldId: 'entity', value: customerId });
    invoice.setValue({ fieldId: 'trandate', value: new Date() });

    // Add items from all sales orders
    for (const soId of salesOrderIds) {
        const so = record.load({
            type: record.Type.SALES_ORDER,
            id: soId
        });

        const lineCount = so.getLineCount({ sublistId: 'item' });

        for (let i = 0; i < lineCount; i++) {
            invoice.selectNewLine({ sublistId: 'item' });

            invoice.setCurrentSublistValue({
                sublistId: 'item',
                fieldId: 'item',
                value: so.getSublistValue({ sublistId: 'item', fieldId: 'item', line: i })
            });

            invoice.setCurrentSublistValue({
                sublistId: 'item',
                fieldId: 'quantity',
                value: so.getSublistValue({ sublistId: 'item', fieldId: 'quantity', line: i })
            });

            invoice.setCurrentSublistValue({
                sublistId: 'item',
                fieldId: 'rate',
                value: so.getSublistValue({ sublistId: 'item', fieldId: 'rate', line: i })
            });

            invoice.setCurrentSublistValue({
                sublistId: 'item',
                fieldId: 'custcol_source_order',
                value: soId
            });

            invoice.commitLine({ sublistId: 'item' });
        }
    }

    return invoice.save();
}
```

## Invoice Delivery

### Email Invoice with PDF Attachment

```javascript
function sendInvoiceEmail(invoiceId) {
    const invoice = record.load({
        type: record.Type.INVOICE,
        id: invoiceId
    });

    const customerEmail = invoice.getText({ fieldId: 'email' });
    const invoiceNumber = invoice.getValue({ fieldId: 'tranid' });

    if (customerEmail) {
        // Render invoice as PDF
        const pdfFile = render.transaction({
            entityId: invoiceId,
            printMode: render.PrintMode.PDF
        });

        email.send({
            author: AR_SENDER_ID,
            recipients: customerEmail,
            subject: `Invoice ${invoiceNumber}`,
            body: `Please find your invoice attached.\n\nDue Date: ${invoice.getValue({ fieldId: 'duedate' })}`,
            attachments: [pdfFile],
            relatedRecords: {
                transactionId: invoiceId
            }
        });

        // Mark invoice as emailed
        record.submitFields({
            type: record.Type.INVOICE,
            id: invoiceId,
            values: {
                custbody_invoice_emailed: true,
                custbody_email_sent_date: new Date()
            }
        });
    }
}
```

## Related Documentation

- **[Sales Orders](sales-orders.md)** - Order creation and approval
- **[Fulfillment](fulfillment.md)** - Item fulfillment automation
- **[Revenue Recognition](../finance/revenue-recognition.md)** - Revenue accounting
- **[Notification Automation](../workflows/notification-automation.md)** - Email templates

**External References:**
- [NetSuite Invoice](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N303850.html)

---

*Generic invoice generation and billing automation patterns for order-to-cash processes*
