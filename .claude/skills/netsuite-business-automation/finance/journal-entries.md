# Journal Entry Automation

Automated journal entry creation, reversal, and intercompany eliminations using SuiteScript 2.x.

## Overview

Journal entry automation eliminates manual data entry, ensures accounting accuracy, and accelerates month-end close processes. Common automation scenarios include:

**Business Benefits:**
- Reduce close time by 30-50% through automation
- Eliminate manual data entry errors
- Ensure consistent accounting treatment
- Create audit trails for all automated entries
- Enable real-time accruals and adjustments

**Typical Automation Rate:** 60-80% of routine journal entries can be automated

## Basic Journal Entry Creation

### User Event Script - afterSubmit

Automatically create journal entries when triggering events occur (invoice posted, payment received, etc.).

```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType UserEventScript
 * @NModuleScope SameAccount
 */
define(['N/record', 'N/log', 'N/error'], (record, log, error) => {

    /**
     * After invoice is created, create revenue recognition journal entry
     */
    function afterSubmit(context) {
        if (context.type !== context.UserEventType.CREATE) {
            return;
        }

        try {
            const invoice = context.newRecord;
            const invoiceId = invoice.id;
            const invoiceTotal = invoice.getValue({ fieldId: 'total' });
            const customerId = invoice.getValue({ fieldId: 'entity' });
            const currency = invoice.getValue({ fieldId: 'currency' });

            // Create journal entry for revenue recognition
            const je = record.create({
                type: record.Type.JOURNAL_ENTRY,
                isDynamic: true
            });

            // Set header fields
            je.setValue({ fieldId: 'subsidiary', value: invoice.getValue({ fieldId: 'subsidiary' }) });
            je.setValue({ fieldId: 'currency', value: currency });
            je.setValue({ fieldId: 'memo', value: `Revenue recognition for Invoice ${invoiceId}` });

            // Debit: Accounts Receivable
            je.selectNewLine({ sublistId: 'line' });
            je.setCurrentSublistValue({
                sublistId: 'line',
                fieldId: 'account',
                value: AR_ACCOUNT_ID // From configuration
            });
            je.setCurrentSublistValue({
                sublistId: 'line',
                fieldId: 'debit',
                value: invoiceTotal
            });
            je.setCurrentSublistValue({
                sublistId: 'line',
                fieldId: 'entity',
                value: customerId
            });
            je.commitLine({ sublistId: 'line' });

            // Credit: Revenue
            je.selectNewLine({ sublistId: 'line' });
            je.setCurrentSublistValue({
                sublistId: 'line',
                fieldId: 'account',
                value: REVENUE_ACCOUNT_ID // From configuration
            });
            je.setCurrentSublistValue({
                sublistId: 'line',
                fieldId: 'credit',
                value: invoiceTotal
            });
            je.commitLine({ sublistId: 'line' });

            const jeId = je.save();
            log.audit({
                title: 'JE Created',
                details: `Journal Entry ${jeId} created for Invoice ${invoiceId}`
            });

        } catch (e) {
            log.error({
                title: 'JE Creation Failed',
                details: e.message
            });
            // Re-throw to prevent invoice save if JE creation is critical
            // throw e; // Uncomment if JE creation should block invoice
        }
    }

    return {
        afterSubmit: afterSubmit
    };
});
```

**Key Points:**
- Use `isDynamic: true` for line-by-line entry (easier debugging)
- Always balance debits and credits
- Include reference to source transaction in memo
- Log all automated JE creation for audit trail
- Decide whether JE creation failure should block source transaction

**Oracle NetSuite Documentation:**
- N/record API: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4407050795.html
- See also: `/opt/ns/kb/suitescript-modules.md` (N/record methods)

## Automatic Journal Entry Reversal

### Scheduled Script - Monthly Accrual Reversal

Automatically reverse accrual journal entries on the first day of the next period.

