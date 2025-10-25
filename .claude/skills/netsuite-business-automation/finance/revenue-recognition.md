# Revenue Recognition Automation

ASC 606 revenue recognition automation including deferred revenue, ratable recognition, and milestone-based revenue.

## Overview

Revenue recognition automation ensures compliance with ASC 606 accounting standards while accelerating revenue processing.

**ASC 606 Five-Step Model:**
1. Identify the contract
2. Identify performance obligations
3. Determine transaction price
4. Allocate transaction price to performance obligations
5. Recognize revenue when/as performance obligations are satisfied

**Automation Scope:**
- Revenue arrangement creation on invoice
- Recognition schedule calculation (ratable, milestone-based)
- Automatic journal entry creation for recognized revenue
- Deferred revenue tracking and amortization
- Performance obligation management

**Oracle NetSuite Documentation:**
- Revenue Recognition: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N3211445.html
- Based on: Perplexity research on ASC 606 compliance and NetSuite period close automation

## Point-in-Time Recognition

### User Event - Immediate Revenue Recognition

Recognize revenue immediately upon invoice creation (goods sold at point of sale).

```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType UserEventScript
 */
define(['N/record', 'N/log'], (record, log) => {

    function afterSubmit(context) {
        if (context.type !== context.UserEventType.CREATE) return;

        const invoice = context.newRecord;
        const revenueType = invoice.getValue({ fieldId: 'custbody_revenue_type' });

        // Only for point-in-time revenue (goods, not services)
        if (revenueType !== 'POINT_IN_TIME') return;

        const invoiceId = invoice.id;
        const revenueAmount = invoice.getValue({ fieldId: 'total' });
        const revenueAccount = invoice.getValue({ fieldId: 'custbody_revenue_account' });

        // Create revenue recognition journal entry
        const je = record.create({
            type: record.Type.JOURNAL_ENTRY,
            isDynamic: true
        });

        je.setValue({ fieldId: 'subsidiary', value: invoice.getValue({ fieldId: 'subsidiary' }) });
        je.setValue({ fieldId: 'memo', value: `Revenue recognition - Invoice ${invoiceId}` });

        // Debit: Deferred Revenue
        je.selectNewLine({ sublistId: 'line' });
        je.setCurrentSublistValue({ sublistId: 'line', fieldId: 'account', value: DEFERRED_REVENUE_ACCOUNT });
        je.setCurrentSublistValue({ sublistId: 'line', fieldId: 'debit', value: revenueAmount });
        je.commitLine({ sublistId: 'line' });

        // Credit: Revenue
        je.selectNewLine({ sublistId: 'line' });
        je.setCurrentSublistValue({ sublistId: 'line', fieldId: 'account', value: revenueAccount });
        je.setCurrentSublistValue({ sublistId: 'line', fieldId: 'credit', value: revenueAmount });
        je.commitLine({ sublistId: 'line' });

        const jeId = je.save();
        log.audit('Revenue Recognized', `JE ${jeId} for Invoice ${invoiceId}`);

        // Link JE to invoice
        record.submitFields({
            type: record.Type.INVOICE,
            id: invoiceId,
            values: { 'custbody_revenue_je': jeId }
        });
    }

    return { afterSubmit };
});
```

## Ratable Recognition (Over Time)

### Scheduled Script - Monthly Recognition

Recognize deferred revenue ratably over contract term (subscriptions, maintenance contracts).

