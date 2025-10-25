# Customer Payment Processing

Automated customer payment application, cash receipt processing, and credit memo handling.

## Overview

Payment processing automation ensures customer payments are accurately applied to invoices, reducing manual effort and improving cash application accuracy.

**Payment Workflows:**
- Apply payment to open invoices
- Handle overpayments and underpayments
- Process credit memos
- Handle payment discounts
- Bank deposit automation
- Unapplied cash tracking

**Automation Benefits:**
- 70% faster cash application
- Reduced application errors
- Improved AR accuracy
- Real-time cash visibility

## Payment Application

### Auto-Apply Payment to Invoices

**User Event Script (afterSubmit on Customer Payment):**

```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType UserEventScript
 */

define(['N/record', 'N/search'], (record, search) => {

    function afterSubmit(context) {
        if (context.type !== context.UserEventType.CREATE) {
            return;
        }

        const payment = context.newRecord;
        const customerId = payment.getValue({ fieldId: 'customer' });
        const paymentAmount = payment.getValue({ fieldId: 'payment' });

        // Find open invoices for customer (oldest first)
        const openInvoices = search.create({
            type: search.Type.INVOICE,
            filters: [
                ['entity', 'is', customerId],
                'AND',
                ['status', 'anyof', ['CustInvc:A']],  // Open
                'AND',
                ['amountremaining', 'greaterthan', '0']
            ],
            columns: [
                'internalid',
                'tranid',
                'amountremaining',
                'duedate'
            ]
        }).run().getRange({ start: 0, end: 100 });

        // Apply payment to invoices
        applyPaymentToInvoices(payment.id, openInvoices, paymentAmount);
    }

    function applyPaymentToInvoices(paymentId, invoices, paymentAmount) {
        const payment = record.load({
            type: record.Type.CUSTOMER_PAYMENT,
            id: paymentId,
            isDynamic: true
        });

        let remainingPayment = paymentAmount;

        for (const invoice of invoices) {
            if (remainingPayment <= 0) break;

            const amountDue = parseFloat(invoice.getValue({ name: 'amountremaining' }));
            const applyAmount = Math.min(remainingPayment, amountDue);

            // Find invoice line in payment
            const lineCount = payment.getLineCount({ sublistId: 'apply' });

            for (let i = 0; i < lineCount; i++) {
                const applyInternalId = payment.getSublistValue({
                    sublistId: 'apply',
                    fieldId: 'internalid',
                    line: i
                });

                if (applyInternalId === invoice.id) {
                    payment.selectLine({ sublistId: 'apply', line: i });
                    payment.setCurrentSublistValue({
                        sublistId: 'apply',
                        fieldId: 'apply',
                        value: true
                    });
                    payment.setCurrentSublistValue({
                        sublistId: 'apply',
                        fieldId: 'amount',
                        value: applyAmount
                    });
                    payment.commitLine({ sublistId: 'apply' });

                    remainingPayment -= applyAmount;
                    break;
                }
            }
        }

        payment.save();

        // Handle unapplied amount
        if (remainingPayment > 0.01) {
            createUnappliedCashRecord(paymentId, remainingPayment);
        }
    }

    return {
        afterSubmit: afterSubmit
    };
});
```

## Payment Matching

### Lockbox File Import

Process bank lockbox files to create customer payments.

**Scheduled Script:**

```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType ScheduledScript
 */

define(['N/file', 'N/record', 'N/search'], (file, record, search) => {

    function execute(context) {
        // Load lockbox file from file cabinet
        const lockboxFile = file.load({ id: LOCKBOX_FILE_ID });
        const lockboxData = parseBAI2Format(lockboxFile.getContents());

        for (const paymentData of lockboxData.payments) {
            // Find customer by account number or invoice number
            const customerId = findCustomer(paymentData.accountNumber, paymentData.invoiceRef);

            if (customerId) {
                createCustomerPayment({
                    customerId: customerId,
                    amount: paymentData.amount,
                    paymentMethod: paymentData.paymentMethod,
                    referenceNumber: paymentData.checkNumber || paymentData.ref,
                    bankAccount: lockboxData.bankAccount
                });
            } else {
                // Log unmatched payment
                logUnmatchedPayment(paymentData);
            }
        }
    }

    function createCustomerPayment(data) {
        const payment = record.create({
            type: record.Type.CUSTOMER_PAYMENT,
            isDynamic: true
        });

        payment.setValue({ fieldId: 'customer', value: data.customerId });
        payment.setValue({ fieldId: 'payment', value: data.amount });
        payment.setValue({ fieldId: 'paymentmethod', value: data.paymentMethod });
        payment.setValue({ fieldId: 'trandate', value: new Date() });
        payment.setValue({ fieldId: 'account', value: data.bankAccount });

        if (data.referenceNumber) {
            payment.setValue({ fieldId: 'checknumber', value: data.referenceNumber });
        }

        return payment.save();
    }

    return {
        execute: execute
    };
});
```

## Credit Memo Handling

### Auto-Apply Credit Memos

