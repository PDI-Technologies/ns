# Approval Routing Automation

Dynamic approval routing workflows using User Event Scripts, Workflow Action Scripts, and custom approval logic.

## Overview

Approval routing automates the process of routing transactions (sales orders, purchase requisitions, vendor bills, expense reports) to appropriate approvers based on business rules.

**Common Use Cases:**
- Multi-level approval hierarchies (manager → director → VP)
- Threshold-based routing ($10K+ requires VP approval)
- Department-specific approval chains
- Conditional routing based on transaction attributes
- Parallel approvals (requires multiple approvers)
- Escalation for overdue approvals

**Implementation Approaches:**
- Native NetSuite Workflows (no code, limited flexibility)
- User Event Scripts (dynamic routing logic)
- Workflow Action Scripts (complex conditional logic)
- RESTlet integration (external approval systems)

## Approval Routing Patterns

### Pattern 1: Threshold-Based Routing

Route based on transaction amount thresholds.

**Business Rules:**
- < $5,000: Auto-approve
- $5,000 - $25,000: Manager approval
- $25,000 - $100,000: Director approval
- > $100,000: VP + CFO approval

**User Event Script (beforeSubmit):**

```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType UserEventScript
 */

define(['N/record', 'N/runtime', 'N/search'], (record, runtime, search) => {

    function beforeSubmit(context) {
        if (context.type !== context.UserEventType.CREATE &&
            context.type !== context.UserEventType.EDIT) {
            return;
        }

        const purchaseOrder = context.newRecord;
        const total = purchaseOrder.getValue({ fieldId: 'total' });

        // Determine required approval level
        const approver = determineApprover(total);

        // Set custom approver field
        purchaseOrder.setValue({
            fieldId: 'custbody_approver',
            value: approver.id
        });

        // Set approval status
        purchaseOrder.setValue({
            fieldId: 'custbody_approval_status',
            value: 'Pending'
        });
    }

    function determineApprover(amount) {
        if (amount < 5000) {
            return { id: null, level: 'Auto-Approved' };
        } else if (amount < 25000) {
            return { id: MANAGER_ID, level: 'Manager' };
        } else if (amount < 100000) {
            return { id: DIRECTOR_ID, level: 'Director' };
        } else {
            return { id: VP_ID, level: 'VP' };
        }
    }

    return {
        beforeSubmit: beforeSubmit
    };
});
```

### Pattern 2: Hierarchical Approvals

Route up the management hierarchy until approval threshold met.

**Workflow Action Script:**

```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType WorkflowActionScript
 */

define(['N/record', 'N/search', 'N/runtime'], (record, search, runtime) => {

    function onAction(context) {
        const currentRecord = context.newRecord;
        const currentApprover = runtime.getCurrentUser().id;
        const total = currentRecord.getValue({ fieldId: 'total' });

        // Get current approver's approval limit
        const approverLimit = getApproverLimit(currentApprover);

        if (total <= approverLimit) {
            // Current approver has authority
            currentRecord.setValue({
                fieldId: 'custbody_approval_status',
                value: 'Approved'
            });
            currentRecord.setValue({
                fieldId: 'approvalstatus',
                value: 2  // Approved
            });
            return 'APPROVED';
        } else {
            // Escalate to next level
            const nextApprover = getNextApprover(currentApprover);

            if (nextApprover) {
                currentRecord.setValue({
                    fieldId: 'custbody_approver',
                    value: nextApprover.id
                });
                currentRecord.setValue({
                    fieldId: 'custbody_approval_status',
                    value: 'Pending - Escalated to ' + nextApprover.name
                });
                return 'ESCALATED';
            } else {
                // No higher approver available
                currentRecord.setValue({
                    fieldId: 'custbody_approval_status',
                    value: 'Rejected - No Approver with Sufficient Authority'
                });
                return 'REJECTED';
            }
        }
    }

    function getApproverLimit(employeeId) {
        // Lookup custom employee field for approval limit
        const employeeFields = search.lookupFields({
            type: search.Type.EMPLOYEE,
            id: employeeId,
            columns: ['custentity_approval_limit']
        });

        return parseFloat(employeeFields.custentity_approval_limit) || 0;
    }

    function getNextApprover(currentApproverId) {
        // Lookup supervisor of current approver
        const employeeFields = search.lookupFields({
            type: search.Type.EMPLOYEE,
            id: currentApproverId,
            columns: ['supervisor']
        });

        const supervisorId = employeeFields.supervisor?.[0]?.value;

        if (supervisorId) {
            const supervisorFields = search.lookupFields({
                type: search.Type.EMPLOYEE,
                id: supervisorId,
                columns: ['entityid']
            });

            return {
                id: supervisorId,
                name: supervisorFields.entityid
            };
        }

        return null;
    }

    return {
        onAction: onAction
    };
});
```

