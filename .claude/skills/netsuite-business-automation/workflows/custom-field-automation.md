# Custom Field Automation

SuiteScript patterns for reading and writing NetSuite custom fields in business automation workflows.

## Overview

Custom fields (custentity_*, custbody_*, custitem_*) are frequently used in business automation workflows for:
- Routing logic (approval workflows based on region)
- Field population (auto-calculate credit limits)
- Validation rules (payment method restrictions)
- Status tracking (custom workflow states)

**Challenge:** Custom fields can be added/removed by admins, requiring defensive coding patterns.

---

## Reading Custom Fields

### Basic Field Read

```javascript
/**
 * Read custom field value from record
 * @governance 0 units
 */
function getCustomFieldValue(record) {
    // Entity custom field
    var region = record.getValue({fieldId: 'custentity_region'});

    // Body custom field (transaction)
    var department = record.getValue({fieldId: 'custbody_department'});

    // Item custom field
    var size = record.getValue({fieldId: 'custitem_size'});

    log.debug('Field Values', {region, department, size});
}
```

### Defensive Field Read (Recommended)

Check if field exists before reading to handle schema changes gracefully:

```javascript
/**
 * Safely read custom field (handles field removal)
 * @param {Record} record - NetSuite record
 * @param {string} fieldId - Field ID to read
 * @param {*} defaultValue - Value if field missing/empty
 * @returns {*} Field value or default
 */
function getCustomFieldSafe(record, fieldId, defaultValue) {
    try {
        // Check if field exists
        var field = record.getField({fieldId: fieldId});

        if (!field) {
            log.debug('Field Not Found', fieldId);
            return defaultValue;
        }

        // Get value
        var value = record.getValue({fieldId: fieldId});

        // Return value or default if empty
        return value || defaultValue;

    } catch (e) {
        log.error('Error Reading Field', {fieldId, error: e.message});
        return defaultValue;
    }
}

// Usage in User Event script
function beforeSubmit(context) {
    var record = context.newRecord;

    // Defensive reads with defaults
    var region = getCustomFieldSafe(record, 'custentity_region', 'Unknown');
    var paymentMethod = getCustomFieldSafe(record, 'custentity_payment_method', 'Check');

    log.audit('Vendor Data', {region, paymentMethod});
}
```

**Benefits:**
- No errors if field removed from NetSuite
- Graceful degradation
- Workflow continues functioning

---

## Writing Custom Fields

### Basic Field Write

```javascript
/**
 * Set custom field values
 * @governance 0 units (field set operations are free)
 */
function setCustomFields(record) {
    // Set entity custom field
    record.setValue({
        fieldId: 'custentity_region',
        value: 'West'
    });

    // Set body custom field
    record.setValue({
        fieldId: 'custbody_department',
        value: '100'  // Department ID
    });

    // Set item custom field
    record.setValue({
        fieldId: 'custitem_size',
        value: 'Large'
    });
}
```

### Conditional Field Write

```javascript
/**
 * Conditionally set custom fields based on business rules
 */
function applyBusinessRules(record) {
    var balance = record.getValue({fieldId: 'balance'});
    var existingTier = record.getValue({fieldId: 'custentity_vendor_tier'});

    // Auto-assign vendor tier based on balance
    var newTier;
    if (balance > 1000000) {
        newTier = 'Tier 1 - Strategic';
    } else if (balance > 100000) {
        newTier = 'Tier 2 - Major';
    } else {
        newTier = 'Tier 3 - Standard';
    }

    // Only update if changed
    if (newTier !== existingTier) {
        record.setValue({
            fieldId: 'custentity_vendor_tier',
            value: newTier
        });

        log.audit('Tier Updated', {
            vendor: record.getValue({fieldId: 'entityid'}),
            oldTier: existingTier,
            newTier: newTier
        });
    }
}
```

---

## Workflow Routing by Custom Fields

### Approval Routing

```javascript
/**
 * Route approval based on vendor region
 * @NApiVersion 2.1
 * @NScriptType UserEventScript
 */
define(['N/record', 'N/runtime', 'N/log'], function(record, runtime, log) {

    function beforeSubmit(context) {
        if (context.type !== context.UserEventType.CREATE) {
            return;
        }

        var vendorRecord = context.newRecord;

        // Get region from custom field
        var region = getCustomFieldSafe(vendorRecord, 'custentity_region', 'Unknown');

        // Route based on region
        var approver;
        switch (region) {
            case 'West':
                approver = '12345';  // West Regional Manager
                break;
            case 'East':
                approver = '12346';  // East Regional Manager
                break;
            case 'Central':
                approver = '12347';  // Central Regional Manager
                break;
            default:
                approver = '10001';  // Default approver
        }

        // Set approver custom field
        vendorRecord.setValue({
            fieldId: 'custentity_approver',
            value: approver
        });

        log.audit('Approval Routed', {region, approver});
    }

    return {
        beforeSubmit: beforeSubmit
    };
});
```

### Status-Based Automation

