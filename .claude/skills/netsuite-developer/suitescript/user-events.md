# User Event Scripts

User Event scripts execute on the server in response to record lifecycle events (create, load, update, copy, delete, submit).

## Entry Points

### beforeLoad
Executes before a record is loaded in standard record forms (view, edit, create, copy modes).

**Use Cases:**
- Customize form UI (add/remove fields, buttons)
- Set default values
- Display custom messages
- Conditional field display

**Context Parameters:**
- `scriptContext.newRecord` - The record being loaded
- `scriptContext.type` - Event type (view, edit, create, copy)
- `scriptContext.form` - The UI form object

**Example:**
```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType UserEventScript
 */
define(['N/ui/serverWidget', 'N/log'],
    (serverWidget, log) => {

        function beforeLoad(scriptContext) {
            try {
                const newRecord = scriptContext.newRecord;
                const form = scriptContext.form;

                // Add custom field to form
                const customField = form.addField({
                    id: 'custpage_custom_field',
                    type: serverWidget.FieldType.TEXT,
                    label: 'Custom Field'
                });

                // Set default value for new records
                if (scriptContext.type === scriptContext.UserEventType.CREATE) {
                    newRecord.setValue({
                        fieldId: 'memo',
                        value: 'Created via User Event Script'
                    });
                }

                // Add custom button
                form.addButton({
                    id: 'custpage_custom_button',
                    label: 'Custom Action',
                    functionName: 'customButtonAction'
                });

                log.debug('beforeLoad', 'Form customized successfully');

            } catch (e) {
                log.error('beforeLoad Error', e);
            }
        }

        return {
            beforeLoad: beforeLoad
        };
    }
);
```

### beforeSubmit
Executes before a record is written to the database (create, update, delete, xedit).

**Use Cases:**
- Field validation
- Data transformation
- Calculate derived values
- Prevent save with errors

**Context Parameters:**
- `scriptContext.newRecord` - The record being submitted (with new values)
- `scriptContext.oldRecord` - The record before changes (not available for create)
- `scriptContext.type` - Event type (create, edit, delete, xedit)

**Example:**
```javascript
function beforeSubmit(scriptContext) {
    try {
        const newRecord = scriptContext.newRecord;
        const oldRecord = scriptContext.oldRecord;

        // Validation: Ensure total is not negative
        const total = newRecord.getValue({ fieldId: 'total' });
        if (total < 0) {
            throw new Error('Total cannot be negative');
        }

        // Calculate field value
        const quantity = newRecord.getValue({ fieldId: 'quantity' });
        const rate = newRecord.getValue({ fieldId: 'rate' });
        newRecord.setValue({
            fieldId: 'amount',
            value: quantity * rate
        });

        // Track changes (edit mode only)
        if (scriptContext.type === scriptContext.UserEventType.EDIT) {
            const oldStatus = oldRecord.getValue({ fieldId: 'status' });
            const newStatus = newRecord.getValue({ fieldId: 'status' });

            if (oldStatus !== newStatus) {
                log.audit('Status Changed', {
                    from: oldStatus,
                    to: newStatus,
                    recordId: newRecord.id
                });
            }
        }

        log.debug('beforeSubmit', 'Validation and calculations completed');

    } catch (e) {
        log.error('beforeSubmit Error', e);
        throw e; // Re-throw to prevent save
    }
}
```

### afterSubmit
Executes after a record is written to the database.

**Use Cases:**
- Create related records
- Update other records
- Send notifications
- Log audit trail
- Trigger external systems

**Context Parameters:**
- `scriptContext.newRecord` - The record just submitted (with ID)
- `scriptContext.oldRecord` - The record before changes (not available for create)
- `scriptContext.type` - Event type (create, edit, delete, xedit)

**Example:**
```javascript
function afterSubmit(scriptContext) {
    try {
        const newRecord = scriptContext.newRecord;
        const recordId = newRecord.id;
        const recordType = newRecord.type;

        // Create related record (example: task)
        if (scriptContext.type === scriptContext.UserEventType.CREATE) {
            const taskRecord = record.create({
                type: record.Type.TASK,
                isDynamic: true
            });

            taskRecord.setValue({
                fieldId: 'title',
                value: `Follow up on ${recordType} ${recordId}`
            });

            taskRecord.setValue({
                fieldId: 'transaction',
                value: recordId
            });

            const taskId = taskRecord.save();
            log.audit('Task Created', `Task ${taskId} created for record ${recordId}`);
        }

        // Update related record
        if (scriptContext.type === scriptContext.UserEventType.EDIT) {
            const customerId = newRecord.getValue({ fieldId: 'entity' });

            record.submitFields({
                type: record.Type.CUSTOMER,
                id: customerId,
                values: {
                    custentity_last_order_date: new Date()
                }
            });
        }

        // Send email notification
        email.send({
            author: runtime.getCurrentUser().id,
            recipients: 'admin@company.com',
            subject: `Record ${recordType} Updated`,
            body: `Record ID: ${recordId} was updated`
        });

        log.debug('afterSubmit', 'Post-processing completed');

    } catch (e) {
        log.error('afterSubmit Error', e);
        // Don't throw - record is already saved
    }
}
```