```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType ScheduledScript
 */
define(['N/search', 'N/record', 'N/log'], (search, record, log) => {

    function execute(context) {
        const accrualJEs = findAccrualJournalEntries();
        let successCount = 0;
        let failCount = 0;

        for (const jeId of accrualJEs) {
            try {
                const reversalId = reverseJournalEntry(jeId);
                log.audit({
                    title: 'JE Reversed',
                    details: `Original JE ${jeId}, Reversal JE ${reversalId}`
                });
                successCount++;
            } catch (e) {
                log.error({
                    title: 'Reversal Failed',
                    details: `JE ${jeId}: ${e.message}`
                });
                failCount++;
            }
        }

        log.audit({
            title: 'Reversal Complete',
            details: `Success: ${successCount}, Failed: ${failCount}`
        });
    }

    function findAccrualJournalEntries() {
        const results = [];

        // Find JEs marked for reversal from prior period
        const jeSearch = search.create({
            type: search.Type.JOURNAL_ENTRY,
            filters: [
                ['custbody_reverse_next_period', 'is', 'T'], // Custom checkbox field
                'AND',
                ['postingperiod', 'is', '@LASTFISCALPERIOD'] // Prior period
            ],
            columns: ['internalid']
        });

        jeSearch.run().each((result) => {
            results.push(result.id);
            return true; // Continue iteration
        });

        return results;
    }

    function reverseJournalEntry(originalJeId) {
        // Load original JE
        const originalJe = record.load({
            type: record.Type.JOURNAL_ENTRY,
            id: originalJeId,
            isDynamic: false
        });

        // Create reversal JE
        const reversalJe = record.create({
            type: record.Type.JOURNAL_ENTRY,
            isDynamic: false
        });

        // Copy header fields
        reversalJe.setValue({
            fieldId: 'subsidiary',
            value: originalJe.getValue({ fieldId: 'subsidiary' })
        });
        reversalJe.setValue({
            fieldId: 'currency',
            value: originalJe.getValue({ fieldId: 'currency' })
        });
        reversalJe.setValue({
            fieldId: 'memo',
            value: `Reversal of JE ${originalJeId}`
        });

        // Copy lines with reversed debits/credits
        const lineCount = originalJe.getLineCount({ sublistId: 'line' });

        for (let i = 0; i < lineCount; i++) {
            const account = originalJe.getSublistValue({
                sublistId: 'line',
                fieldId: 'account',
                line: i
            });
            const debit = originalJe.getSublistValue({
                sublistId: 'line',
                fieldId: 'debit',
                line: i
            });
            const credit = originalJe.getSublistValue({
                sublistId: 'line',
                fieldId: 'credit',
                line: i
            });

            reversalJe.setSublistValue({
                sublistId: 'line',
                fieldId: 'account',
                line: i,
                value: account
            });

            // Reverse: debit becomes credit, credit becomes debit
            if (debit) {
                reversalJe.setSublistValue({
                    sublistId: 'line',
                    fieldId: 'credit',
                    line: i,
                    value: debit
                });
            }
            if (credit) {
                reversalJe.setSublistValue({
                    sublistId: 'line',
                    fieldId: 'debit',
                    line: i,
                    value: credit
                });
            }
        }

        const reversalId = reversalJe.save();

        // Mark original as reversed
        record.submitFields({
            type: record.Type.JOURNAL_ENTRY,
            id: originalJeId,
            values: {
                'custbody_reversed_by': reversalId,
                'custbody_reverse_next_period': false
            }
        });

        return reversalId;
    }

    return {
        execute: execute
    };
});
```

**Key Design Patterns:**
- Use custom field (`custbody_reverse_next_period`) to flag JEs for reversal
- Load with `isDynamic: false` for better performance in batch operations
- Reverse debits/credits automatically
- Link original and reversal JEs via custom field
- Schedule to run on 1st of month during off-peak hours

## Intercompany Journal Entries

### Automatic Elimination Entries

Create elimination journal entries for intercompany transactions during consolidation.

