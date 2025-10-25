# Period Close Automation

Automated month-end and period-end close processes including accruals, deferrals, allocations, and reconciliations.

## Overview

Period close automation reduces manual effort and ensures consistency in month-end, quarter-end, and year-end financial processes.

**Common Close Tasks:**
- Accrual journal entries (expenses, revenue)
- Deferral adjustments
- Cost allocations (overhead, shared services)
- Depreciation calculations
- Inventory adjustments
- Reconciliations (bank, intercompany, AR/AP)
- Financial statement preparation

**Automation Benefits:**
- 50-70% time reduction in close cycle
- Improved accuracy (eliminate manual errors)
- Audit trail and compliance
- Faster financial reporting

**Typical Timeline:**
- Manual close: 5-10 business days
- Automated close: 1-3 business days

## Accrual Automation

### Expense Accruals

Automatically accrue unpaid expenses at month-end.

**Scheduled Script (last day of month):**

```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType ScheduledScript
 */

define(['N/record', 'N/search', 'N/runtime'], (record, search, runtime) => {

    function execute(context) {
        const currentPeriod = getCurrentAccountingPeriod();

        // Find unpaid vendor bills for current period
        const unpaidBills = search.create({
            type: search.Type.VENDOR_BILL,
            filters: [
                ['status', 'anyof', ['VendBill:A']],  // Open
                'AND',
                ['trandate', 'within', currentPeriod.startDate, currentPeriod.endDate]
            ],
            columns: [
                'tranid',
                'entity',
                'amount',
                'account',
                'department',
                'class',
                'location'
            ]
        }).run();

        unpaidBills.each((bill) => {
            const accrualAmount = parseFloat(bill.getValue({ name: 'amount' }));

            // Create accrual journal entry
            createAccrualJE({
                period: currentPeriod.id,
                amount: accrualAmount,
                expenseAccount: bill.getValue({ name: 'account' }),
                department: bill.getValue({ name: 'department' }),
                class: bill.getValue({ name: 'class' }),
                location: bill.getValue({ name: 'location' }),
                memo: `Accrual for ${bill.getValue({ name: 'tranid' })}`,
                reversalDate: currentPeriod.nextPeriodStart
            });

            return true;  // Continue iteration
        });
    }

    function createAccrualJE(accrualData) {
        const je = record.create({
            type: record.Type.JOURNAL_ENTRY,
            isDynamic: true
        });

        je.setValue({ fieldId: 'trandate', value: accrualData.period.endDate });
        je.setValue({ fieldId: 'postingperiod', value: accrualData.period.id });
        je.setValue({ fieldId: 'memo', value: accrualData.memo });
        je.setValue({ fieldId: 'custbody_auto_reverse', value: true });
        je.setValue({ fieldId: 'custbody_reversal_date', value: accrualData.reversalDate });

        // Debit: Expense
        je.selectNewLine({ sublistId: 'line' });
        je.setCurrentSublistValue({ sublistId: 'line', fieldId: 'account', value: accrualData.expenseAccount });
        je.setCurrentSublistValue({ sublistId: 'line', fieldId: 'debit', value: accrualData.amount });
        je.setCurrentSublistValue({ sublistId: 'line', fieldId: 'department', value: accrualData.department });
        je.commitLine({ sublistId: 'line' });

        // Credit: Accrued Expenses
        je.selectNewLine({ sublistId: 'line' });
        je.setCurrentSublistValue({ sublistId: 'line', fieldId: 'account', value: ACCRUED_EXPENSES_ACCOUNT });
        je.setCurrentSublistValue({ sublistId: 'line', fieldId: 'credit', value: accrualData.amount });
        je.commitLine({ sublistId: 'line' });

        return je.save();
    }

    return {
        execute: execute
    };
});
```

### Revenue Accruals