## Complete Example: Sales Order Validation

```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType UserEventScript
 * @NModuleScope SameAccount
 */
define(['N/record', 'N/search', 'N/email', 'N/runtime', 'N/log', 'N/error'],
    (record, search, email, runtime, log, error) => {

        /**
         * Before Load - Customize form based on user role
         */
        function beforeLoad(scriptContext) {
            try {
                const form = scriptContext.form;
                const currentUser = runtime.getCurrentUser();

                // Hide discount field for non-managers
                if (currentUser.role !== 'manager') {
                    const discountField = form.getField({ id: 'discountrate' });
                    if (discountField) {
                        discountField.updateDisplayType({
                            displayType: serverWidget.FieldDisplayType.HIDDEN
                        });
                    }
                }

            } catch (e) {
                log.error('beforeLoad Error', e);
            }
        }

        /**
         * Before Submit - Validate order and calculate totals
         */
        function beforeSubmit(scriptContext) {
            try {
                const newRecord = scriptContext.newRecord;
                const type = scriptContext.type;

                // Only validate on create and edit
                if (type !== scriptContext.UserEventType.CREATE &&
                    type !== scriptContext.UserEventType.EDIT) {
                    return;
                }

                // Validate customer credit limit
                const customerId = newRecord.getValue({ fieldId: 'entity' });
                const orderTotal = newRecord.getValue({ fieldId: 'total' });

                const customerSearch = search.lookupFields({
                    type: search.Type.CUSTOMER,
                    id: customerId,
                    columns: ['creditlimit', 'balance']
                });

                const creditLimit = parseFloat(customerSearch.creditlimit) || 0;
                const currentBalance = parseFloat(customerSearch.balance) || 0;
                const newBalance = currentBalance + orderTotal;

                if (creditLimit > 0 && newBalance > creditLimit) {
                    throw error.create({
                        name: 'CREDIT_LIMIT_EXCEEDED',
                        message: `Order would exceed credit limit. Limit: ${creditLimit}, New Balance: ${newBalance}`,
                        notifyOff: false
                    });
                }

                // Validate line items
                const lineCount = newRecord.getLineCount({ sublistId: 'item' });

                for (let i = 0; i < lineCount; i++) {
                    const itemId = newRecord.getSublistValue({
                        sublistId: 'item',
                        fieldId: 'item',
                        line: i
                    });

                    const quantity = newRecord.getSublistValue({
                        sublistId: 'item',
                        fieldId: 'quantity',
                        line: i
                    });

                    // Check inventory availability
                    const itemSearch = search.lookupFields({
                        type: search.Type.ITEM,
                        id: itemId,
                        columns: ['quantityavailable', 'displayname']
                    });

                    const available = parseFloat(itemSearch.quantityavailable) || 0;

                    if (quantity > available) {
                        log.audit('Inventory Warning', {
                            item: itemSearch.displayname,
                            requested: quantity,
                            available: available
                        });
                    }
                }

                log.debug('beforeSubmit', 'Validation completed successfully');

            } catch (e) {
                log.error('beforeSubmit Error', e);
                throw e;
            }
        }

        /**
         * After Submit - Create follow-up tasks and notifications
         */
        function afterSubmit(scriptContext) {
            try {
                const newRecord = scriptContext.newRecord;
                const type = scriptContext.type;
                const recordId = newRecord.id;

                // Only process on create
                if (type !== scriptContext.UserEventType.CREATE) {
                    return;
                }

                const customerId = newRecord.getValue({ fieldId: 'entity' });
                const salesRep = newRecord.getValue({ fieldId: 'salesrep' });
                const orderTotal = newRecord.getValue({ fieldId: 'total' });

                // Create follow-up task for high-value orders
                if (orderTotal > 10000) {
                    const taskRecord = record.create({
                        type: record.Type.TASK,
                        isDynamic: true
                    });

                    taskRecord.setValue({
                        fieldId: 'title',
                        value: `High-Value Order Follow-up: SO ${recordId}`
                    });

                    taskRecord.setValue({
                        fieldId: 'assigned',
                        value: salesRep || runtime.getCurrentUser().id
                    });

                    taskRecord.setValue({
                        fieldId: 'transaction',
                        value: recordId
                    });

                    taskRecord.setValue({
                        fieldId: 'duedate',
                        value: new Date(Date.now() + (2 * 24 * 60 * 60 * 1000)) // 2 days
                    });

                    const taskId = taskRecord.save();
                    log.audit('Task Created', `Follow-up task ${taskId} created`);
                }

                // Send notification email
                if (salesRep) {
                    email.send({
                        author: runtime.getCurrentUser().id,
                        recipients: salesRep,
                        subject: `New Sales Order Created: ${recordId}`,
                        body: `A new sales order has been created.\n\nOrder ID: ${recordId}\nCustomer ID: ${customerId}\nTotal: $${orderTotal}`
                    });
                }

                // Update customer last order date
                record.submitFields({
                    type: record.Type.CUSTOMER,
                    id: customerId,
                    values: {
                        custentity_last_order_date: new Date(),
                        custentity_last_order_amount: orderTotal
                    },
                    options: {
                        enableSourcing: false,
                        ignoreMandatoryFields: true
                    }
                });

                log.audit('afterSubmit', `Sales Order ${recordId} post-processing completed`);

            } catch (e) {
                log.error('afterSubmit Error', e);
            }
        }

        return {
            beforeLoad: beforeLoad,
            beforeSubmit: beforeSubmit,
            afterSubmit: afterSubmit
        };
    }
);
```

