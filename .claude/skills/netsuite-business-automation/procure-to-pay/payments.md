# Vendor Payment Automation

Automated vendor payment processing, payment file generation, and early payment discount capture.

## Overview

Vendor payment automation manages the payables process from approved bills through payment execution and reconciliation.

**Payment Workflow:**
1. Vendor bills approved
2. Payment batch created
3. Early payment discounts evaluated
4. Payment file generated (ACH, wire, check)
5. Payment transmitted to bank
6. Bills marked as paid
7. Cash account reconciled

**Automation Benefits:**
- 90% reduction in manual payment processing
- Automated discount capture (2-3% savings)
- Reduced payment errors
- Improved vendor relationships

## Payment Batch Creation

### Select Bills for Payment

**Scheduled Script (weekly):**

```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType ScheduledScript
 */

define(['N/record', 'N/search'], (record, search) => {

    function execute(context) {
        // Find bills due within next 7 days
        const dueDate = new Date();
        dueDate.setDate(dueDate.getDate() + 7);

        const billsToPay = search.create({
            type: search.Type.VENDOR_BILL,
            filters: [
                ['status', 'anyof', ['VendBill:A']],  // Open
                'AND',
                ['duedate', 'onorbefore', formatDate(dueDate)],
                'AND',
                ['approvalstatus', 'is', '2']  // Approved
            ],
            columns: [
                'entity',
                'tranid',
                'amountremaining',
                'duedate',
                'terms'
            ]
        }).run();

        const payments = [];

        billsToPay.each((bill) => {
            const vendorId = bill.getValue({ name: 'entity' });
            const amountDue = parseFloat(bill.getValue({ name: 'amountremaining' }));

            // Check for early payment discount
            const discountInfo = evaluateEarlyPaymentDiscount(bill);

            if (discountInfo.eligible) {
                // Pay early to capture discount
                payments.push({
                    billId: bill.id,
                    vendorId: vendorId,
                    amount: amountDue * (1 - discountInfo.discountPercent),
                    discountAmount: amountDue * discountInfo.discountPercent,
                    paymentDate: new Date()
                });
            } else {
                // Pay on due date
                payments.push({
                    billId: bill.id,
                    vendorId: vendorId,
                    amount: amountDue,
                    discountAmount: 0,
                    paymentDate: new Date(bill.getValue({ name: 'duedate' }))
                });
            }

            return true;
        });

        // Create payment batch
        createPaymentBatch(payments);
    }

    return {
        execute: execute
    };
});
```

## Early Payment Discount

### Evaluate Discount ROI

```javascript
function evaluateEarlyPaymentDiscount(bill) {
    const terms = bill.getValue({ name: 'terms' });
    const dueDate = new Date(bill.getValue({ name: 'duedate' }));

    // Parse discount terms (e.g., "2/10 Net 30")
    const match = terms.match(/(\d+)\/(\d+)\s+Net\s+(\d+)/i);

    if (match) {
        const discountPercent = parseInt(match[1]) / 100;
        const discountDays = parseInt(match[2]);
        const netDays = parseInt(match[3]);

        // Calculate days until discount expires
        const today = new Date();
        const invoiceDate = new Date(bill.getValue({ name: 'trandate' }));
        const daysSinceInvoice = Math.floor((today - invoiceDate) / (1000 * 60 * 60 * 24));

        if (daysSinceInvoice <= discountDays) {
            // Calculate effective APR of discount
            const daysEarly = netDays - discountDays;
            const effectiveAPR = (discountPercent / (1 - discountPercent)) * (365 / daysEarly);

            // Take discount if APR > cost of capital (assume 10%)
            return {
                eligible: effectiveAPR > 0.10,
                discountPercent: discountPercent,
                effectiveAPR: effectiveAPR,
                daysRemaining: discountDays - daysSinceInvoice
            };
        }
    }

    return { eligible: false };
}
```

## Payment File Generation

### ACH Payment File (NACHA Format)