### Pattern 3: Department-Based Routing

Route to approvers based on transaction department.

**Approval Mapping Table:**

```javascript
const DEPARTMENT_APPROVERS = {
    'Sales': { manager: '123', director: '456' },
    'Marketing': { manager: '789', director: '101' },
    'Operations': { manager: '112', director: '131' },
    'Finance': { manager: '415', director: '161' }
};

function getDepartmentApprover(department, level) {
    const approvers = DEPARTMENT_APPROVERS[department];
    if (!approvers) {
        throw error.create({
            name: 'NO_APPROVER_DEFINED',
            message: `No approver defined for department: ${department}`
        });
    }
    return approvers[level];
}
```

### Pattern 4: Conditional Multi-Approver

Require multiple approvals based on transaction attributes.

**Example: Capital Expenditure Approval**
- CapEx items require both Department Head + CFO approval
- Operating expenses require only Department Head

**User Event Script:**

```javascript
function beforeSubmit(context) {
    const purchaseOrder = context.newRecord;
    const lineCount = purchaseOrder.getLineCount({ sublistId: 'item' });

    let requiresCapExApproval = false;

    // Check if any line items are CapEx
    for (let i = 0; i < lineCount; i++) {
        const itemCategory = purchaseOrder.getSublistValue({
            sublistId: 'item',
            fieldId: 'custcol_expense_category',
            line: i
        });

        if (itemCategory === 'CapEx') {
            requiresCapExApproval = true;
            break;
        }
    }

    if (requiresCapExApproval) {
        // Set both approvers required
        purchaseOrder.setValue({
            fieldId: 'custbody_dept_approver',
            value: getDepartmentHead()
        });
        purchaseOrder.setValue({
            fieldId: 'custbody_finance_approver',
            value: CFO_ID
        });
        purchaseOrder.setValue({
            fieldId: 'custbody_approval_type',
            value: 'Multi-Approver'
        });
    } else {
        // Single approver
        purchaseOrder.setValue({
            fieldId: 'custbody_dept_approver',
            value: getDepartmentHead()
        });
        purchaseOrder.setValue({
            fieldId: 'custbody_approval_type',
            value: 'Single-Approver'
        });
    }
}
```

### Pattern 5: Escalation for Overdue Approvals

Auto-escalate approvals not completed within SLA.

**Scheduled Script (daily):**

```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType ScheduledScript
 */

define(['N/search', 'N/record', 'N/email'], (search, record, email) => {

    function execute(context) {
        // Find pending approvals older than 3 days
        const overdueApprovals = search.create({
            type: search.Type.PURCHASE_ORDER,
            filters: [
                ['custbody_approval_status', 'is', 'Pending'],
                'AND',
                ['datecreated', 'before', 'daysago3']
            ],
            columns: [
                'tranid',
                'total',
                'custbody_approver',
                'datecreated',
                'createdby'
            ]
        }).run();

        overdueApprovals.each((result) => {
            const poId = result.id;
            const currentApprover = result.getValue({ name: 'custbody_approver' });

            // Get next level approver (supervisor)
            const nextApprover = getNextApprover(currentApprover);

            if (nextApprover) {
                // Escalate approval
                record.submitFields({
                    type: record.Type.PURCHASE_ORDER,
                    id: poId,
                    values: {
                        custbody_approver: nextApprover.id,
                        custbody_approval_status: 'Escalated - Overdue'
                    }
                });

                // Send notification
                sendEscalationEmail(poId, nextApprover);
            }

            return true;  // Continue iteration
        });
    }

    function sendEscalationEmail(poId, approver) {
        email.send({
            author: SENDER_ID,
            recipients: approver.email,
            subject: 'Escalated Purchase Order Approval Required',
            body: `Purchase Order ${poId} has been escalated to you for approval due to timeout.`
        });
    }

    return {
        execute: execute
    };
});
```

## Parallel Approval Workflow

Handle scenarios requiring multiple approvers to approve independently.

**State Tracking:**

