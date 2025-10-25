# Intercompany Transaction Automation

Automated intercompany transaction creation, reconciliation, and elimination for multi-subsidiary organizations.

## Overview

Intercompany automation manages transactions between subsidiaries within a consolidated entity, ensuring balances match and eliminations are properly recorded.

**Common Intercompany Transactions:**
- Intercompany sales/purchases
- Intercompany loans
- Shared service allocations
- Royalty and IP licensing fees
- Management fees

**Automation Goals:**
- Auto-generate matching intercompany entries
- Ensure balances match between subsidiaries
- Automate elimination entries for consolidation
- Provide intercompany reconciliation reports

## Intercompany Sales Pattern

### Creating Matched Intercompany Entries

**User Event Script (afterSubmit on Sales Order):**

```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType UserEventScript
 */

define(['N/record'], (record) => {

    function afterSubmit(context) {
        if (context.type !== context.UserEventType.CREATE) {
            return;
        }

        const salesOrder = context.newRecord;
        const customer = salesOrder.getValue({ fieldId: 'entity' });

        // Check if customer is an intercompany subsidiary
        const isIntercompany = checkIfIntercompanyCustomer(customer);

        if (isIntercompany) {
            // Get subsidiaries
            const sellingSubsidiary = salesOrder.getValue({ fieldId: 'subsidiary' });
            const buyingSubsidiary = getCustomerSubsidiary(customer);

            // Create matching purchase order in buying subsidiary
            createIntercompanyPO({
                salesOrderId: salesOrder.id,
                sellingSubsidiary: sellingSubsidiary,
                buyingSubsidiary: buyingSubsidiary,
                items: getOrderItems(salesOrder),
                total: salesOrder.getValue({ fieldId: 'total' })
            });
        }
    }

    function createIntercompanyPO(icData) {
        const po = record.create({
            type: record.Type.PURCHASE_ORDER,
            isDynamic: true
        });

        po.setValue({ fieldId: 'subsidiary', value: icData.buyingSubsidiary });
        po.setValue({ fieldId: 'entity', value: getIntercompanyVendor(icData.sellingSubsidiary) });
        po.setValue({ fieldId: 'custbody_intercompany_so', value: icData.salesOrderId });

        // Add line items
        for (const item of icData.items) {
            po.selectNewLine({ sublistId: 'item' });
            po.setCurrentSublistValue({ sublistId: 'item', fieldId: 'item', value: item.itemId });
            po.setCurrentSublistValue({ sublistId: 'item', fieldId: 'quantity', value: item.quantity });
            po.setCurrentSublistValue({ sublistId: 'item', fieldId: 'rate', value: item.rate });
            po.commitLine({ sublistId: 'item' });
        }

        const poId = po.save();

        // Link back to sales order
        record.submitFields({
            type: record.Type.SALES_ORDER,
            id: icData.salesOrderId,
            values: {
                custbody_intercompany_po: poId
            }
        });

        return poId;
    }

    return {
        afterSubmit: afterSubmit
    };
});
```

## Intercompany Reconciliation

### Balance Matching

Verify intercompany AR/AP balances match between subsidiaries.

**Scheduled Script (monthly):**

```javascript
function reconcileIntercompanyBalances(periodId) {
    const subsidiaries = getAllSubsidiaries();
    const mismatches = [];

    for (let i = 0; i < subsidiaries.length; i++) {
        for (let j = i + 1; j < subsidiaries.length; j++) {
            const sub1 = subsidiaries[i];
            const sub2 = subsidiaries[j];

            // Get intercompany AR from sub1 to sub2
            const arBalance = getIntercompanyAR(sub1.id, sub2.id, periodId);

            // Get intercompany AP from sub2 to sub1
            const apBalance = getIntercompanyAP(sub2.id, sub1.id, periodId);

            // Should match (AR in sub1 = AP in sub2)
            const variance = arBalance + apBalance;  // AP is negative

            if (Math.abs(variance) > 0.01) {
                mismatches.push({
                    subsidiary1: sub1.name,
                    subsidiary2: sub2.name,
                    arBalance: arBalance,
                    apBalance: apBalance,
                    variance: variance
                });
            }
        }
    }

    if (mismatches.length > 0) {
        sendIntercompanyMismatchAlert(mismatches);
    }

    return mismatches;
}

function getIntercompanyAR(fromSubsidiary, toSubsidiary, periodId) {
    const invoices = search.create({
        type: search.Type.INVOICE,
        filters: [
            ['subsidiary', 'is', fromSubsidiary],
            'AND',
            ['custbody_intercompany_subsidiary', 'is', toSubsidiary],
            'AND',
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

    return invoices.length > 0
        ? parseFloat(invoices[0].getValue({ name: 'amountremaining', summary: search.Summary.SUM }))
        : 0;
}
```

