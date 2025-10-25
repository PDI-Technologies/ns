# Account Reconciliation Automation

Automated bank reconciliation, AR/AP subledger reconciliation, and variance analysis.

## Overview

Account reconciliation automation ensures financial accuracy by matching transactions between different systems and identifying discrepancies.

**Common Reconciliations:**
- Bank reconciliation (bank statement vs NetSuite cash account)
- AR aging reconciliation (customer invoices vs subledger)
- AP aging reconciliation (vendor bills vs subledger)
- Intercompany reconciliation (intercompany AR/AP balances)
- Inventory reconciliation (physical count vs system)

**Automation Benefits:**
- 80% time reduction in manual reconciliation
- Real-time variance identification
- Automated exception reporting
- Audit-ready documentation

## Bank Reconciliation

### Bank Statement Import

Import bank statement and match to NetSuite transactions.

**Scheduled Script:**

```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType ScheduledScript
 */

define(['N/record', 'N/search', 'N/file'], (record, search, file) => {

    function execute(context) {
        // Load bank statement CSV from file cabinet
        const bankStatementFile = file.load({ id: BANK_STATEMENT_FILE_ID });
        const bankTransactions = parseCSV(bankStatementFile.getContents());

        const reconciliationResults = {
            matched: [],
            unmatched: [],
            duplicates: []
        };

        for (const bankTxn of bankTransactions) {
            // Find matching NetSuite transaction
            const match = findMatchingTransaction(bankTxn);

            if (match) {
                // Mark as reconciled
                markReconciled(match.id, bankTxn.statementDate);
                reconciliationResults.matched.push({
                    bankTxn: bankTxn,
                    nsTxn: match
                });
            } else {
                // No match found
                reconciliationResults.unmatched.push(bankTxn);
            }
        }

        // Generate reconciliation report
        createReconciliationReport(reconciliationResults);
    }

    function findMatchingTransaction(bankTxn) {
        // Match on amount and date (within 3 days)
        const amount = parseFloat(bankTxn.amount);
        const txnDate = new Date(bankTxn.date);

        const dateStart = new Date(txnDate);
        dateStart.setDate(dateStart.getDate() - 3);

        const dateEnd = new Date(txnDate);
        dateEnd.setDate(dateEnd.getDate() + 3);

        const matches = search.create({
            type: search.Type.TRANSACTION,
            filters: [
                ['account', 'is', CASH_ACCOUNT],
                'AND',
                ['amount', 'equalto', Math.abs(amount)],
                'AND',
                ['trandate', 'within', formatDate(dateStart), formatDate(dateEnd)],
                'AND',
                ['custbody_bank_reconciled', 'is', 'F']
            ],
            columns: ['tranid', 'trandate', 'amount', 'type']
        }).run().getRange({ start: 0, end: 1 });

        return matches.length > 0 ? {
            id: matches[0].id,
            tranid: matches[0].getValue({ name: 'tranid' }),
            amount: matches[0].getValue({ name: 'amount' })
        } : null;
    }

    function markReconciled(transactionId, statementDate) {
        record.submitFields({
            type: record.Type.DEPOSIT,  // Or appropriate transaction type
            id: transactionId,
            values: {
                custbody_bank_reconciled: true,
                custbody_reconciliation_date: new Date(statementDate)
            }
        });
    }

    return {
        execute: execute
    };
});
```

### Matching Rules

```javascript
const MATCHING_RULES = {
    // Exact match
    exact: (bankTxn, nsTxn) => {
        return bankTxn.amount === nsTxn.amount &&
               bankTxn.date === nsTxn.date;
    },

    // Amount match with date tolerance
    fuzzy: (bankTxn, nsTxn, dateTolerance = 3) => {
        const amountMatch = Math.abs(bankTxn.amount - nsTxn.amount) < 0.01;
        const daysDiff = Math.abs(
            (new Date(bankTxn.date) - new Date(nsTxn.date)) / (1000 * 60 * 60 * 24)
        );
        return amountMatch && daysDiff <= dateTolerance;
    },

    // Aggregate match (multiple transactions sum to bank transaction)
    aggregate: (bankTxn, nsTxns) => {
        const total = nsTxns.reduce((sum, txn) => sum + txn.amount, 0);
        return Math.abs(bankTxn.amount - total) < 0.01;
    }
};
```

## AR/AP Subledger Reconciliation

### AR Reconciliation

Verify AR subledger matches GL control account.