```javascript
function checkAllApproversComplete(purchaseOrderId) {
    const po = record.load({
        type: record.Type.PURCHASE_ORDER,
        id: purchaseOrderId
    });

    const deptApprovalStatus = po.getValue({ fieldId: 'custbody_dept_approval' });
    const financeApprovalStatus = po.getValue({ fieldId: 'custbody_finance_approval' });

    if (deptApprovalStatus === 'Approved' && financeApprovalStatus === 'Approved') {
        // All approvals complete
        po.setValue({
            fieldId: 'approvalstatus',
            value: 2  // Approved
        });
        po.setValue({
            fieldId: 'custbody_approval_status',
            value: 'Fully Approved'
        });
        po.save();
    } else if (deptApprovalStatus === 'Rejected' || financeApprovalStatus === 'Rejected') {
        // Any rejection fails the approval
        po.setValue({
            fieldId: 'approvalstatus',
            value: 3  // Rejected
        });
        po.setValue({
            fieldId: 'custbody_approval_status',
            value: 'Rejected'
        });
        po.save();
    }
    // Otherwise, still pending partial approvals
}
```

## Best Practices

### Custom Fields

**Required Custom Fields:**
```javascript
// Transaction Body Fields
custbody_approver               // Employee (current approver)
custbody_approval_status        // Text (Pending, Approved, Rejected, Escalated)
custbody_approval_level         // List (Manager, Director, VP, CFO)
custbody_approval_history       // Long Text (audit trail)
custbody_approval_date          // Date (when approved)

// Employee Fields
custentity_approval_limit       // Currency (maximum approval amount)
custentity_approval_groups      // Multi-Select List (approval domains)
```

### Audit Trail

**Log all approval actions:**

```javascript
function logApprovalAction(recordId, action, approver, comments) {
    const timestamp = new Date().toISOString();
    const logEntry = `[${timestamp}] ${action} by ${approver}: ${comments}`;

    const currentRecord = record.load({
        type: record.Type.PURCHASE_ORDER,
        id: recordId
    });

    const currentHistory = currentRecord.getValue({ fieldId: 'custbody_approval_history' }) || '';
    const updatedHistory = currentHistory + '\n' + logEntry;

    currentRecord.setValue({
        fieldId: 'custbody_approval_history',
        value: updatedHistory
    });

    currentRecord.save();
}
```

### Error Handling

```javascript
function routeForApproval(recordId, approverId) {
    try {
        const rec = record.load({
            type: record.Type.PURCHASE_ORDER,
            id: recordId
        });

        rec.setValue({
            fieldId: 'custbody_approver',
            value: approverId
        });

        rec.save();

    } catch (e) {
        log.error({
            title: 'Approval Routing Failed',
            details: `Record: ${recordId}, Approver: ${approverId}, Error: ${e.message}`
        });

        // Send alert to admin
        email.send({
            author: ADMIN_ID,
            recipients: ADMIN_EMAIL,
            subject: 'Approval Routing Error',
            body: `Failed to route ${recordId} to approver ${approverId}. Error: ${e.message}`
        });

        throw e;  // Re-throw to prevent record save
    }
}
```

### Performance Optimization

**Avoid N+1 query problem when batch routing:**

```javascript
// Bad: Individual lookups in loop
for (const recordId of recordIds) {
    const approver = getApproverForRecord(recordId);  // Separate query each iteration
    routeRecord(recordId, approver);
}

// Good: Batch lookup first
const approverMap = batchGetApprovers(recordIds);  // Single search
for (const recordId of recordIds) {
    const approver = approverMap[recordId];
    routeRecord(recordId, approver);
}

function batchGetApprovers(recordIds) {
    const approvers = {};

    const searchResults = search.create({
        type: search.Type.PURCHASE_ORDER,
        filters: [
            ['internalid', 'anyof', recordIds]
        ],
        columns: ['internalid', 'department', 'total']
    }).run().getRange({ start: 0, end: 1000 });

    searchResults.forEach((result) => {
        const id = result.getValue({ name: 'internalid' });
        const dept = result.getText({ name: 'department' });
        const total = parseFloat(result.getValue({ name: 'total' }));

        approvers[id] = determineApprover(dept, total);
    });

    return approvers;
}
```

## Related Documentation

- **[Notification Automation](notification-automation.md)** - Email/SMS notifications for approval events
- **[Custom Workflows](custom-workflows.md)** - Workflow Action Script patterns
- **[Journal Entries](../finance/journal-entries.md)** - Approval routing for JEs

**External References:**
- [NetSuite Workflow Guide](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/chapter_N286696.html)
- [User Event Scripts](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4387799721.html)

---

*Generic approval routing patterns for NetSuite transaction workflows*
