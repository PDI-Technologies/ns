# Large Volume Processing

Map/Reduce script patterns for processing >1000 records with automatic governance yielding.

## Overview

NetSuite Map/Reduce scripts enable parallel processing of large datasets with automatic governance management. Use for batch operations exceeding Scheduled Script limits.

**When to Use Map/Reduce:**
- Processing >1000 records
- Complex multi-step data transformations
- Heavy computation that exceeds governance limits
- Operations requiring parallel execution

**Governance Benefits:**
- Automatic yielding (no manual governance monitoring)
- Queue-based execution (processes continue across multiple executions)
- Parallel processing across multiple queues
- Handles millions of records

**Oracle NetSuite Documentation:**
- Map/Reduce Scripts: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4387799161.html
- Based on: Perplexity research on NetSuite scheduled scripts and governance limits

## Basic Map/Reduce Pattern

### Four-Stage Processing

Map/Reduce scripts have four stages:

1. **getInputData()** - Define input dataset (search or array)
2. **map()** - Process each record independently
3. **reduce()** - Aggregate results by key
4. **summarize()** - Final reporting and error handling

```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType MapReduceScript
 */
define(['N/record', 'N/search', 'N/log'], (record, search, log) => {

    /**
     * Stage 1: Define input data
     * Returns: search.Search object or array
     */
    function getInputData() {
        // Return saved search or create search
        return search.create({
            type: search.Type.TRANSACTION,
            filters: [
                ['type', 'anyof', 'CustInvc'],
                'AND',
                ['mainline', 'is', 'T'],
                'AND',
                ['status', 'anyof', 'CustInvc:A'] // Open invoices
            ],
            columns: ['entity', 'total', 'duedate', 'trandate']
        });
    }

    /**
     * Stage 2: Process each record
     * Called once per search result
     */
    function map(context) {
        try {
            const searchResult = JSON.parse(context.value);
            const invoiceId = searchResult.id;

            // Process record
            const daysOverdue = calculateDaysOverdue(searchResult);

            if (daysOverdue > 30) {
                // Write to reduce stage
                context.write({
                    key: searchResult.values.entity.value, // Customer ID
                    value: {
                        invoiceId: invoiceId,
                        amount: searchResult.values.total,
                        daysOverdue: daysOverdue
                    }
                });
            }
        } catch (e) {
            log.error('Map Error', `Record ${context.key}: ${e.message}`);
        }
    }

    /**
     * Stage 3: Aggregate by key
     * Called once per unique key from map stage
     */
    function reduce(context) {
        try {
            const customerId = context.key;
            const invoices = context.values.map(JSON.parse);

            // Aggregate customer data
            const totalOverdue = invoices.reduce((sum, inv) => sum + parseFloat(inv.amount), 0);
            const oldestInvoice = Math.max(...invoices.map(inv => inv.daysOverdue));

            // Create task or send notification
            createCollectionTask(customerId, totalOverdue, oldestInvoice);

            context.write({
                key: customerId,
                value: { totalOverdue, invoiceCount: invoices.length }
            });
        } catch (e) {
            log.error('Reduce Error', `Customer ${context.key}: ${e.message}`);
        }
    }

    /**
     * Stage 4: Summarize results and handle errors
     */
    function summarize(summary) {
        log.audit('Summary', `Total Usage: ${summary.usage} units`);
        log.audit('Summary', `Yields: ${summary.yields}`);

        // Process map stage errors
        summary.mapSummary.errors.iterator().each((key, error) => {
            log.error('Map Error', `Key: ${key}, Error: ${error}`);
            return true;
        });

        // Process reduce stage errors
        summary.reduceSummary.errors.iterator().each((key, error) => {
            log.error('Reduce Error', `Key: ${key}, Error: ${error}`);
            return true;
        });

        // Log final output
        let processedCount = 0;
        summary.output.iterator().each((key, value) => {
            processedCount++;
            return true;
        });

        log.audit('Complete', `Processed ${processedCount} customers`);
    }

    return {
        getInputData: getInputData,
        map: map,
        reduce: reduce,
        summarize: summarize
    };
});
```

## Common Patterns

### Pattern 1: Bulk Record Updates

Update thousands of records efficiently.