```javascript
function applyCreditMemoToInvoices(creditMemoId) {
    const creditMemo = record.load({
        type: record.Type.CREDIT_MEMO,
        id: creditMemoId,
        isDynamic: true
    });

    const customerId = creditMemo.getValue({ fieldId: 'entity' });
    const creditAmount = creditMemo.getValue({ fieldId: 'total' });

    // Find open invoices
    const openInvoices = search.create({
        type: search.Type.INVOICE,
        filters: [
            ['entity', 'is', customerId],
            'AND',
            ['status', 'anyof', ['CustInvc:A']],
            'AND',
            ['amountremaining', 'greaterthan', '0']
        ],
        columns: ['internalid', 'amountremaining']
    }).run().getRange({ start: 0, end: 10 });

    let remainingCredit = creditAmount;

    // Apply credit to invoices
    for (const invoice of openInvoices) {
        if (remainingCredit <= 0) break;

        const amountDue = parseFloat(invoice.getValue({ name: 'amountremaining' }));
        const applyAmount = Math.min(remainingCredit, amountDue);

        // Find and select invoice line
        const lineCount = creditMemo.getLineCount({ sublistId: 'apply' });
        for (let i = 0; i < lineCount; i++) {
            const applyId = creditMemo.getSublistValue({
                sublistId: 'apply',
                fieldId: 'internalid',
                line: i
            });

            if (applyId === invoice.id) {
                creditMemo.selectLine({ sublistId: 'apply', line: i });
                creditMemo.setCurrentSublistValue({ sublistId: 'apply', fieldId: 'apply', value: true });
                creditMemo.setCurrentSublistValue({ sublistId: 'apply', fieldId: 'amount', value: applyAmount });
                creditMemo.commitLine({ sublistId: 'apply' });

                remainingCredit -= applyAmount;
                break;
            }
        }
    }

    creditMemo.save();
}
```

## Payment Discounts

### Early Payment Discount Application

```javascript
function applyEarlyPaymentDiscount(paymentId, invoiceId) {
    const invoice = record.load({
        type: record.Type.INVOICE,
        id: invoiceId
    });

    const terms = invoice.getValue({ fieldId: 'terms' });
    const invoiceDate = invoice.getValue({ fieldId: 'trandate' });
    const paymentDate = new Date();

    // Parse discount terms (e.g., "2/10 Net 30")
    const discountInfo = parseDiscountTerms(terms);

    if (discountInfo) {
        const daysSinceInvoice = Math.floor(
            (paymentDate - new Date(invoiceDate)) / (1000 * 60 * 60 * 24)
        );

        if (daysSinceInvoice <= discountInfo.discountDays) {
            // Eligible for discount
            const invoiceTotal = invoice.getValue({ fieldId: 'total' });
            const discountAmount = invoiceTotal * (discountInfo.discountPercent / 100);

            // Create credit memo for discount
            const creditMemo = record.create({
                type: record.Type.CREDIT_MEMO,
                isDynamic: true
            });

            creditMemo.setValue({ fieldId: 'entity', value: invoice.getValue({ fieldId: 'entity' }) });
            creditMemo.setValue({ fieldId: 'custbody_discount_invoice', value: invoiceId });
            creditMemo.setValue({ fieldId: 'memo', value: `Early payment discount - ${discountInfo.discountPercent}%` });

            // Add discount line
            creditMemo.selectNewLine({ sublistId: 'item' });
            creditMemo.setCurrentSublistValue({ sublistId: 'item', fieldId: 'item', value: DISCOUNT_ITEM });
            creditMemo.setCurrentSublistValue({ sublistId: 'item', fieldId: 'rate', value: discountAmount });
            creditMemo.setCurrentSublistValue({ sublistId: 'item', fieldId: 'quantity', value: 1 });
            creditMemo.commitLine({ sublistId: 'item' });

            const creditMemoId = creditMemo.save();

            // Auto-apply credit memo to invoice
            applyCreditMemoToInvoices(creditMemoId);

            return { discountApplied: true, discountAmount: discountAmount, creditMemoId: creditMemoId };
        }
    }

    return { discountApplied: false };
}
```

## Best Practices

### Payment Validation

```javascript
function validatePayment(context) {
    const payment = context.newRecord;
    const paymentAmount = payment.getValue({ fieldId: 'payment' });

    // Verify payment amount is positive
    if (paymentAmount <= 0) {
        throw error.create({
            name: 'INVALID_PAYMENT_AMOUNT',
            message: 'Payment amount must be greater than zero'
        });
    }

    // Verify customer is active
    const customerId = payment.getValue({ fieldId: 'customer' });
    const customerStatus = search.lookupFields({
        type: search.Type.CUSTOMER,
        id: customerId,
        columns: ['isinactive']
    }).isinactive;

    if (customerStatus) {
        throw error.create({
            name: 'INACTIVE_CUSTOMER',
            message: 'Cannot process payment for inactive customer'
        });
    }
}
```

### Unapplied Cash Tracking

```javascript
function createUnappliedCashRecord(paymentId, unappliedAmount) {
    // Create custom record to track unapplied cash
    const unapplied = record.create({
        type: 'customrecord_unapplied_cash'
    });

    unapplied.setValue({ fieldId: 'custrecord_payment', value: paymentId });
    unapplied.setValue({ fieldId: 'custrecord_amount', value: unappliedAmount });
    unapplied.setValue({ fieldId: 'custrecord_date', value: new Date() });

    unapplied.save();

    // Alert AR team
    sendUnappliedCashAlert(paymentId, unappliedAmount);
}
```

## Related Documentation

- **[Invoicing](invoicing.md)** - Invoice generation
- **[Sales Orders](sales-orders.md)** - Order management
- **[Reconciliation](../finance/reconciliation.md)** - Cash reconciliation

**External References:**
- [Customer Payment](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N304550.html)

---

*Generic customer payment processing patterns for order-to-cash workflows*
