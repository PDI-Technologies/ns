# Notification Automation

Automated email and workflow notifications for business events using NetSuite Email, Workflow, and Scheduled Scripts.

## Overview

Notification automation keeps stakeholders informed of critical business events without manual intervention.

**Common Use Cases:**
- Approval notifications (pending approval, approved, rejected)
- Transaction status changes (order fulfilled, invoice overdue)
- Threshold alerts (inventory low, budget exceeded)
- Escalation notices (overdue tasks, SLA breaches)
- Daily/weekly summary reports (open orders, pending bills)
- Error alerts (integration failures, validation errors)

**Implementation Methods:**
- Native Workflow Email Actions (no code, template-based)
- User Event Scripts with N/email module (dynamic content)
- Scheduled Scripts for batch notifications
- RESTlet-triggered notifications (external systems)

## Email Notification Patterns

### Pattern 1: Simple Transaction Email

Send email when transaction reaches specific status.

**User Event Script (afterSubmit):**

```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType UserEventScript
 */

define(['N/email', 'N/record'], (email, record) => {

    function afterSubmit(context) {
        if (context.type !== context.UserEventType.CREATE) {
            return;
        }

        const salesOrder = context.newRecord;
        const customerId = salesOrder.getValue({ fieldId: 'entity' });
        const orderTotal = salesOrder.getValue({ fieldId: 'total' });
        const orderNumber = salesOrder.getValue({ fieldId: 'tranid' });

        // Get customer email
        const customerEmail = record.load({
            type: record.Type.CUSTOMER,
            id: customerId
        }).getValue({ fieldId: 'email' });

        if (customerEmail) {
            email.send({
                author: SENDER_ID,  // Employee ID of sender
                recipients: customerEmail,
                subject: `Order Confirmation - ${orderNumber}`,
                body: `Thank you for your order.\n\nOrder Number: ${orderNumber}\nTotal: $${orderTotal}\n\nWe will send shipping confirmation when your order ships.`,
                relatedRecords: {
                    transactionId: salesOrder.id
                }
            });
        }
    }

    return {
        afterSubmit: afterSubmit
    };
});
```

### Pattern 2: Approval Notifications

Notify approver when transaction requires approval.

**User Event Script:**

```javascript
function notifyApprover(purchaseOrderId, approverId) {
    const po = record.load({
        type: record.Type.PURCHASE_ORDER,
        id: purchaseOrderId
    });

    const poNumber = po.getValue({ fieldId: 'tranid' });
    const total = po.getValue({ fieldId: 'total' });
    const vendor = po.getText({ fieldId: 'entity' });
    const memo = po.getValue({ fieldId: 'memo' });

    // Get approver email
    const approverEmail = record.load({
        type: record.Type.EMPLOYEE,
        id: approverId
    }).getValue({ fieldId: 'email' });

    // Build approval link
    const approvalLink = `https://${ACCOUNT_ID}.app.netsuite.com/app/accounting/transactions/purchord.nl?id=${purchaseOrderId}`;

    email.send({
        author: SENDER_ID,
        recipients: approverEmail,
        subject: `Purchase Order Approval Required: ${poNumber}`,
        body: `
            A purchase order requires your approval:

            PO Number: ${poNumber}
            Vendor: ${vendor}
            Amount: $${total}
            Memo: ${memo}

            Click here to review and approve: ${approvalLink}

            Please approve or reject within 2 business days.
        `,
        relatedRecords: {
            transactionId: purchaseOrderId
        }
    });
}
```

### Pattern 3: Multi-Recipient Notifications

Send to multiple stakeholders based on transaction attributes.

**Pattern:**

```javascript
function notifyStakeholders(salesOrderId) {
    const so = record.load({
        type: record.Type.SALES_ORDER,
        id: salesOrderId
    });

    const total = parseFloat(so.getValue({ fieldId: 'total' }));
    const department = so.getValue({ fieldId: 'department' });

    // Build recipient list based on business rules
    const recipients = [];

    // Always notify sales rep
    const salesRepEmail = so.getText({ fieldId: 'salesrep' });
    if (salesRepEmail) {
        recipients.push(salesRepEmail);
    }

    // Notify manager for orders > $10K
    if (total > 10000) {
        recipients.push(SALES_MANAGER_EMAIL);
    }

    // Notify department head
    const deptHeadEmail = getDepartmentHeadEmail(department);
    if (deptHeadEmail) {
        recipients.push(deptHeadEmail);
    }

    // Notify CFO for orders > $100K
    if (total > 100000) {
        recipients.push(CFO_EMAIL);
    }

    // Send notification
    email.send({
        author: SENDER_ID,
        recipients: recipients,
        subject: `High-Value Sales Order Created: ${so.getValue({ fieldId: 'tranid' })}`,
        body: buildOrderSummary(so),
        relatedRecords: {
            transactionId: salesOrderId
        }
    });
}
```

### Pattern 4: HTML Email Templates

Send formatted HTML emails with dynamic content.

**Template:**

```javascript
function sendHtmlEmail(orderId, customerEmail) {
    const order = record.load({
        type: record.Type.SALES_ORDER,
        id: orderId
    });

    const orderNumber = order.getValue({ fieldId: 'tranid' });
    const total = order.getValue({ fieldId: 'total' });

    const htmlBody = `
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; }
                .header { background-color: #0066cc; color: white; padding: 20px; }
                .content { padding: 20px; }
                .footer { background-color: #f0f0f0; padding: 10px; font-size: 12px; }
                table { border-collapse: collapse; width: 100%; }
                td { border: 1px solid #ddd; padding: 8px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Order Confirmation</h1>
            </div>
            <div class="content">
                <p>Thank you for your order!</p>
                <p><strong>Order Number:</strong> ${orderNumber}</p>
                <p><strong>Total:</strong> $${total}</p>

                <h3>Order Details</h3>
                ${buildItemTable(order)}
            </div>
            <div class="footer">
                <p>Questions? Contact support@company.com</p>
            </div>
        </body>
        </html>
    `;

    email.send({
        author: SENDER_ID,
        recipients: customerEmail,
        subject: `Order Confirmation - ${orderNumber}`,
        body: htmlBody,
        isHTML: true,
        relatedRecords: {
            transactionId: orderId
        }
    });
}