```javascript
function getInputData() {
    // Search for records to update
    return search.create({
        type: search.Type.CUSTOMER,
        filters: [['custentity_needs_update', 'is', 'T']]
    });
}

function map(context) {
    const customerId = JSON.parse(context.value).id;

    try {
        record.submitFields({
            type: record.Type.CUSTOMER,
            id: customerId,
            values: {
                'custentity_updated': true,
                'custentity_update_date': new Date()
            }
        });

        context.write({ key: 'success', value: customerId });
    } catch (e) {
        context.write({ key: 'failed', value: { id: customerId, error: e.message } });
    }
}

function reduce(context) {
    // Count successes and failures
    const count = context.values.length;
    log.audit(context.key, `Count: ${count}`);
}
```

### Pattern 2: Data Aggregation

Calculate aggregates across large datasets.

```javascript
function getInputData() {
    // Return large transaction dataset
    return search.create({
        type: search.Type.TRANSACTION,
        filters: [['trandate', 'within', 'lastfiscalyear']],
        columns: ['entity', 'amount', 'account']
    });
}

function map(context) {
    const txn = JSON.parse(context.value);
    const accountId = txn.values.account.value;
    const amount = parseFloat(txn.values.amount);

    // Group by account
    context.write({
        key: accountId,
        value: amount
    });
}

function reduce(context) {
    // Sum amounts per account
    const accountId = context.key;
    const amounts = context.values.map(parseFloat);
    const total = amounts.reduce((sum, amt) => sum + amt, 0);

    // Update custom record with totals
    updateAccountSummary(accountId, total);
}
```

### Pattern 3: External API Integration

Process records with external API calls.

```javascript
function map(context) {
    const order = JSON.parse(context.value);
    const orderId = order.id;

    try {
        // Call external API (each API call consumes governance)
        const response = https.post({
            url: EXTERNAL_API_URL,
            headers: { 'Authorization': 'Bearer ' + API_KEY },
            body: JSON.stringify({
                netsuite_order_id: orderId,
                customer: order.values.entity.text,
                total: order.values.total
            })
        });

        const result = JSON.parse(response.body);

        // Update order with external system ID
        record.submitFields({
            type: record.Type.SALES_ORDER,
            id: orderId,
            values: { 'custbody_external_id': result.external_id }
        });

        context.write({ key: 'success', value: orderId });
    } catch (e) {
        context.write({ key: 'error', value: { orderId, error: e.message } });
    }
}
```

## Performance Optimization

### Input Data Optimization

```javascript
function getInputData() {
    // Optimize search for Map/Reduce
    return search.create({
        type: search.Type.SALES_ORDER,
        filters: [
            ['mainline', 'is', 'T'], // Main line only (reduces volume)
            'AND',
            ['status', 'anyof', 'SalesOrd:B'] // Specific status
        ],
        columns: [
            'entity',
            'total',
            'custbody_field1' // Only needed columns
        ]
    });
}
```

**Best Practices:**
- Use `mainline = T` filter for transaction searches
- Return only required columns
- Use indexed fields in filters
- Consider saved searches for complex queries

### Reduce Stage Optimization

```javascript
function reduce(context) {
    // Batch operations instead of one-at-a-time
    const records = context.values.map(JSON.parse);

    // Process in batches
    const BATCH_SIZE = 100;
    for (let i = 0; i < records.length; i += BATCH_SIZE) {
        const batch = records.slice(i, i + BATCH_SIZE);
        processBatch(batch);
    }
}
```

## Error Handling

### Comprehensive Error Management

```javascript
function summarize(summary) {
    // Check for input stage errors
    if (summary.inputSummary.error) {
        log.error('Input Error', summary.inputSummary.error);
        // Send alert to admin
        sendErrorNotification('Input stage failed', summary.inputSummary.error);
    }

    // Track all map errors
    const mapErrors = [];
    summary.mapSummary.errors.iterator().each((key, error) => {
        mapErrors.push({ key, error });
        log.error('Map Error', `${key}: ${error}`);
        return true;
    });

    // Track all reduce errors
    const reduceErrors = [];
    summary.reduceSummary.errors.iterator().each((key, error) => {
        reduceErrors.push({ key, error });
        log.error('Reduce Error', `${key}: ${error}`);
        return true;
    });

    // Create error report if failures occurred
    if (mapErrors.length > 0 || reduceErrors.length > 0) {
        createErrorReport({
            mapErrors,
            reduceErrors,
            scriptId: summary.scriptId,
            timestamp: new Date()
        });
    }

    // Log success metrics
    log.audit('Processing Complete', {
        inputCount: summary.inputSummary.count,
        mapCount: summary.mapSummary.count,
        reduceCount: summary.reduceSummary.count,
        outputCount: summary.output.count(),
        totalUsage: summary.usage,
        yields: summary.yields
    });
}
```