```javascript
function accrueUnbilledRevenue(periodId) {
    // Find completed but unbilled work
    const unbilledTime = search.create({
        type: search.Type.TIME_BILL,
        filters: [
            ['isbillable', 'is', 'T'],
            'AND',
            ['billingtransaction', 'anyof', '@NONE@'],  // Not yet billed
            'AND',
            ['trandate', 'within', periodId]
        ],
        columns: [
            search.createColumn({
                name: 'hours',
                summary: search.Summary.SUM
            }),
            search.createColumn({
                name: 'rate',
                summary: search.Summary.AVG
            }),
            'customer',
            'class'
        ]
    }).run();

    unbilledTime.each((result) => {
        const hours = parseFloat(result.getValue({ name: 'hours', summary: search.Summary.SUM }));
        const rate = parseFloat(result.getValue({ name: 'rate', summary: search.Summary.AVG }));
        const unbilledAmount = hours * rate;

        if (unbilledAmount > 0) {
            createUnbilledRevenueJE({
                amount: unbilledAmount,
                customer: result.getValue({ name: 'customer' }),
                class: result.getValue({ name: 'class' })
            });
        }

        return true;
    });
}
```

## Deferral Automation

### Revenue Deferrals

Defer revenue for multi-period contracts.

```javascript
function createRevenueDeferralSchedule(invoiceId, deferralPeriods) {
    const invoice = record.load({
        type: record.Type.INVOICE,
        id: invoiceId
    });

    const totalAmount = invoice.getValue({ fieldId: 'total' });
    const monthlyRecognition = totalAmount / deferralPeriods;

    // Create deferral journal entry (initial)
    const deferralJE = record.create({
        type: record.Type.JOURNAL_ENTRY,
        isDynamic: true
    });

    // Debit: Deferred Revenue
    deferralJE.selectNewLine({ sublistId: 'line' });
    deferralJE.setCurrentSublistValue({ sublistId: 'line', fieldId: 'account', value: DEFERRED_REVENUE_ACCOUNT });
    deferralJE.setCurrentSublistValue({ sublistId: 'line', fieldId: 'debit', value: totalAmount });
    deferralJE.commitLine({ sublistId: 'line' });

    // Credit: Revenue
    deferralJE.selectNewLine({ sublistId: 'line' });
    deferralJE.setCurrentSublistValue({ sublistId: 'line', fieldId: 'account', value: REVENUE_ACCOUNT });
    deferralJE.setCurrentSublistValue({ sublistId: 'line', fieldId: 'credit', value: totalAmount });
    deferralJE.commitLine({ sublistId: 'line' });

    deferralJE.save();

    // Create monthly recognition schedule
    for (let month = 1; month <= deferralPeriods; month++) {
        createMonthlyRecognitionJE({
            amount: monthlyRecognition,
            month: month,
            totalMonths: deferralPeriods,
            invoiceId: invoiceId
        });
    }
}
```

## Cost Allocation

### Overhead Allocation

Allocate shared costs to departments.

```javascript
function allocateOverheadCosts(periodId) {
    // Get total overhead costs for period
    const overheadTotal = calculateOverheadTotal(periodId);

    // Get allocation basis (e.g., headcount by department)
    const deptHeadcount = getDepartmentHeadcount();
    const totalHeadcount = Object.values(deptHeadcount).reduce((sum, count) => sum + count, 0);

    const allocations = [];

    for (const [deptId, headcount] of Object.entries(deptHeadcount)) {
        const allocationPct = headcount / totalHeadcount;
        const allocationAmount = overheadTotal * allocationPct;

        allocations.push({
            department: deptId,
            amount: allocationAmount,
            basis: `${headcount} employees (${(allocationPct * 100).toFixed(1)}%)`
        });
    }

    // Create allocation journal entry
    createAllocationJE(periodId, allocations);
}

function createAllocationJE(periodId, allocations) {
    const je = record.create({
        type: record.Type.JOURNAL_ENTRY,
        isDynamic: true
    });

    je.setValue({ fieldId: 'postingperiod', value: periodId });
    je.setValue({ fieldId: 'memo', value: 'Overhead cost allocation' });

    // Credit: Overhead clearing account (total)
    const totalAllocation = allocations.reduce((sum, alloc) => sum + alloc.amount, 0);
    je.selectNewLine({ sublistId: 'line' });
    je.setCurrentSublistValue({ sublistId: 'line', fieldId: 'account', value: OVERHEAD_CLEARING_ACCOUNT });
    je.setCurrentSublistValue({ sublistId: 'line', fieldId: 'credit', value: totalAllocation });
    je.commitLine({ sublistId: 'line' });

    // Debit: Department expense accounts
    for (const allocation of allocations) {
        je.selectNewLine({ sublistId: 'line' });
        je.setCurrentSublistValue({ sublistId: 'line', fieldId: 'account', value: ALLOCATED_OVERHEAD_ACCOUNT });
        je.setCurrentSublistValue({ sublistId: 'line', fieldId: 'debit', value: allocation.amount });
        je.setCurrentSublistValue({ sublistId: 'line', fieldId: 'department', value: allocation.department });
        je.setCurrentSublistValue({ sublistId: 'line', fieldId: 'memo', value: allocation.basis });
        je.commitLine({ sublistId: 'line' });
    }

    je.save();
}
```