```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType ScheduledScript
 */
define(['N/record', 'N/search', 'N/log'], (record, search, log) => {

    function execute(context) {
        const currentDate = new Date();
        const recognitionItems = findItemsForRecognition(currentDate);

        let recognizedCount = 0;

        for (const item of recognitionItems) {
            try {
                const amountToRecognize = calculateMonthlyRecognition(item);
                createRecognitionJE(item, amountToRecognize);
                updateRecognitionSchedule(item.scheduleId, amountToRecognize);
                recognizedCount++;
            } catch (e) {
                log.error('Recognition Failed', `Schedule ${item.scheduleId}: ${e.message}`);
            }
        }

        log.audit('Recognition Complete', `Recognized ${recognizedCount} items`);
    }

    function findItemsForRecognition(recognitionDate) {
        // Find revenue schedules due for recognition
        const schedules = [];

        const scheduleSearch = search.create({
            type: 'customrecord_revenue_schedule',
            filters: [
                ['custrecord_next_recognition_date', 'onorbefore', recognitionDate],
                'AND',
                ['custrecord_remaining_amount', 'greaterthan', '0']
            ],
            columns: [
                'custrecord_invoice',
                'custrecord_total_amount',
                'custrecord_remaining_amount',
                'custrecord_start_date',
                'custrecord_end_date',
                'custrecord_recognition_frequency'
            ]
        });

        scheduleSearch.run().each((result) => {
            schedules.push({
                scheduleId: result.id,
                invoiceId: result.getValue({ name: 'custrecord_invoice' }),
                totalAmount: parseFloat(result.getValue({ name: 'custrecord_total_amount' })),
                remainingAmount: parseFloat(result.getValue({ name: 'custrecord_remaining_amount' })),
                startDate: new Date(result.getValue({ name: 'custrecord_start_date' })),
                endDate: new Date(result.getValue({ name: 'custrecord_end_date' })),
                frequency: result.getValue({ name: 'custrecord_recognition_frequency' })
            });
            return true;
        });

        return schedules;
    }

    function calculateMonthlyRecognition(item) {
        const totalMonths = getMonthsBetween(item.startDate, item.endDate);
        const monthlyAmount = item.totalAmount / totalMonths;

        // Don't exceed remaining
        return Math.min(monthlyAmount, item.remainingAmount);
    }

    function createRecognitionJE(item, amount) {
        const je = record.create({ type: record.Type.JOURNAL_ENTRY, isDynamic: true });

        je.setValue({ fieldId: 'memo', value: `Revenue recognition - Schedule ${item.scheduleId}` });

        // Debit: Deferred Revenue
        je.selectNewLine({ sublistId: 'line' });
        je.setCurrentSublistValue({ sublistId: 'line', fieldId: 'account', value: DEFERRED_REVENUE_ACCOUNT });
        je.setCurrentSublistValue({ sublistId: 'line', fieldId: 'debit', value: amount });
        je.commitLine({ sublistId: 'line' });

        // Credit: Revenue
        je.selectNewLine({ sublistId: 'line' });
        je.setCurrentSublistValue({ sublistId: 'line', fieldId: 'account', value: REVENUE_ACCOUNT });
        je.setCurrentSublistValue({ sublistId: 'line', fieldId: 'credit', value: amount });
        je.commitLine({ sublistId: 'line' });

        return je.save();
    }

    function updateRecognitionSchedule(scheduleId, amountRecognized) {
        const schedule = record.load({
            type: 'customrecord_revenue_schedule',
            id: scheduleId
        });

        const currentRemaining = schedule.getValue({ fieldId: 'custrecord_remaining_amount' });
        const newRemaining = currentRemaining - amountRecognized;

        schedule.setValue({ fieldId: 'custrecord_remaining_amount', value: newRemaining });
        schedule.setValue({ fieldId: 'custrecord_last_recognition_date', value: new Date() });

        // Calculate next recognition date
        const nextDate = calculateNextRecognitionDate(new Date(), schedule.getValue({ fieldId: 'custrecord_recognition_frequency' }));
        schedule.setValue({ fieldId: 'custrecord_next_recognition_date', value: nextDate });

        schedule.save();
    }

    function getMonthsBetween(startDate, endDate) {
        const months = (endDate.getFullYear() - startDate.getFullYear()) * 12;
        return months + (endDate.getMonth() - startDate.getMonth());
    }

    function calculateNextRecognitionDate(currentDate, frequency) {
        const next = new Date(currentDate);
        if (frequency === 'MONTHLY') {
            next.setMonth(next.getMonth() + 1);
        } else if (frequency === 'QUARTERLY') {
            next.setMonth(next.getMonth() + 3);
        } else if (frequency === 'ANNUALLY') {
            next.setFullYear(next.getFullYear() + 1);
        }
        return next;
    }

    return { execute };
});
```

## Milestone-Based Recognition

### User Event - Recognize on Milestone Completion

Recognize revenue when project milestones are completed.