```javascript
/**
 * Automated actions based on custom status field
 */
function handleVendorStatus(context) {
    var record = context.newRecord;

    var status = getCustomFieldSafe(record, 'custentity_vendor_status', 'Active');

    // Take action based on status
    switch (status) {
        case 'Pending Review':
            // Send notification to procurement team
            notifyProcurement(record);
            break;

        case 'Approved':
            // Set inactive flag to false
            record.setValue({fieldId: 'isinactive', value: false});
            // Set approval date
            record.setValue({
                fieldId: 'custentity_approval_date',
                value: new Date()
            });
            break;

        case 'Suspended':
            // Set inactive flag to true
            record.setValue({fieldId: 'isinactive', value: true});
            // Log suspension
            logSuspension(record);
            break;
    }
}
```

---

## Custom Field Validation

### Validate Field Combinations

```javascript
/**
 * Validate custom field combinations
 * @param {Record} record
 * @throws {Error} if validation fails
 */
function validateCustomFields(record) {
    var paymentMethod = getCustomFieldSafe(record, 'custentity_payment_method', '');
    var bankAccount = getCustomFieldSafe(record, 'custentity_bank_account', '');

    // Payment method ACH requires bank account
    if (paymentMethod === 'ACH' && !bankAccount) {
        throw new Error('Bank account required for ACH payment method');
    }

    // Validate region for US vendors
    var country = record.getValue({fieldId: 'country'});
    var region = getCustomFieldSafe(record, 'custentity_region', '');

    if (country === 'US' && !region) {
        throw new Error('Region required for US vendors');
    }
}

// Use in saveRecord (Client Script)
function saveRecord(context) {
    try {
        validateCustomFields(context.currentRecord);
        return true;  // Allow save
    } catch (e) {
        alert('Validation Error: ' + e.message);
        return false;  // Prevent save
    }
}
```

---

## Field Change Detection

### Detect Custom Field Changes

```javascript
/**
 * Detect custom field changes in beforeSubmit
 * @param {UserEventContext} context
 */
function detectFieldChanges(context) {
    if (context.type !== context.UserEventType.EDIT) {
        return;  // Only check on edits
    }

    var newRecord = context.newRecord;
    var oldRecord = context.oldRecord;

    // Check if region changed
    var oldRegion = oldRecord.getValue({fieldId: 'custentity_region'});
    var newRegion = newRecord.getValue({fieldId: 'custentity_region'});

    if (oldRegion !== newRegion) {
        log.audit('Region Changed', {
            vendor: newRecord.getValue({fieldId: 'entityid'}),
            from: oldRegion,
            to: newRegion
        });

        // Trigger re-routing or notifications
        handleRegionChange(newRecord, oldRegion, newRegion);
    }
}
```

---

## Scheduled Script Patterns

### Bulk Update Custom Fields

```javascript
/**
 * Scheduled Script to update custom fields in bulk
 * @NApiVersion 2.1
 * @NScriptType ScheduledScript
 */
define(['N/record', 'N/search', 'N/log'], function(record, search, log) {

    function execute(context) {
        // Search for vendors needing tier update
        var vendorSearch = search.create({
            type: search.Type.VENDOR,
            filters: [
                ['isinactive', 'is', 'F']
            ],
            columns: ['entityid', 'balance', 'custentity_vendor_tier']
        });

        var searchResults = vendorSearch.run().getRange({start: 0, end: 1000});

        searchResults.forEach(function(result) {
            try {
                var vendorId = result.id;
                var balance = parseFloat(result.getValue({name: 'balance'})) || 0;

                // Calculate tier
                var tier;
                if (balance > 1000000) {
                    tier = 'Tier 1';
                } else if (balance > 100000) {
                    tier = 'Tier 2';
                } else {
                    tier = 'Tier 3';
                }

                // Update if changed
                var currentTier = result.getValue({name: 'custentity_vendor_tier'});
                if (tier !== currentTier) {
                    record.submitFields({
                        type: record.Type.VENDOR,
                        id: vendorId,
                        values: {
                            'custentity_vendor_tier': tier
                        }
                    });

                    log.audit('Tier Updated', {vendorId, tier});
                }

            } catch (e) {
                log.error('Error Updating Vendor', {vendorId, error: e.message});
            }
        });

        log.audit('Bulk Update Complete', {processed: searchResults.length});
    }

    return {
        execute: execute
    };
});
```

---

## Best Practices

1. **Defensive reads** - Always use getCustomFieldSafe() pattern
2. **Check field exists** - Use getField() before getValue()
3. **Handle missing fields** - Provide sensible defaults
4. **Log field changes** - Audit trail for custom field updates
5. **Validate combinations** - Business rules for field dependencies
6. **Bulk updates carefully** - Handle errors gracefully in loops

---

## Related Documentation

**NetSuite Developer Skill:**
- `patterns/custom-fields.md` - Custom field types and classification
- `suitescript/user-events.md` - User Event script patterns
- `suitescript/scheduled.md` - Scheduled script patterns

**This Skill:**
- [workflows/approval-routing.md](approval-routing.md) - Approval workflows
- [workflows/notification-automation.md](notification-automation.md) - Notifications

**Reference Implementation:**
- `/opt/ns/apps/vendor-analysis/` - Custom field processing in integrations

---

## Summary

**Key Points:**

1. **Defensive reads** - Check field exists before reading (handle removal)
2. **Sensible defaults** - Always provide default values
3. **Detect changes** - Compare oldRecord vs newRecord
4. **Validation** - Check field combinations and business rules
5. **Bulk updates** - Use submitFields for performance
6. **Error handling** - Try-catch for field operations

**Custom field automation requires defensive patterns to handle schema evolution without breaking workflows.**