## Governance Monitoring

### Track Usage Across Stages

Map/Reduce automatically yields, but monitoring helps optimize:

```javascript
function summarize(summary) {
    // Analyze governance usage
    const usage = summary.usage;
    const seconds = summary.seconds;

    log.audit('Governance Report', {
        usage: usage,
        time: seconds,
        yields: summary.yields,
        concurrency: summary.concurrency
    });

    // Alert if usage is high (may indicate inefficiency)
    if (usage > 8000) {
        log.audit('High Usage Warning',
            'Consider optimizing search or reducing API calls');
    }
}
```

**Governance Limits:**
- Map/Reduce has no hard limit (auto-yields)
- Each stage can use full governance allocation
- Yields automatically when approaching limits
- Continues in new queue after yield

## Scheduling Best Practices

### Deployment Configuration

```javascript
// Script Deployment settings:
// - Status: Testing (during development)
// - Status: Released (production)
// - Execute as Admin: Yes (for system-wide operations)
// - Audience: All Roles (or specific roles)

// Triggers:
// - Scheduled: Daily at 2 AM (off-peak)
// - On Demand: Manual execution
// - Workflow: Triggered by workflow action
```

**Scheduling Recommendations:**
- Run during off-peak hours (2-6 AM Pacific)
- Avoid overlapping with other heavy scripts
- Monitor queue depth (too many scripts = delays)
- Use Scheduled triggers, not time-based (more reliable)

## Testing Approach

### Development Testing

```javascript
// Create test version with limited input
function getInputData() {
    // TESTING: Limit to 100 records
    const TEST_MODE = true;

    const baseSearch = search.create({
        type: search.Type.SALES_ORDER,
        filters: [/* your filters */]
    });

    if (TEST_MODE) {
        // Run limited search for testing
        return baseSearch.run().getRange({ start: 0, end: 100 });
    } else {
        return baseSearch;
    }
}
```

**Testing Checklist:**
1. Test with small dataset (100 records)
2. Verify map output is correct
3. Verify reduce aggregation is correct
4. Check error handling (invalid record)
5. Monitor governance usage
6. Test with full dataset in sandbox
7. Review execution logs
8. Verify summarize stage reporting

## Common Use Cases

### Use Case 1: Mass Customer Update
- Input: All customers matching criteria
- Map: Update each customer record
- Reduce: Count successes/failures
- Summarize: Generate report

### Use Case 2: Financial Close
- Input: All open transactions
- Map: Calculate accruals per transaction
- Reduce: Sum accruals by account
- Summarize: Create journal entries

### Use Case 3: Inventory Revaluation
- Input: All inventory items
- Map: Calculate new valuation
- Reduce: Aggregate by location
- Summarize: Create adjustment transactions

### Use Case 4: Data Migration
- Input: Records to migrate
- Map: Transform and create new records
- Reduce: Track migration status
- Summarize: Generate migration report

## Related Documentation

- **[Journal Entries](../finance/journal-entries.md)** - Bulk JE creation with Map/Reduce
- **[Sales Orders](../order-to-cash/sales-orders.md)** - Batch order processing

**Local KB:**
- `/opt/ns/kb/suitescript-modules.md` - N/search, N/record APIs
- `/opt/ns/kb/suitecloud-sdk-framework.md` - Deployment workflows

**Oracle NetSuite:**
- Map/Reduce Scripts: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4387799161.html
- Script Governance: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N3450096.html

---

*Based on: Perplexity research findings on NetSuite scheduled scripts (10,000 unit limit), Map/Reduce auto-yielding, and off-peak scheduling (2-6 AM Pacific)*