```javascript
/**
 * Create intercompany elimination entry
 */
function createEliminationEntry(intercompanyTxn) {
    const je = record.create({
        type: record.Type.JOURNAL_ENTRY,
        isDynamic: true
    });

    // Set to parent company subsidiary for consolidation
    je.setValue({ fieldId: 'subsidiary', value: PARENT_COMPANY_ID });
    je.setValue({ fieldId: 'memo', value: `IC elimination for ${intercompanyTxn.id}` });

    // Debit: Eliminate intercompany receivable
    je.selectNewLine({ sublistId: 'line' });
    je.setCurrentSublistValue({
        sublistId: 'line',
        fieldId: 'account',
        value: IC_PAYABLE_ACCOUNT_ID
    });
    je.setCurrentSublistValue({
        sublistId: 'line',
        fieldId: 'debit',
        value: intercompanyTxn.amount
    });
    je.setCurrentSublistValue({
        sublistId: 'line',
        fieldId: 'eliminate',
        value: true // NetSuite consolidation flag
    });
    je.commitLine({ sublistId: 'line' });

    // Credit: Eliminate intercompany payable
    je.selectNewLine({ sublistId: 'line' });
    je.setCurrentSublistValue({
        sublistId: 'line',
        fieldId: 'account',
        value: IC_RECEIVABLE_ACCOUNT_ID
    });
    je.setCurrentSublistValue({
        sublistId: 'line',
        fieldId: 'credit',
        value: intercompanyTxn.amount
    });
    je.setCurrentSublistValue({
        sublistId: 'line',
        fieldId: 'eliminate',
        value: true
    });
    je.commitLine({ sublistId: 'line' });

    return je.save();
}
```

**Intercompany Best Practices:**
- Use NetSuite's built-in `eliminate` flag on JE lines
- Post elimination entries to parent subsidiary
- Match elimination amounts to intercompany transaction amounts
- Run elimination script as part of period close checklist
- Maintain audit trail linking eliminations to source transactions

## Performance Optimization

### Bulk Journal Entry Creation

Use Map/Reduce for creating >100 journal entries from source data.

```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType MapReduceScript
 */
define(['N/record', 'N/search'], (record, search) => {

    function getInputData() {
        // Return search of source transactions requiring JEs
        return search.create({
            type: 'transaction',
            filters: [
                ['custbody_je_required', 'is', 'T'],
                'AND',
                ['custbody_je_created', 'is', 'F']
            ]
        });
    }

    function map(context) {
        const searchResult = JSON.parse(context.value);
        const txnId = searchResult.id;

        try {
            // Create JE for this transaction
            const jeId = createJournalEntryForTransaction(txnId);

            // Mark source transaction
            record.submitFields({
                type: searchResult.recordType,
                id: txnId,
                values: { 'custbody_je_created': true }
            });

            context.write({
                key: txnId,
                value: { success: true, jeId: jeId }
            });
        } catch (e) {
            context.write({
                key: txnId,
                value: { success: false, error: e.message }
            });
        }
    }

    function reduce(context) {
        // Summarize results
        const results = context.values.map(JSON.parse);
        const success = results.filter(r => r.success).length;
        const failed = results.filter(r => !r.success).length;

        log.audit({
            title: 'Batch JE Creation',
            details: `Success: ${success}, Failed: ${failed}`
        });
    }

    function summarize(summary) {
        log.audit({
            title: 'Total Governance',
            details: summary.usage
        });
    }

    return {
        getInputData: getInputData,
        map: map,
        reduce: reduce,
        summarize: summarize
    };
});
```

**Performance Tips:**
- Use Map/Reduce for >1000 JEs (auto-yields for governance)
- Use Scheduled Script for 100-1000 JEs
- Use `isDynamic: false` in batch operations (faster)
- Batch `submitFields()` calls when possible
- Schedule during off-peak hours (2-6 AM Pacific)

## Error Handling & Validation

### Pre-Creation Validation

```javascript
function validateJournalEntry(jeData) {
    const errors = [];

    // Validate balanced entry
    const totalDebits = jeData.lines
        .filter(l => l.debit)
        .reduce((sum, l) => sum + l.debit, 0);

    const totalCredits = jeData.lines
        .filter(l => l.credit)
        .reduce((sum, l) => sum + l.credit, 0);

    if (Math.abs(totalDebits - totalCredits) > 0.01) {
        errors.push(`Entry not balanced: Debits ${totalDebits}, Credits ${totalCredits}`);
    }

    // Validate minimum lines
    if (jeData.lines.length < 2) {
        errors.push('Journal entry must have at least 2 lines');
    }

    // Validate accounts exist
    for (const line of jeData.lines) {
        if (!line.account) {
            errors.push('All lines must have an account');
        }
    }

    // Validate period is open
    if (!isPeriodOpen(jeData.postingPeriod)) {
        errors.push(`Period ${jeData.postingPeriod} is closed`);
    }

    if (errors.length > 0) {
        throw error.create({
            name: 'JE_VALIDATION_ERROR',
            message: errors.join('; ')
        });
    }
}
```

