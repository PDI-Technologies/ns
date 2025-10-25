# Expense Report Automation

Automated expense report submission, approval, and reimbursement processing.

## Overview

Expense report automation streamlines employee expense submissions from receipt capture through reimbursement payment.

**Expense Workflow:**
1. Employee submits expense report
2. Receipts attached (mobile app/email)
3. Policy compliance validation
4. Manager approval
5. Accounting review (for large amounts)
6. Post to GL
7. Reimbursement payment processed

**Automation Benefits:**
- 50% faster reimbursement cycle
- Reduced policy violations
- Automated mileage calculations
- Mobile receipt capture

## Expense Validation

### Policy Compliance Checks

**User Event Script (beforeSubmit):**

```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType UserEventScript
 */

define(['N/record', 'N/error'], (record, error) => {

    function beforeSubmit(context) {
        if (context.type !== context.UserEventType.CREATE &&
            context.type !== context.UserEventType.EDIT) {
            return;
        }

        const expenseReport = context.newRecord;
        const violations = [];

        // Check each expense line
        const lineCount = expenseReport.getLineCount({ sublistId: 'expense' });

        for (let i = 0; i < lineCount; i++) {
            const category = expenseReport.getSublistValue({
                sublistId: 'expense',
                fieldId: 'category',
                line: i
            });

            const amount = expenseReport.getSublistValue({
                sublistId: 'expense',
                fieldId: 'amount',
                line: i
            });

            const receipt = expenseReport.getSublistValue({
                sublistId: 'expense',
                fieldId: 'custcol_receipt_attached',
                line: i
            });

            // Check policy limits
            const policyLimit = getPolicyLimit(category);

            if (amount > policyLimit) {
                violations.push(`${category}: $${amount} exceeds limit of $${policyLimit}`);
            }

            // Check receipt requirement
            if (amount > 25 && !receipt) {
                violations.push(`${category}: Receipt required for amounts over $25`);
            }
        }

        if (violations.length > 0) {
            expenseReport.setValue({
                fieldId: 'custbody_policy_violations',
                value: violations.join('\n')
            });

            expenseReport.setValue({
                fieldId: 'custbody_requires_review',
                value: true
            });
        }
    }

    function getPolicyLimit(category) {
        const POLICY_LIMITS = {
            'Meals': 75,
            'Lodging': 250,
            'Airfare': 1000,
            'Car Rental': 100,
            'Entertainment': 150
        };

        return POLICY_LIMITS[category] || 100;
    }

    return {
        beforeSubmit: beforeSubmit
    };
});
```

## Mileage Calculation

### Auto-Calculate Mileage Reimbursement

```javascript
function calculateMileageExpense(fromAddress, toAddress, roundTrip = false) {
    // Call mapping API to get distance
    const distance = getDistance(fromAddress, toAddress);

    const mileage = roundTrip ? distance * 2 : distance;

    // IRS standard mileage rate (update annually)
    const mileageRate = 0.67;  // 2024 rate: $0.67/mile

    const reimbursement = mileage * mileageRate;

    return {
        miles: mileage,
        rate: mileageRate,
        amount: reimbursement
    };
}

function addMileageExpenseLine(expenseReport, mileageData) {
    expenseReport.selectNewLine({ sublistId: 'expense' });

    expenseReport.setCurrentSublistValue({
        sublistId: 'expense',
        fieldId: 'category',
        value: MILEAGE_CATEGORY_ID
    });

    expenseReport.setCurrentSublistValue({
        sublistId: 'expense',
        fieldId: 'amount',
        value: mileageData.amount
    });

    expenseReport.setCurrentSublistValue({
        sublistId: 'expense',
        fieldId: 'memo',
        value: `Mileage: ${mileageData.miles} miles @ $${mileageData.rate}/mile`
    });

    expenseReport.commitLine({ sublistId: 'expense' });
}
```

## Receipt Management

### Mobile Receipt Capture

**RESTlet for mobile app:**