function buildItemTable(order) {
    let html = '<table><tr><th>Item</th><th>Quantity</th><th>Price</th><th>Amount</th></tr>';

    const lineCount = order.getLineCount({ sublistId: 'item' });

    for (let i = 0; i < lineCount; i++) {
        const itemName = order.getSublistText({
            sublistId: 'item',
            fieldId: 'item',
            line: i
        });
        const quantity = order.getSublistValue({
            sublistId: 'item',
            fieldId: 'quantity',
            line: i
        });
        const rate = order.getSublistValue({
            sublistId: 'item',
            fieldId: 'rate',
            line: i
        });
        const amount = order.getSublistValue({
            sublistId: 'item',
            fieldId: 'amount',
            line: i
        });

        html += `
            <tr>
                <td>${itemName}</td>
                <td>${quantity}</td>
                <td>$${rate}</td>
                <td>$${amount}</td>
            </tr>
        `;
    }

    html += '</table>';
    return html;
}
```

### Pattern 5: Email Attachments

Attach PDF invoices or reports to emails.

**Pattern:**

```javascript
function sendInvoiceWithAttachment(invoiceId, customerEmail) {
    const invoice = record.load({
        type: record.Type.INVOICE,
        id: invoiceId
    });

    const invoiceNumber = invoice.getValue({ fieldId: 'tranid' });

    // Render invoice as PDF
    const pdfFile = render.transaction({
        entityId: invoiceId,
        printMode: render.PrintMode.PDF
    });

    // Send email with PDF attachment
    email.send({
        author: SENDER_ID,
        recipients: customerEmail,
        subject: `Invoice ${invoiceNumber}`,
        body: `Please find your invoice attached.`,
        attachments: [pdfFile],
        relatedRecords: {
            transactionId: invoiceId
        }
    });
}
```

## Scheduled Notification Patterns

### Pattern 1: Daily Summary Report

Send daily summary of pending transactions.

**Scheduled Script (daily at 8 AM):**

```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType ScheduledScript
 */