```javascript
/**
 * Trigger revenue recognition on milestone completion
 */
function afterSubmit(context) {
    if (context.type !== context.UserEventType.EDIT) return;

    const milestone = context.newRecord;
    const oldRecord = context.oldRecord;

    // Check if milestone was just completed
    const newStatus = milestone.getValue({ fieldId: 'custrecord_milestone_status' });
    const oldStatus = oldRecord.getValue({ fieldId: 'custrecord_milestone_status' });

    if (oldStatus !== 'COMPLETED' && newStatus === 'COMPLETED') {
        const projectId = milestone.getValue({ fieldId: 'custrecord_project' });
        const milestoneValue = milestone.getValue({ fieldId: 'custrecord_milestone_value' });

        recognizeRevenueForMilestone(projectId, milestoneValue, milestone.id);
    }
}

function recognizeRevenueForMilestone(projectId, amount, milestoneId) {
    // Create JE recognizing revenue
    const je = record.create({ type: record.Type.JOURNAL_ENTRY, isDynamic: true });

    je.setValue({ fieldId: 'memo', value: `Revenue recognition - Milestone ${milestoneId}` });
    je.setValue({ fieldId: 'custbody_project', value: projectId });

    // Debit: Unbilled Receivables
    je.selectNewLine({ sublistId: 'line' });
    je.setCurrentSublistValue({ sublistId: 'line', fieldId: 'account', value: UNBILLED_AR_ACCOUNT });
    je.setCurrentSublistValue({ sublistId: 'line', fieldId: 'debit', value: amount });
    je.commitLine({ sublistId: 'line' });

    // Credit: Revenue
    je.selectNewLine({ sublistId: 'line' });
    je.setCurrentSublistValue({ sublistId: 'line', fieldId: 'account', value: PROJECT_REVENUE_ACCOUNT });
    je.setCurrentSublistValue({ sublistId: 'line', fieldId: 'credit', value: amount });
    je.commitLine({ sublistId: 'line' });

    const jeId = je.save();

    // Update milestone with JE reference
    record.submitFields({
        type: 'customrecord_milestone',
        id: milestoneId,
        values: { 'custrecord_revenue_je': jeId }
    });

    return jeId;
}
```

## Subscription Billing

### Scheduled Script - Recurring Revenue Recognition

Process subscription renewals and recognize revenue monthly.

```javascript
function execute(context) {
    const subscriptions = findActiveSubscriptions();

    for (const sub of subscriptions) {
        // Check if billing date
        if (isRenewalDue(sub)) {
            // Create renewal invoice
            const invoiceId = createRenewalInvoice(sub);

            // Create deferred revenue
            createDeferredRevenueSchedule(invoiceId, sub);

            // Update subscription
            updateSubscriptionDates(sub.id);
        }

        // Recognize monthly portion
        if (isRecognitionDue(sub)) {
            recognizeMonthlyRevenue(sub);
        }
    }
}

function createRenewalInvoice(subscription) {
    const invoice = record.create({ type: record.Type.INVOICE, isDynamic: true });

    invoice.setValue({ fieldId: 'entity', value: subscription.customerId });
    invoice.setValue({ fieldId: 'custbody_subscription_id', value: subscription.id });

    // Add subscription line item
    invoice.selectNewLine({ sublistId: 'item' });
    invoice.setCurrentSublistValue({ sublistId: 'item', fieldId: 'item', value: subscription.itemId });
    invoice.setCurrentSublistValue({ sublistId: 'item', fieldId: 'quantity', value: 1 });
    invoice.setCurrentSublistValue({ sublistId: 'item', fieldId: 'rate', value: subscription.recurringAmount });
    invoice.commitLine({ sublistId: 'item' });

    return invoice.save();
}

function createDeferredRevenueSchedule(invoiceId, subscription) {
    const schedule = record.create({
        type: 'customrecord_revenue_schedule',
        isDynamic: false
    });

    schedule.setValue({ fieldId: 'custrecord_invoice', value: invoiceId });
    schedule.setValue({ fieldId: 'custrecord_total_amount', value: subscription.recurringAmount });
    schedule.setValue({ fieldId: 'custrecord_remaining_amount', value: subscription.recurringAmount });
    schedule.setValue({ fieldId: 'custrecord_start_date', value: new Date() });
    schedule.setValue({ fieldId: 'custrecord_end_date', value: calculateEndDate(12) }); // 12 months
    schedule.setValue({ fieldId: 'custrecord_recognition_frequency', value: 'MONTHLY' });

    return schedule.save();
}
```

## Custom Revenue Arrangements

### Create Revenue Arrangement Record

Track multi-element arrangements with separate performance obligations.

```javascript
function createRevenueArrangement(salesOrder) {
    const arrangement = record.create({
        type: 'customrecord_revenue_arrangement',
        isDynamic: false
    });

    arrangement.setValue({ fieldId: 'custrecord_sales_order', value: salesOrder.id });
    arrangement.setValue({ fieldId: 'custrecord_customer', value: salesOrder.getValue({ fieldId: 'entity' }) });
    arrangement.setValue({ fieldId: 'custrecord_total_contract_value', value: salesOrder.getValue({ fieldId: 'total' }) });

    const arrangementId = arrangement.save();

    // Create performance obligations
    const lineCount = salesOrder.getLineCount({ sublistId: 'item' });

    for (let i = 0; i < lineCount; i++) {
        const itemType = salesOrder.getSublistValue({ sublistId: 'item', fieldId: 'custcol_item_type', line: i });

        if (itemType === 'SERVICE' || itemType === 'SUBSCRIPTION') {
            createPerformanceObligation(arrangementId, salesOrder, i);
        }
    }

    return arrangementId;
}

function createPerformanceObligation(arrangementId, salesOrder, lineIndex) {
    const obligation = record.create({
        type: 'customrecord_performance_obligation',
        isDynamic: false
    });

    const itemId = salesOrder.getSublistValue({ sublistId: 'item', fieldId: 'item', line: lineIndex });
    const amount = salesOrder.getSublistValue({ sublistId: 'item', fieldId: 'amount', line: lineIndex });

    obligation.setValue({ fieldId: 'custrecord_arrangement', value: arrangementId });
    obligation.setValue({ fieldId: 'custrecord_item', value: itemId });
    obligation.setValue({ fieldId: 'custrecord_allocated_amount', value: amount });
    obligation.setValue({ fieldId: 'custrecord_status', value: 'NOT_SATISFIED' });

    return obligation.save();
}
```