```javascript
function generateACHFile(payments) {
    const achRecords = [];

    // File header
    achRecords.push(createFileHeader());

    // Batch header
    achRecords.push(createBatchHeader(payments));

    // Payment details
    for (const payment of payments) {
        const vendor = record.load({
            type: record.Type.VENDOR,
            id: payment.vendorId
        });

        const bankAccount = vendor.getValue({ fieldId: 'custentity_bank_account' });
        const routingNumber = vendor.getValue({ fieldId: 'custentity_routing_number' });

        achRecords.push({
            recordType: '6',  // Entry detail
            transactionCode: '27',  // Debit checking
            receivingDFI: routingNumber.substring(0, 8),
            checkDigit: routingNumber.substring(8, 9),
            accountNumber: bankAccount,
            amount: Math.round(payment.amount * 100),  // In cents
            vendorName: vendor.getValue({ fieldId: 'companyname' }),
            invoiceNumber: payment.invoiceNumber
        });
    }

    // Batch control
    achRecords.push(createBatchControl(payments));

    // File control
    achRecords.push(createFileControl());

    return formatNACHAFile(achRecords);
}
```

## Payment Execution

### Create Bill Payments

```javascript
function createPaymentBatch(paymentData) {
    for (const payment of paymentData) {
        try {
            const billPayment = record.transform({
                fromType: record.Type.VENDOR_BILL,
                fromId: payment.billId,
                toType: record.Type.VENDOR_PAYMENT,
                isDynamic: true
            });

            billPayment.setValue({
                fieldId: 'trandate',
                value: payment.paymentDate
            });

            billPayment.setValue({
                fieldId: 'account',
                value: CHECKING_ACCOUNT_ID
            });

            // Apply discount if applicable
            if (payment.discountAmount > 0) {
                applyPaymentDiscount(billPayment, payment.discountAmount);
            }

            const paymentId = billPayment.save();

            log.audit({
                title: 'Payment Created',
                details: `Bill ${payment.billId} → Payment ${paymentId}, Amount: $${payment.amount}`
            });

        } catch (e) {
            log.error({
                title: 'Payment Failed',
                details: `Bill ${payment.billId}: ${e.message}`
            });
        }
    }
}
```

## Payment Methods

### ACH vs Wire vs Check

```javascript
function determinePaymentMethod(vendorId, amount) {
    const vendor = record.load({
        type: record.Type.VENDOR,
        id: vendorId
    });

    const preferredMethod = vendor.getValue({ fieldId: 'custentity_preferred_payment_method' });
    const hasACH = vendor.getValue({ fieldId: 'custentity_bank_account' });

    // Business rules
    if (amount > 10000 && preferredMethod === 'Wire') {
        return 'WIRE';
    } else if (hasACH) {
        return 'ACH';
    } else {
        return 'CHECK';
    }
}
```

## Best Practices

### Payment Validation

```javascript
function validatePayment(context) {
    const payment = context.newRecord;

    // Verify positive amount
    const amount = payment.getValue({ fieldId: 'usertotal' });
    if (amount <= 0) {
        throw error.create({
            name: 'INVALID_AMOUNT',
            message: 'Payment amount must be greater than zero'
        });
    }

    // Verify sufficient cash balance
    const account = payment.getValue({ fieldId: 'account' });
    const accountBalance = getAccountBalance(account);

    if (amount > accountBalance) {
        throw error.create({
            name: 'INSUFFICIENT_FUNDS',
            message: `Payment amount $${amount} exceeds account balance $${accountBalance}`
        });
    }
}
```

### Duplicate Payment Prevention

```javascript
function checkForDuplicatePayment(context) {
    const payment = context.newRecord;
    const vendorId = payment.getValue({ fieldId: 'entity' });
    const amount = payment.getValue({ fieldId: 'usertotal' });
    const paymentDate = payment.getValue({ fieldId: 'trandate' });

    // Search for recent payments to same vendor for same amount
    const recentPayments = search.create({
        type: search.Type.VENDOR_PAYMENT,
        filters: [
            ['entity', 'is', vendorId],
            'AND',
            ['amount', 'equalto', amount],
            'AND',
            ['trandate', 'within', 'yesterday', 'today']
        ]
    }).run().getRange({ start: 0, end: 1 });

    if (recentPayments.length > 0) {
        throw error.create({
            name: 'POSSIBLE_DUPLICATE',
            message: `Similar payment exists (ID: ${recentPayments[0].id}). Please verify not a duplicate.`
        });
    }
}
```

## Related Documentation

- **[Vendor Bills](vendor-bills.md)** - Bill processing
- **[Expense Reports](expense-reports.md)** - Reimbursement processing
- **[Reconciliation](../finance/reconciliation.md)** - Cash reconciliation

**External References:**
- [Vendor Payment](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N305775.html)

---

*Generic vendor payment automation patterns for accounts payable*