define(['N/search', 'N/email'], (search, email) => {

    function execute(context) {
        // Search for open sales orders
        const openOrders = search.create({
            type: search.Type.SALES_ORDER,
            filters: [
                ['status', 'anyof', ['SalesOrd:A']],  // Pending Approval
                'AND',
                ['mainline', 'is', 'T']
            ],
            columns: [
                'tranid',
                'entity',
                'total',
                'trandate'
            ]
        }).run().getRange({ start: 0, end: 100 });

        if (openOrders.length === 0) {
            return;  // No notifications needed
        }

        // Build email body
        let body = `Daily Summary Report\n\n`;
        body += `You have ${openOrders.length} sales orders pending approval:\n\n`;

        openOrders.forEach((order) => {
            const tranid = order.getValue({ name: 'tranid' });
            const customer = order.getText({ name: 'entity' });
            const total = order.getValue({ name: 'total' });

            body += `- ${tranid}: ${customer} - $${total}\n`;
        });

        body += `\nPlease review and approve pending orders.`;

        // Send to sales managers
        email.send({
            author: SENDER_ID,
            recipients: SALES_MANAGER_EMAILS,
            subject: `Daily Sales Order Summary - ${new Date().toLocaleDateString()}`,
            body: body
        });
    }

    return {
        execute: execute
    };
});
```

### Pattern 2: Overdue Invoice Reminders

Send reminder emails for overdue invoices.

**Scheduled Script (weekly):**

```javascript
function sendOverdueReminders() {
    // Search for overdue invoices
    const overdueInvoices = search.create({
        type: search.Type.INVOICE,
        filters: [
            ['status', 'anyof', ['CustInvc:A']],  // Open
            'AND',
            ['duedate', 'before', 'today']
        ],
        columns: [
            'tranid',
            'entity',
            'email',
            'total',
            'amountremaining',
            'duedate'
        ]
    }).run();

    overdueInvoices.each((invoice) => {
        const customerEmail = invoice.getValue({ name: 'email' });

        if (customerEmail) {
            const tranid = invoice.getValue({ name: 'tranid' });
            const total = invoice.getValue({ name: 'total' });
            const remaining = invoice.getValue({ name: 'amountremaining' });
            const dueDate = invoice.getValue({ name: 'duedate' });

            email.send({
                author: SENDER_ID,
                recipients: customerEmail,
                subject: `Payment Reminder: Invoice ${tranid} is Overdue`,
                body: `
                    Your invoice is overdue. Please submit payment at your earliest convenience.

                    Invoice Number: ${tranid}
                    Due Date: ${dueDate}
                    Amount Due: $${remaining}

                    If you have already submitted payment, please disregard this notice.
                `
            });
        }

        return true;  // Continue iteration
    });
}
```

### Pattern 3: Threshold Alerts

Send alerts when metrics exceed thresholds.

**Example: Low Inventory Alert**

```javascript
function checkInventoryLevels() {
    // Search for items below reorder point
    const lowStockItems = search.create({
        type: search.Type.ITEM,
        filters: [
            ['quantityavailable', 'lessthan', 'reorderpoint'],
            'AND',
            ['isinactive', 'is', 'F']
        ],
        columns: [
            'itemid',
            'displayname',
            'quantityavailable',
            'reorderpoint',
            'preferredvendor'
        ]
    }).run().getRange({ start: 0, end: 50 });

    if (lowStockItems.length === 0) {
        return;
    }

    // Build alert email
    let body = `INVENTORY ALERT: ${lowStockItems.length} items below reorder point\n\n`;

    lowStockItems.forEach((item) => {
        const itemName = item.getValue({ name: 'displayname' });
        const onHand = item.getValue({ name: 'quantityavailable' });
        const reorder = item.getValue({ name: 'reorderpoint' });
        const vendor = item.getText({ name: 'preferredvendor' });

        body += `- ${itemName}: ${onHand} on hand (reorder at ${reorder}) - Vendor: ${vendor}\n`;
    });

    email.send({
        author: SENDER_ID,
        recipients: [PURCHASING_MANAGER_EMAIL, WAREHOUSE_MANAGER_EMAIL],
        subject: `Inventory Alert: ${lowStockItems.length} Items Below Reorder Point`,
        body: body
    });
}
```

## Workflow Email Actions

**Native Workflow Configuration:**
1. Navigate to Customization → Workflow → Workflows → New
2. Add State with Email Action
3. Configure email template with merge fields

**Merge Fields:**
```
{entity.companyname} - Customer name
{tranid} - Transaction number
{total} - Transaction total
{memo} - Transaction memo
{approvalstatus} - Approval status
```

**Example Workflow Email:**
```
Subject: Order {tranid} Approved

Body:
Dear {entity.companyname},

Your order {tranid} for ${total} has been approved and is being processed.

Expected ship date: {expectedshipdate}

Thank you for your business!
```

## Best Practices

### Email Limits

**NetSuite Email Limits:**
- 10 emails per script execution (User Event)
- 20 emails per script execution (Scheduled, Map/Reduce)
- 5,000 emails per day (account-wide)

**Strategies:**
- Batch notifications in scheduled scripts
- Use BCC for multiple recipients (single email)
- Queue emails when near limit

### Error Handling

```javascript
function sendEmailSafely(recipient, subject, body) {
    try {
        email.send({
            author: SENDER_ID,
            recipients: recipient,
            subject: subject,
            body: body
        });

        log.audit({
            title: 'Email Sent',
            details: `To: ${recipient}, Subject: ${subject}`
        });

    } catch (e) {
        log.error({
            title: 'Email Failed',
            details: `To: ${recipient}, Error: ${e.message}`
        });

        // Fallback: Log notification for manual follow-up
        createNotificationRecord(recipient, subject, body, e.message);
    }
}
```

### Email Validation

```javascript
function isValidEmail(email) {
    if (!email) return false;

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function getValidRecipients(emailList) {
    return emailList.filter(email => isValidEmail(email));
}
```

### Personalization

```javascript
function personalizeEmail(template, customer) {
    return template
        .replace('{name}', customer.companyname || 'Customer')
        .replace('{contact}', customer.firstname || '')
        .replace('{account}', customer.accountnumber || '');
}
```

### Unsubscribe Handling

```javascript
function shouldSendEmail(customerId) {
    const customer = record.load({
        type: record.Type.CUSTOMER,
        id: customerId
    });

    // Check unsubscribe flag
    const unsubscribed = customer.getValue({ fieldId: 'custentity_email_unsubscribe' });

    return !unsubscribed;
}
```

## Related Documentation

- **[Approval Routing](approval-routing.md)** - Trigger notifications on approval events
- **[Custom Workflows](custom-workflows.md)** - Workflow Action Scripts with notifications
- **[Sales Orders](../order-to-cash/sales-orders.md)** - Order confirmation emails

**External References:**
- [N/email Module](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4296361146.html)
- [Workflow Email Actions](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N286989.html)

---

*Generic notification automation patterns for NetSuite business events*