## Elimination Entries

### Automated Consolidation Eliminations

```javascript
function createEliminationEntries(periodId) {
    // Find all intercompany transactions for period
    const icTransactions = search.create({
        type: search.Type.TRANSACTION,
        filters: [
            ['custbody_intercompany_flag', 'is', 'T'],
            'AND',
            ['postingperiod', 'is', periodId]
        ],
        columns: [
            'subsidiary',
            'account',
            'amount',
            'department',
            'class',
            'custbody_intercompany_subsidiary'
        ]
    }).run();

    const eliminations = [];

    icTransactions.each((txn) => {
        const subsidiary = txn.getValue({ name: 'subsidiary' });
        const icSubsidiary = txn.getValue({ name: 'custbody_intercompany_subsidiary' });
        const amount = parseFloat(txn.getValue({ name: 'amount' }));
        const account = txn.getValue({ name: 'account' });

        eliminations.push({
            fromSubsidiary: subsidiary,
            toSubsidiary: icSubsidiary,
            account: account,
            amount: amount
        });

        return true;
    });

    // Create elimination journal entry
    createEliminationJE(periodId, eliminations);
}

function createEliminationJE(periodId, eliminations) {
    const je = record.create({
        type: record.Type.ADVANCED_INTERCOMPANY_JOURNAL_ENTRY,
        isDynamic: true
    });

    je.setValue({ fieldId: 'postingperiod', value: periodId });
    je.setValue({ fieldId: 'memo', value: 'Intercompany eliminations' });

    for (const elim of eliminations) {
        // Debit elimination
        je.selectNewLine({ sublistId: 'line' });
        je.setCurrentSublistValue({ sublistId: 'line', fieldId: 'account', value: elim.account });
        je.setCurrentSublistValue({ sublistId: 'line', fieldId: 'debit', value: elim.amount });
        je.setCurrentSublistValue({ sublistId: 'line', fieldId: 'subsidiary', value: elim.fromSubsidiary });
        je.setCurrentSublistValue({ sublistId: 'line', fieldId: 'eliminate', value: true });
        je.commitLine({ sublistId: 'line' });

        // Credit elimination
        je.selectNewLine({ sublistId: 'line' });
        je.setCurrentSublistValue({ sublistId: 'line', fieldId: 'account', value: elim.account });
        je.setCurrentSublistValue({ sublistId: 'line', fieldId: 'credit', value: elim.amount });
        je.setCurrentSublistValue({ sublistId: 'line', fieldId: 'subsidiary', value: elim.toSubsidiary });
        je.setCurrentSublistValue({ sublistId: 'line', fieldId: 'eliminate', value: true });
        je.commitLine({ sublistId: 'line' });
    }

    je.save();
}
```

## Best Practices

### Intercompany Setup

```javascript
// Custom fields needed for intercompany tracking
const INTERCOMPANY_FIELDS = {
    transactions: [
        'custbody_intercompany_flag',          // Checkbox
        'custbody_intercompany_subsidiary',    // List/Record (Subsidiary)
        'custbody_intercompany_linked_txn',    // List/Record (Transaction)
        'custbody_ic_reconciliation_status'    // List (Matched, Variance, Pending)
    ],
    customers: [
        'custentity_intercompany_subsidiary',  // List/Record (Subsidiary)
        'custentity_is_intercompany'           // Checkbox
    ],
    vendors: [
        'custentity_intercompany_subsidiary',
        'custentity_is_intercompany'
    ]
};
```

### Error Handling

```javascript
function createIntercompanyTransaction(data) {
    try {
        // Validate subsidiaries are different
        if (data.fromSubsidiary === data.toSubsidiary) {
            throw error.create({
                name: 'INVALID_INTERCOMPANY',
                message: 'Cannot create intercompany transaction within same subsidiary'
            });
        }

        // Create transactions
        const txn1 = createTransactionInSubsidiary(data.fromSubsidiary, data);
        const txn2 = createTransactionInSubsidiary(data.toSubsidiary, data);

        // Link transactions
        linkIntercompanyTransactions(txn1, txn2);

    } catch (e) {
        log.error({
            title: 'Intercompany Transaction Failed',
            details: e.message
        });
        throw e;
    }
}
```

## Related Documentation

- **[Period Close](period-close.md)** - Integration with month-end close
- **[Reconciliation](reconciliation.md)** - General reconciliation patterns
- **[Journal Entries](journal-entries.md)** - Elimination journal entries

**External References:**
- [NetSuite Intercompany Management](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N557541.html)

---

*Generic intercompany transaction and elimination patterns for multi-subsidiary organizations*