```javascript
function reconcileARSubledger(periodId) {
    // Get AR GL balance
    const arGLBalance = getGLBalance(AR_CONTROL_ACCOUNT, periodId);

    // Calculate AR subledger total (open invoices)
    const openInvoices = search.create({
        type: search.Type.INVOICE,
        filters: [
            ['status', 'anyof', ['CustInvc:A']],  // Open
            'AND',
            ['postingperiod', 'is', periodId]
        ],
        columns: [
            search.createColumn({
                name: 'amountremaining',
                summary: search.Summary.SUM
            })
        ]
    }).run().getRange({ start: 0, end: 1 });

    const arSubledgerBalance = openInvoices.length > 0
        ? parseFloat(openInvoices[0].getValue({ name: 'amountremaining', summary: search.Summary.SUM }))
        : 0;

    // Check for variance
    const variance = arGLBalance - arSubledgerBalance;

    if (Math.abs(variance) > 0.01) {
        log.error({
            title: 'AR Reconciliation Variance',
            details: `GL: ${arGLBalance}, Subledger: ${arSubledgerBalance}, Variance: ${variance}`
        });

        createReconciliationVarianceRecord({
            account: AR_CONTROL_ACCOUNT,
            period: periodId,
            glBalance: arGLBalance,
            subledgerBalance: arSubledgerBalance,
            variance: variance
        });
    } else {
        log.audit({ title: 'AR Reconciled', details: `Balance: ${arGLBalance}` });
    }

    return {
        glBalance: arGLBalance,
        subledgerBalance: arSubledgerBalance,
        variance: variance,
        reconciled: Math.abs(variance) < 0.01
    };
}
```

### AP Reconciliation

```javascript
function reconcileAPSubledger(periodId) {
    // Get AP GL balance
    const apGLBalance = getGLBalance(AP_CONTROL_ACCOUNT, periodId);

    // Calculate AP subledger total (open bills)
    const openBills = search.create({
        type: search.Type.VENDOR_BILL,
        filters: [
            ['status', 'anyof', ['VendBill:A']],  // Open
            'AND',
            ['postingperiod', 'is', periodId]
        ],
        columns: [
            search.createColumn({
                name: 'amountremaining',
                summary: search.Summary.SUM
            })
        ]
    }).run().getRange({ start: 0, end: 1 });

    const apSubledgerBalance = openBills.length > 0
        ? parseFloat(openBills[0].getValue({ name: 'amountremaining', summary: search.Summary.SUM }))
        : 0;

    const variance = apGLBalance - apSubledgerBalance;

    return {
        glBalance: apGLBalance,
        subledgerBalance: apSubledgerBalance,
        variance: variance,
        reconciled: Math.abs(variance) < 0.01
    };
}
```

## Variance Analysis

### Identifying Reconciliation Differences

```javascript
function analyzeReconciliationVariance(glBalance, subledgerBalance) {
    const variance = glBalance - subledgerBalance;

    // Potential causes of variance
    const possibleCauses = [];

    // Check for unposted transactions
    const unpostedCount = countUnpostedTransactions();
    if (unpostedCount > 0) {
        possibleCauses.push(`${unpostedCount} unposted transactions`);
    }

    // Check for transactions in wrong period
    const wrongPeriodTxns = findTransactionsInWrongPeriod();
    if (wrongPeriodTxns.length > 0) {
        possibleCauses.push(`${wrongPeriodTxns.length} transactions in wrong period`);
    }

    // Check for manual journal entries without proper classification
    const uncategorizedJEs = findUncategorizedJournalEntries();
    if (uncategorizedJEs.length > 0) {
        possibleCauses.push(`${uncategorizedJEs.length} uncategorized journal entries`);
    }

    return {
        variance: variance,
        possibleCauses: possibleCauses,
        requiresInvestigation: Math.abs(variance) > 1.00
    };
}
```

## Best Practices

### Daily Reconciliation

```javascript
// Run daily bank reconciliation instead of monthly
function dailyBankRecon() {
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);

    // Import yesterday's bank transactions
    const bankTxns = importBankTransactions(yesterday);

    // Match to NetSuite
    matchBankTransactions(bankTxns);

    // Alert on unmatched items
    const unmatched = getUnmatchedTransactions(yesterday);
    if (unmatched.length > 0) {
        sendReconciliationAlert(unmatched);
    }
}
```

### Materialized Balance Snapshots

```javascript
// Store period-end balances for faster historical reconciliation
function snapshotPeriodBalances(periodId) {
    const balances = {
        arGL: getGLBalance(AR_CONTROL_ACCOUNT, periodId),
        arSubledger: getARSubledgerBalance(periodId),
        apGL: getGLBalance(AP_CONTROL_ACCOUNT, periodId),
        apSubledger: getAPSubledgerBalance(periodId),
        cash: getGLBalance(CASH_ACCOUNT, periodId),
        reconciled: getRe conciledCash(periodId)
    };

    // Store in custom record for audit trail
    const snapshot = record.create({
        type: 'customrecord_period_balance_snapshot'
    });

    snapshot.setValue({ fieldId: 'custrecord_period', value: periodId });
    snapshot.setValue({ fieldId: 'custrecord_balances_json', value: JSON.stringify(balances) });
    snapshot.setValue({ fieldId: 'custrecord_snapshot_date', value: new Date() });

    snapshot.save();
}
```

## Related Documentation

- **[Period Close](period-close.md)** - Month-end close processes
- **[Intercompany](intercompany.md)** - Intercompany reconciliation
- **[Journal Entries](journal-entries.md)** - Manual adjustments

**External References:**
- [Bank Reconciliation in NetSuite](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N294202.html)

---

*Generic account reconciliation patterns for financial controls and compliance*