```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType Restlet
 */

define(['N/file', 'N/record'], (file, record) => {

    function post(requestBody) {
        const { employeeId, receiptImage, expenseData } = requestBody;

        // Save receipt image to file cabinet
        const receiptFile = file.create({
            name: `receipt_${expenseData.date}_${expenseData.merchant}.jpg`,
            fileType: file.Type.JPGIMAGE,
            contents: receiptImage,
            folder: RECEIPT_FOLDER_ID
        });

        const receiptFileId = receiptFile.save();

        // Create expense report
        const expenseReport = record.create({
            type: record.Type.EXPENSE_REPORT,
            isDynamic: true
        });

        expenseReport.setValue({ fieldId: 'entity', value: employeeId });
        expenseReport.setValue({ fieldId: 'trandate', value: new Date(expenseData.date) });

        // Add expense line
        expenseReport.selectNewLine({ sublistId: 'expense' });
        expenseReport.setCurrentSublistValue({ sublistId: 'expense', fieldId: 'category', value: expenseData.category });
        expenseReport.setCurrentSublistValue({ sublistId: 'expense', fieldId: 'amount', value: expenseData.amount });
        expenseReport.setCurrentSublistValue({ sublistId: 'expense', fieldId: 'memo', value: expenseData.merchant });
        expenseReport.setCurrentSublistValue({ sublistId: 'expense', fieldId: 'custcol_receipt_file', value: receiptFileId });
        expenseReport.commitLine({ sublistId: 'expense' });

        const expenseReportId = expenseReport.save();

        return {
            success: true,
            expenseReportId: expenseReportId,
            receiptFileId: receiptFileId
        };
    }

    return {
        post: post
    };
});
```

## Approval and Reimbursement

### Auto-Approve Under Threshold

```javascript
function afterSubmit(context) {
    if (context.type !== context.UserEventType.CREATE) {
        return;
    }

    const expenseReport = context.newRecord;
    const total = expenseReport.getValue({ fieldId: 'total' });

    // Auto-approve expenses under $100
    if (total < 100) {
        record.submitFields({
            type: record.Type.EXPENSE_REPORT,
            id: expenseReport.id,
            values: {
                approvalstatus: 2,  // Approved
                custbody_auto_approved: true
            }
        });

        // Schedule for payment
        scheduleReimbursement(expenseReport.id);
    } else {
        // Route to manager for approval
        routeForApproval(expenseReport.id);
    }
}
```

### Create Reimbursement Check

```javascript
function createReimbursementCheck(expenseReportId) {
    const expenseReport = record.load({
        type: record.Type.EXPENSE_REPORT,
        id: expenseReportId
    });

    const employeeId = expenseReport.getValue({ fieldId: 'entity' });
    const total = expenseReport.getValue({ fieldId: 'total' });

    // Create vendor bill for reimbursement (employee as vendor)
    const reimbursement = record.create({
        type: record.Type.VENDOR_BILL,
        isDynamic: false
    });

    reimbursement.setValue({ fieldId: 'entity', value: employeeId });
    reimbursement.setValue({ fieldId: 'trandate', value: new Date() });
    reimbursement.setValue({ fieldId: 'custbody_expense_report', value: expenseReportId });

    const reimbursementId = reimbursement.save();

    return reimbursementId;
}
```

## Best Practices

### Duplicate Detection

```javascript
function checkForDuplicateExpense(context) {
    const expense = context.newRecord;
    const employee = expense.getValue({ fieldId: 'entity' });

    // Get first expense line details
    const merchant = expense.getSublistValue({ sublistId: 'expense', fieldId: 'memo', line: 0 });
    const amount = expense.getSublistValue({ sublistId: 'expense', fieldId: 'amount', line: 0 });
    const date = expense.getSublistValue({ sublistId: 'expense', fieldId: 'expensedate', line: 0 });

    // Search for recent duplicates
    const duplicates = search.create({
        type: search.Type.EXPENSE_REPORT,
        filters: [
            ['entity', 'is', employee],
            'AND',
            ['expense.memo', 'is', merchant],
            'AND',
            ['expense.amount', 'equalto', amount],
            'AND',
            ['expense.expensedate', 'on', date]
        ]
    }).run().getRange({ start: 0, end: 1 });

    if (duplicates.length > 0) {
        expense.setValue({
            fieldId: 'custbody_possible_duplicate',
            value: true
        });
    }
}
```

## Related Documentation

- **[Approval Routing](../workflows/approval-routing.md)** - Expense approval workflows
- **[Payments](payments.md)** - Reimbursement payments
- **[Notification Automation](../workflows/notification-automation.md)** - Approval notifications

**External References:**
- [Expense Report](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N303250.html)

---

*Generic expense report automation patterns for employee reimbursement*