## Deployment Configuration

### Script Record (XML)
```xml
<userEventScript scriptid="customscript_sales_order_validation">
    <name>Sales Order Validation</name>
    <scriptfile>[/SuiteScripts/sales_order_validation.js]</scriptfile>
    <deployments>
        <deployment>
            <scriptid>customdeploy_sales_order_validation</scriptid>
            <status>RELEASED</status>
            <recordtype>salesorder</recordtype>
            <eventtype>create</eventtype>
            <eventtype>edit</eventtype>
            <loglevel>DEBUG</loglevel>
        </deployment>
    </deployments>
</userEventScript>
```

## Best Practices

### DO's ✅
- Always wrap code in try-catch blocks
- Log important operations and errors
- Use governance-efficient search methods
- Validate all inputs
- Set appropriate log levels
- Use specific error messages
- Test in sandbox first
- Check scriptContext.type before processing

### DON'Ts ❌
- Don't load the same record multiple times
- Don't perform heavy operations in beforeLoad
- Don't throw errors in afterSubmit (record is already saved)
- Don't forget to handle all event types
- Don't exceed governance limits
- Don't modify the record in afterSubmit
- Don't perform UI operations on server scripts

### Governance Considerations
- beforeLoad: Low governance (UI customization only)
- beforeSubmit: Medium governance (calculations, validations)
- afterSubmit: High governance (can create/update other records)

Use `runtime.getCurrentScript().getRemainingUsage()` to monitor governance.

## Common Patterns

### Prevent Deletion
```javascript
function beforeSubmit(scriptContext) {
    if (scriptContext.type === scriptContext.UserEventType.DELETE) {
        const record = scriptContext.newRecord;
        const status = record.getValue({ fieldId: 'status' });

        if (status === 'Closed') {
            throw error.create({
                name: 'CANNOT_DELETE',
                message: 'Cannot delete closed records'
            });
        }
    }
}
```

### Track Field Changes
```javascript
function afterSubmit(scriptContext) {
    if (scriptContext.type === scriptContext.UserEventType.EDIT) {
        const newRecord = scriptContext.newRecord;
        const oldRecord = scriptContext.oldRecord;

        const fieldsToTrack = ['amount', 'status', 'probability'];

        fieldsToTrack.forEach(fieldId => {
            const oldValue = oldRecord.getValue({ fieldId });
            const newValue = newRecord.getValue({ fieldId });

            if (oldValue !== newValue) {
                log.audit('Field Changed', {
                    field: fieldId,
                    oldValue: oldValue,
                    newValue: newValue,
                    recordId: newRecord.id,
                    changedBy: runtime.getCurrentUser().id
                });
            }
        });
    }
}
```

### Conditional Email Notifications
```javascript
function afterSubmit(scriptContext) {
    const newRecord = scriptContext.newRecord;
    const type = scriptContext.type;

    // Only notify on status change to "Approved"
    if (type === scriptContext.UserEventType.EDIT) {
        const oldStatus = scriptContext.oldRecord.getValue({ fieldId: 'status' });
        const newStatus = newRecord.getValue({ fieldId: 'status' });

        if (oldStatus !== 'Approved' && newStatus === 'Approved') {
            const owner = newRecord.getValue({ fieldId: 'owner' });

            email.send({
                author: runtime.getCurrentUser().id,
                recipients: owner,
                subject: `Record ${newRecord.id} Approved`,
                body: 'Your request has been approved.'
            });
        }
    }
}
```

## Related Documentation
- [Error Handling Patterns](../patterns/error-handling.md)
- [Governance Management](../patterns/governance.md)
- [Performance Optimization](../patterns/performance.md)
- [Local KB: SuiteScript Modules](/opt/ns/kb/suitescript-modules.md)
