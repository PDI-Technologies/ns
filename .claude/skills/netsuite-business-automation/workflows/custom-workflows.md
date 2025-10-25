# Custom Workflow Actions

Workflow Action Scripts for complex calculations, external API calls, and conditional routing within NetSuite workflows.

## Overview

Workflow Action Scripts execute custom logic within NetSuite workflows, enabling:

**Use Cases:**
- Complex calculations (pricing, allocation, scoring)
- External API integrations (notifications, data sync)
- Conditional routing logic (dynamic approval paths)
- Record transformations (create related records)
- Data validation (business rule enforcement)

**Script Type:** WorkflowActionScript
**Governance:** 1,000 units per execution
**Return Values:** 'SUCCESS', 'FAILURE', or custom status

**Oracle NetSuite Documentation:**
- Workflow Action Scripts: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4463405142.html
- See also: `/opt/ns/kb/suitescript-modules.md` (N/record, N/https APIs)

## Basic Pattern

### Workflow Action Script Structure

```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType WorkflowActionScript
 */
define(['N/record', 'N/runtime'], (record, runtime) => {

    /**
     * Main entry point - called by workflow
     * @param {Object} context
     * @param {Record} context.newRecord - Current record
     * @param {Record} context.oldRecord - Previous state (before workflow)
     * @return {string} 'SUCCESS' or 'FAILURE'
     */
    function onAction(context) {
        try {
            const currentRecord = context.newRecord;
            const recordId = currentRecord.id;

            // Custom logic here
            const result = performCalculation(currentRecord);

            // Update record fields
            currentRecord.setValue({
                fieldId: 'custbody_calculated_value',
                value: result
            });

            log.audit('Workflow Action', `Processed record ${recordId}`);
            return 'SUCCESS';

        } catch (e) {
            log.error('Workflow Action Error', e.message);
            return 'FAILURE';
        }
    }

    return {
        onAction: onAction
    };
});
```

## Common Patterns

### Pattern 1: External API Notification

Send data to external system during workflow.

```javascript
define(['N/https', 'N/record'], (https, record) => {

    function onAction(context) {
        const salesOrder = context.newRecord;
        const orderId = salesOrder.id;
        const orderTotal = salesOrder.getValue({ fieldId: 'total' });
        const customerId = salesOrder.getValue({ fieldId: 'entity' });

        try {
            // Call external notification service
            const response = https.post({
                url: 'https://api.example.com/notifications',
                headers: {
                    'Authorization': 'Bearer ' + getApiKey(),
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    event: 'order_approved',
                    order_id: orderId,
                    customer_id: customerId,
                    amount: orderTotal,
                    timestamp: new Date().toISOString()
                })
            });

            if (response.code === 200) {
                salesOrder.setValue({
                    fieldId: 'custbody_notification_sent',
                    value: true
                });
                return 'SUCCESS';
            } else {
                log.error('API Error', `Status: ${response.code}`);
                return 'FAILURE';
            }

        } catch (e) {
            log.error('Notification Failed', e.message);
            return 'FAILURE';
        }
    }

    return { onAction };
});
```

### Pattern 2: Complex Calculation

Calculate values based on complex business rules.

```javascript
function onAction(context) {
    const salesOrder = context.newRecord;

    // Calculate commission based on complex rules
    const lineCount = salesOrder.getLineCount({ sublistId: 'item' });
    let totalCommission = 0;

    for (let i = 0; i < lineCount; i++) {
        const itemCategory = salesOrder.getSublistValue({
            sublistId: 'item',
            fieldId: 'custcol_category',
            line: i
        });
        const amount = salesOrder.getSublistValue({
            sublistId: 'item',
            fieldId: 'amount',
            line: i
        });

        // Category-based commission rates
        const commissionRate = getCommissionRate(itemCategory);
        totalCommission += (amount * commissionRate);
    }

    // Apply commission to sales rep
    salesOrder.setValue({
        fieldId: 'custbody_commission_amount',
        value: totalCommission
    });

    return 'SUCCESS';
}

function getCommissionRate(category) {
    const rates = {
        'HARDWARE': 0.05,   // 5%
        'SOFTWARE': 0.10,   // 10%
        'SERVICES': 0.15    // 15%
    };
    return rates[category] || 0.03; // Default 3%
}
```

### Pattern 3: Conditional Routing

Return custom status to control workflow path.

```javascript
function onAction(context) {
    const purchaseOrder = context.newRecord;
    const poTotal = purchaseOrder.getValue({ fieldId: 'total' });
    const vendor = purchaseOrder.getValue({ fieldId: 'entity' });

    // Check vendor risk rating
    const vendorRisk = search.lookupFields({
        type: search.Type.VENDOR,
        id: vendor,
        columns: ['custentity_risk_rating']
    }).custentity_risk_rating;

    // Routing logic
    if (poTotal > 50000 && vendorRisk === 'HIGH') {
        return 'EXECUTIVE_APPROVAL'; // Custom status - route to executive
    } else if (poTotal > 10000) {
        return 'MANAGER_APPROVAL'; // Route to manager
    } else {
        return 'AUTO_APPROVE'; // Auto-approve
    }
}
```