## Revenue Schedule Management

### Data Model

Custom records for tracking revenue recognition:

**Revenue Arrangement:**
- Sales Order reference
- Total contract value
- Contract start/end dates
- Status (Active, Completed, Terminated)

**Performance Obligation:**
- Revenue Arrangement reference
- Item/service description
- Allocated amount
- Satisfaction status
- Recognition method (Point-in-time, Over time, Milestone)

**Revenue Schedule:**
- Performance Obligation reference
- Total deferred amount
- Remaining amount
- Recognition frequency (Monthly, Quarterly)
- Next recognition date

## Compliance Reporting

### Revenue Recognition Report

Generate ASC 606 compliance report.

```javascript
function generateComplianceReport(fiscalPeriod) {
    const report = {
        period: fiscalPeriod,
        totalContractValue: 0,
        recognizedRevenue: 0,
        deferredRevenue: 0,
        performanceObligations: {
            satisfied: 0,
            partiallyS satisfied: 0,
            notSatisfied: 0
        }
    };

    // Query revenue arrangements
    const arrangements = search.create({
        type: 'customrecord_revenue_arrangement',
        filters: [
            ['custrecord_period', 'is', fiscalPeriod],
            'AND',
            ['custrecord_status', 'noneof', 'TERMINATED']
        ],
        columns: [
            'custrecord_total_contract_value',
            'custrecord_recognized_amount',
            'custrecord_deferred_amount'
        ]
    });

    arrangements.run().each((result) => {
        report.totalContractValue += parseFloat(result.getValue({ name: 'custrecord_total_contract_value' }));
        report.recognizedRevenue += parseFloat(result.getValue({ name: 'custrecord_recognized_amount' }));
        report.deferredRevenue += parseFloat(result.getValue({ name: 'custrecord_deferred_amount' }));
        return true;
    });

    return report;
}
```

## Best Practices

### ASC 606 Compliance
- Identify distinct performance obligations for each contract
- Allocate transaction price based on standalone selling prices
- Recognize revenue when (or as) performance obligations are satisfied
- Maintain detailed audit trail of recognition decisions
- Document contract modifications and variable consideration

### Automation Guidelines
- Create revenue schedule on invoice creation (for subscriptions)
- Run recognition scripts monthly during period close
- Validate deferred balances reconcile to GL
- Link all JEs to source invoices/contracts
- Maintain performance obligation status tracking

### Data Integrity
- Always balance deferred revenue and revenue accounts
- Validate recognition doesn't exceed contract value
- Check that all performance obligations are tracked
- Ensure recognition dates align with contract terms
- Audit trail for all recognition events

### Performance
- Use custom records for revenue schedules (scalable)
- Schedule recognition during off-peak hours
- Use Map/Reduce for >1000 schedules
- Cache account mappings
- Batch JE creation when possible

## Testing Checklist

1. **Point-in-Time Recognition**
   - Invoice created → Revenue recognized immediately
   - JE created with correct amounts
   - Deferred revenue = 0

2. **Ratable Recognition**
   - Schedule created on invoice
   - Monthly recognition JE created
   - Remaining balance decreases correctly
   - Final recognition completes schedule

3. **Milestone Recognition**
   - Milestone completed → Revenue recognized
   - JE created for milestone value
   - Unbilled AR recognized

4. **Contract Modifications**
   - Additional services → New performance obligations
   - Cancellation → Adjust deferred revenue
   - Price change → Reallocate transaction price

## Related Documentation

- **[Journal Entries](journal-entries.md)** - JE creation patterns
- **[Period Close](period-close.md)** - Month-end recognition process
- **[Revenue (O2C)](../order-to-cash/revenue.md)** - Order-to-cash revenue tracking

**Oracle NetSuite:**
- Revenue Recognition: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N3211445.html
- Advanced Revenue Management: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/bridgehead_N3046713.html

---

*Based on: ASC 606 accounting standards and Perplexity research on NetSuite revenue recognition automation*