**Validation Checklist:**
- ✅ Debits = Credits (balanced entry)
- ✅ Minimum 2 lines
- ✅ All accounts valid and active
- ✅ Posting period is open
- ✅ Subsidiary matches all line subsidiaries (OneWorld)
- ✅ Currency matches all line amounts
- ✅ Required custom fields populated

## Common Use Cases

### 1. Accrual Journal Entries

**Scenario:** Automatically accrue expenses at month-end

**Trigger:** Scheduled script runs last day of month
**Logic:** Calculate accrued but unpaid expenses from approved POs/bills
**Reversal:** Auto-reverse on 1st of next month

### 2. Revenue Recognition JEs

**Scenario:** Recognize revenue when invoice is posted

**Trigger:** Invoice afterSubmit event
**Logic:** Debit AR, Credit Revenue (or Deferred Revenue for subscriptions)
**Compliance:** Supports ASC 606 revenue recognition rules

### 3. Depreciation Journal Entries

**Scenario:** Monthly depreciation calculation for fixed assets

**Trigger:** Scheduled script (monthly)
**Logic:** Calculate depreciation per asset, aggregate by account
**Output:** Single JE with depreciation expense and accumulated depreciation

### 4. Intercompany Allocations

**Scenario:** Allocate shared services costs across subsidiaries

**Trigger:** Scheduled script (monthly or quarterly)
**Logic:** Calculate allocation percentages, create JE debiting each subsidiary
**Compliance:** Transfer pricing documentation

### 5. Currency Revaluation

**Scenario:** Revalue foreign currency balances at month-end

**Trigger:** Scheduled script (month-end)
**Logic:** Calculate unrealized gain/loss on foreign currency accounts
**Output:** JE recording forex gain/loss

## Testing Approach

### Sandbox Testing Checklist

Before production deployment:

1. **Test Data Validation**
   - Create unbalanced JE (should fail)
   - Create JE in closed period (should fail)
   - Create JE with invalid account (should fail)

2. **Test Automation Logic**
   - Verify correct accounts selected
   - Verify amounts calculated correctly
   - Verify memo/description populated

3. **Test Governance**
   - Create 100+ JEs and monitor governance usage
   - Verify Map/Reduce script yields properly
   - Check execution time vs. timeout limits

4. **Test Reversal Logic**
   - Create accrual JE, verify reversal created correctly
   - Verify debits/credits reversed
   - Verify linking between original and reversal

5. **Test Error Handling**
   - Simulate API failures
   - Verify error logging
   - Verify source transaction not affected if JE creation fails

## Best Practices

### Configuration Management
- **Never hard-code account IDs** - Use custom record or configuration script
- Store account mappings in custom record type
- Use subsidiary-specific account mappings for OneWorld

### Audit Trail
- Always populate memo field with source transaction reference
- Use custom fields to link JE to source transaction
- Log all automated JE creation with transaction details
- Maintain separate log for failed JE attempts

### Approval Workflows
- Consider requiring approval for large JEs (threshold-based)
- Implement maker-checker for material automated JEs
- Route unusual JEs (e.g., large amounts) for manual review

### SOX Compliance
- Maintain segregation of duties (developer ≠ approver)
- Require change management process for script modifications
- Version control all SuiteScript files
- Document business rules for automated JEs

## Related Documentation

- **[Reconciliation](reconciliation.md)** - Bank reconciliation automation
- **[Period Close](period-close.md)** - Month-end close checklist
- **[Revenue Recognition](revenue-recognition.md)** - ASC 606 compliance
- **[Large Volume Processing](../patterns/large-volume.md)** - Map/Reduce patterns

**Local KB:**
- `/opt/ns/kb/suitescript-modules.md` - N/record, N/search API reference
- `/opt/ns/kb/suitecloud-sdk-framework.md` - Deployment workflows

**Oracle NetSuite:**
- Journal Entry Record: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N3052057.html
- SuiteScript 2.x Best Practices: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/

---

*Based on research: Perplexity findings on NetSuite financial automation best practices*