## Depreciation

### Automated Depreciation Entries

```javascript
function calculateDepreciation(periodId) {
    // Find all depreciable assets
    const assets = search.create({
        type: 'fixedasset',
        filters: [
            ['isdepreciated', 'is', 'T'],
            'AND',
            ['isinactive', 'is', 'F']
        ],
        columns: [
            'assetid',
            'cost',
            'deprecmethod',
            'lifetimeuse',
            'purchasedate',
            'assetacct',
            'accumdepr'
        ]
    }).run();

    const depreciationEntries = [];

    assets.each((asset) => {
        const cost = parseFloat(asset.getValue({ name: 'cost' }));
        const lifetimeMonths = parseInt(asset.getValue({ name: 'lifetimeuse' }));
        const monthlyDepreciation = cost / lifetimeMonths;

        depreciationEntries.push({
            assetId: asset.getValue({ name: 'assetid' }),
            amount: monthlyDepreciation,
            assetAccount: asset.getValue({ name: 'assetacct' }),
            accumDepr: asset.getValue({ name: 'accumdepr' })
        });

        return true;
    });

    // Create batch depreciation journal entry
    createDepreciationJE(periodId, depreciationEntries);
}
```

## Period Locking

### Automated Period Lock

```javascript
function lockPeriod(periodId) {
    // Verify all close tasks complete
    const pendingTasks = checkCloseTasksStatus(periodId);

    if (pendingTasks.length > 0) {
        throw error.create({
            name: 'INCOMPLETE_CLOSE',
            message: `Cannot lock period. Pending tasks: ${pendingTasks.join(', ')}`
        });
    }

    // Lock accounting period
    record.submitFields({
        type: record.Type.ACCOUNTING_PERIOD,
        id: periodId,
        values: {
            islocked: true,
            custrecord_locked_date: new Date(),
            custrecord_locked_by: runtime.getCurrentUser().id
        }
    });

    // Send notification
    notifyPeriodLocked(periodId);
}

function checkCloseTasksStatus(periodId) {
    const requiredTasks = [
        'Accruals Posted',
        'Deferrals Processed',
        'Allocations Complete',
        'Depreciation Calculated',
        'Bank Reconciled',
        'AR/AP Reconciled'
    ];

    const completedTasks = getCompletedTasks(periodId);
    return requiredTasks.filter(task => !completedTasks.includes(task));
}
```

## Close Checklist Automation

### Tracking Close Progress