**Workflow Configuration:**
- Create workflow transitions for each return value
- 'EXECUTIVE_APPROVAL' → Transition to executive approval state
- 'MANAGER_APPROVAL' → Transition to manager approval state
- 'AUTO_APPROVE' → Transition to approved state

### Pattern 4: Record Creation

Create related records during workflow.

```javascript
function onAction(context) {
    const invoice = context.newRecord;
    const invoiceId = invoice.id;
    const invoiceTotal = invoice.getValue({ fieldId: 'total' });

    // Create payment reminder task
    const task = record.create({
        type: record.Type.TASK,
        isDynamic: true
    });

    task.setValue({ fieldId: 'title', value: `Payment Reminder - Invoice ${invoiceId}` });
    task.setValue({ fieldId: 'assigned', value: AR_MANAGER_ID });
    task.setValue({ fieldId: 'transaction', value: invoiceId });
    task.setValue({ fieldId: 'duedate', value: calculateDueDate(30) }); // 30 days
    task.setValue({ fieldId: 'message', value: `Invoice ${invoiceId} for $${invoiceTotal} due in 30 days` });

    const taskId = task.save();

    invoice.setValue({
        fieldId: 'custbody_reminder_task',
        value: taskId
    });

    return 'SUCCESS';
}
```

## Best Practices

### Error Handling

Always return explicit status:

```javascript
function onAction(context) {
    try {
        // Business logic
        performAction(context.newRecord);
        return 'SUCCESS';

    } catch (e) {
        // Log detailed error
        log.error({
            title: 'Workflow Action Failed',
            details: {
                recordId: context.newRecord.id,
                error: e.message,
                stack: e.stack
            }
        });

        // Optionally set error field on record
        context.newRecord.setValue({
            fieldId: 'custbody_workflow_error',
            value: e.message
        });

        return 'FAILURE';
    }
}
```

### Governance Management

Monitor governance usage:

```javascript
function onAction(context) {
    const startUsage = runtime.getCurrentScript().getRemainingUsage();

    // Perform operations
    processRecord(context.newRecord);

    const endUsage = runtime.getCurrentScript().getRemainingUsage();
    const used = startUsage - endUsage;

    log.audit('Governance Used', `${used} units`);

    // Alert if approaching limit
    if (endUsage < 100) {
        log.audit('Low Governance Warning', `Only ${endUsage} units remaining`);
    }

    return 'SUCCESS';
}
```

### Field Access

Use correct methods for field access:

```javascript
function onAction(context) {
    const record = context.newRecord;

    // Body fields - direct access
    const customerId = record.getValue({ fieldId: 'entity' });

    // Sublist fields - getSublistValue
    const itemId = record.getSublistValue({
        sublistId: 'item',
        fieldId: 'item',
        line: 0
    });

    // Set values
    record.setValue({ fieldId: 'memo', value: 'Updated by workflow' });

    return 'SUCCESS';
}
```

## Deployment Configuration

### Script Deployment Settings

```
Script File: custom_workflow_action.js
Deployments:
  - Script ID: customdeploy_workflow_action
  - Status: Released
  - Execute As Admin: Yes (for system-wide operations)
  - Log Level: Debug (development) / Audit (production)
```

### Workflow Configuration

```
Workflow: Sales Order Approval
State: Pending Approval
Action: Calculate Commission
  - Script: Custom Workflow Action
  - Result Field: Workflow Action Result
  - On Success: Transition to Approved
  - On Failure: Transition to Review
```

## Testing Approach

### Development Testing

```javascript
// Add test mode flag
function onAction(context) {
    const TEST_MODE = runtime.getCurrentScript()
        .getParameter({ name: 'custscript_test_mode' });

    if (TEST_MODE) {
        log.audit('TEST MODE', 'Skipping external API call');
        return 'SUCCESS';
    }

    // Normal execution
    return callExternalAPI(context.newRecord);
}
```

**Testing Steps:**
1. Create test workflow with action script
2. Test with sample record in sandbox
3. Verify script execution logs
4. Check governance usage
5. Test success and failure paths
6. Verify record field updates
7. Test with production-like data volume

## Common Use Cases

**Financial Approval:**
- Calculate approval amounts
- Route based on thresholds
- Apply discount limits

**Order Processing:**
- Validate inventory availability
- Calculate shipping costs
- Apply pricing rules

**Integration:**
- Send notifications to external systems
- Sync data to third-party apps
- Create related records in other systems

**Validation:**
- Enforce business rules
- Check compliance requirements
- Validate data integrity

## Related Documentation

- **[Approval Routing](approval-routing.md)** - Workflow approval patterns
- **[Sales Orders](../order-to-cash/sales-orders.md)** - Order workflow examples

**Local KB:**
- `/opt/ns/kb/suitescript-modules.md` - N/record, N/https APIs
- `/opt/ns/kb/authentication.md` - OAuth for external APIs

**Oracle NetSuite:**
- Workflow Action Scripts: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4463405142.html
- Workflow States: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N3602163.html