```javascript
/**
 * Custom Record: customrecord_close_checklist_item
 */
function initializeCloseChecklist(periodId) {
    const tasks = [
        { name: 'Run Bank Import', order: 1, assignee: ACCOUNTING_MANAGER },
        { name: 'Post Accrual JEs', order: 2, assignee: CONTROLLER },
        { name: 'Process Deferrals', order: 3, assignee: CONTROLLER },
        { name: 'Allocate Overhead', order: 4, assignee: CONTROLLER },
        { name: 'Calculate Depreciation', order: 5, assignee: ACCOUNTING_MANAGER },
        { name: 'Reconcile Bank Accounts', order: 6, assignee: ACCOUNTING_MANAGER },
        { name: 'Reconcile AR', order: 7, assignee: AR_SPECIALIST },
        { name: 'Reconcile AP', order: 8, assignee: AP_SPECIALIST },
        { name: 'Review Financial Statements', order: 9, assignee: CONTROLLER },
        { name: 'CFO Approval', order: 10, assignee: CFO }
    ];

    for (const task of tasks) {
        const checklistItem = record.create({
            type: 'customrecord_close_checklist_item'
        });

        checklistItem.setValue({ fieldId: 'custrecord_period', value: periodId });
        checklistItem.setValue({ fieldId: 'custrecord_task_name', value: task.name });
        checklistItem.setValue({ fieldId: 'custrecord_task_order', value: task.order });
        checklistItem.setValue({ fieldId: 'custrecord_assignee', value: task.assignee });
        checklistItem.setValue({ fieldId: 'custrecord_status', value: STATUS_PENDING });

        checklistItem.save();
    }
}

function markTaskComplete(taskId) {
    record.submitFields({
        type: 'customrecord_close_checklist_item',
        id: taskId,
        values: {
            custrecord_status: STATUS_COMPLETE,
            custrecord_completed_date: new Date(),
            custrecord_completed_by: runtime.getCurrentUser().id
        }
    });

    // Check if all tasks complete
    const allComplete = checkAllTasksComplete();
    if (allComplete) {
        notifyCloseComplete();
    }
}
```

## Best Practices

### Scheduling Close Tasks

```javascript
// Schedule close tasks in sequence
const CLOSE_SCHEDULE = [
    { task: 'accruals', time: '18:00', dayOfMonth: 'last' },
    { task: 'deferrals', time: '19:00', dayOfMonth: 'last' },
    { task: 'allocations', time: '20:00', dayOfMonth: 'last' },
    { task: 'depreciation', time: '21:00', dayOfMonth: 'last' }
];
```

### Error Handling

```javascript
function runCloseTask(taskName, taskFunction) {
    try {
        log.audit({ title: `Starting: ${taskName}` });

        taskFunction();

        log.audit({ title: `Completed: ${taskName}` });
        markTaskComplete(taskName);

    } catch (e) {
        log.error({
            title: `Failed: ${taskName}`,
            details: e.message
        });

        notifyCloseTaskFailure(taskName, e.message);
        throw e;
    }
}
```

### Reconciliation Controls

```javascript
function validateJournalEntry(jeId) {
    const je = record.load({
        type: record.Type.JOURNAL_ENTRY,
        id: jeId
    });

    // Verify balanced
    const lineCount = je.getLineCount({ sublistId: 'line' });
    let totalDebit = 0;
    let totalCredit = 0;

    for (let i = 0; i < lineCount; i++) {
        totalDebit += parseFloat(je.getSublistValue({ sublistId: 'line', fieldId: 'debit', line: i }) || 0);
        totalCredit += parseFloat(je.getSublistValue({ sublistId: 'line', fieldId: 'credit', line: i }) || 0);
    }

    if (Math.abs(totalDebit - totalCredit) > 0.01) {
        throw error.create({
            name: 'UNBALANCED_JE',
            message: `Journal Entry ${jeId} is not balanced. Debit: ${totalDebit}, Credit: ${totalCredit}`
        });
    }
}
```

## Related Documentation

- **[Journal Entries](journal-entries.md)** - Automated JE creation patterns
- **[Reconciliation](reconciliation.md)** - Bank and account reconciliation
- **[Intercompany](intercompany.md)** - Intercompany eliminations

**External References:**
- [NetSuite Period Close](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N294152.html)
- [Journal Entry API](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N3053002.html)

---

*Generic period close automation patterns for month-end and year-end financial processes*
