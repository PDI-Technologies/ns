---
name: netsuite-business-automation
description: Automates accounting, finance, and operations workflows in NetSuite including journal entries, account reconciliation, period close, order-to-cash (sales orders, fulfillment, invoicing, payments), procure-to-pay (requisitions, POs, vendor bills, expense reports), revenue recognition, subscription billing, and approval workflows. Use when building finance team automations, sales operations, procurement processes, or custom business workflows.
---

# NetSuite Business Automation

Comprehensive skill for automating accounting, finance, and operations workflows in NetSuite.

## Quick Start

### Common Automations
- **Finance**: See [finance/journal-entries.md](finance/journal-entries.md)
- **Order-to-Cash**: See [order-to-cash/sales-orders.md](order-to-cash/sales-orders.md)
- **Procure-to-Pay**: See [procure-to-pay/requisitions-pos.md](procure-to-pay/requisitions-pos.md)
- **Workflows**: See [workflows/approval-routing.md](workflows/approval-routing.md)
- **Custom Records**: See [custom-records/record-design.md](custom-records/record-design.md)

### Business Process Overview

| Process | Automation Type | Typical Scripts | Use Cases |
|---------|----------------|-----------------|-----------|
| **Finance** | Journal Entries, Reconciliation | User Event, Scheduled | Month-end close, Accruals, Intercompany |
| **Order-to-Cash** | Sales Operations | User Event, Workflow | Order processing, Billing, Revenue |
| **Procure-to-Pay** | AP Automation | User Event, Scheduled | Procurement, AP, Payments |
| **Workflows** | Business Logic | Workflow Actions | Approvals, Routing, Notifications |
| **Custom Records** | Data Extensions | User Event, Client Script | Custom data models, Relationships |

## Knowledge Base Resources

### Local KB Documentation
- **SuiteScript Modules**: [/opt/ns/kb/suitescript-modules.md](/opt/ns/kb/suitescript-modules.md)
- **Authentication**: [/opt/ns/kb/authentication.md](/opt/ns/kb/authentication.md)
- **SuiteCloud SDK**: [/opt/ns/kb/suitecloud-sdk-framework.md](/opt/ns/kb/suitecloud-sdk-framework.md)

### Archon Vector KB
For NetSuite automation documentation:

```javascript
mcp__archon__rag_search_knowledge_base(
  query="journal entry automation NetSuite",
  match_count=5
)

mcp__archon__rag_search_code_examples(
  query="sales order workflow automation",
  match_count=3
)
```

## Finance Automation

### Journal Entries
See [finance/journal-entries.md](finance/journal-entries.md)

**Automation Types:**
- Automatic JE creation (User Event afterSubmit)
- Recurring journal entries (Scheduled Script)
- Reversal automation (User Event afterSubmit)
- Intercompany eliminations (Scheduled Script)
- Foreign currency revaluation (Scheduled Script)

**Common Triggers:**
- Invoice creation → Revenue recognition JE
- Payment received → Cash application JE
- Month-end close → Accrual JEs
- Payroll processing → Expense allocation JEs

**Example - Auto JE on Invoice:**
```javascript
function afterSubmit(scriptContext) {
    if (scriptContext.type === scriptContext.UserEventType.CREATE) {
        const invoice = scriptContext.newRecord;
        const invoiceTotal = invoice.getValue({ fieldId: 'total' });

        // Create journal entry for revenue recognition
        const je = record.create({
            type: record.Type.JOURNAL_ENTRY,
            isDynamic: true
        });

        // Debit: Accounts Receivable
        je.selectNewLine({ sublistId: 'line' });
        je.setCurrentSublistValue({
            sublistId: 'line',
            fieldId: 'account',
            value: AR_ACCOUNT_ID
        });
        je.setCurrentSublistValue({
            sublistId: 'line',
            fieldId: 'debit',
            value: invoiceTotal
        });
        je.commitLine({ sublistId: 'line' });

        // Credit: Revenue
        je.selectNewLine({ sublistId: 'line' });
        je.setCurrentSublistValue({
            sublistId: 'line',
            fieldId: 'account',
            value: REVENUE_ACCOUNT_ID
        });
        je.setCurrentSublistValue({
            sublistId: 'line',
            fieldId: 'credit',
            value: invoiceTotal
        });
        je.commitLine({ sublistId: 'line' });

        const jeId = je.save();
        log.audit('JE Created', `Journal Entry ${jeId} for Invoice ${invoice.id}`);
    }
}
```

### Account Reconciliation
See [finance/reconciliation.md](finance/reconciliation.md)

**Automation Types:**
- Bank reconciliation matching (Scheduled Script)
- Variance analysis (Saved Search + Scheduled Script)
- Account balance monitoring (Scheduled Script)
- Reconciliation reports (Scheduled Script)

**Workflows:**
1. Import bank statement (CSV Import or RESTlet)
2. Match transactions (Scheduled Script with fuzzy matching)
3. Flag unmatched items (Custom Record)
4. Review and approve (Workflow)
5. Generate reconciliation report (Saved Search)

### Period Close
See [finance/period-close.md](finance/period-close.md)

**Automation Components:**
- Close checklist tracking (Custom Record + Dashboard)
- Accrual calculations (Scheduled Script)
- Deferred revenue recognition (Scheduled Script)
- Intercompany eliminations (Map/Reduce Script)
- Financial statement generation (Saved Searches)

**Period Close Checklist:**
1. Reconcile bank accounts
2. Review AR aging
3. Review AP aging
4. Process accruals
5. Run depreciation
6. Intercompany eliminations
7. Review P&L variances
8. Generate financial statements
9. Lock period

### Revenue Recognition
See [finance/revenue-recognition.md](finance/revenue-recognition.md)

**Methods:**
- Point-in-time recognition (User Event)
- Ratable recognition (Scheduled Script)
- Milestone-based (User Event + Workflow)
- Subscription billing (Scheduled Script)

**Automation:**
- Create revenue arrangement
- Calculate recognition schedule
- Generate JEs automatically
- Update deferred revenue balances

### Intercompany Transactions
See [finance/intercompany.md](finance/intercompany.md)

**Automation:**
- Intercompany journal entries
- Elimination entries
- Currency translation
- Transfer pricing calculations

## Order-to-Cash (O2C)

### Sales Orders
See [order-to-cash/sales-orders.md](order-to-cash/sales-orders.md)

**Automation Points:**
- Order creation validation (User Event beforeSubmit)
- Pricing and discounts (User Event beforeLoad/beforeSubmit)
- Credit limit checks (User Event beforeSubmit)
- Inventory allocation (User Event afterSubmit)
- Approval routing (Workflow)
- Order confirmation emails (User Event afterSubmit)

**Example - Credit Limit Check:**
```javascript
function beforeSubmit(scriptContext) {
    const salesOrder = scriptContext.newRecord;
    const customerId = salesOrder.getValue({ fieldId: 'entity' });
    const orderTotal = salesOrder.getValue({ fieldId: 'total' });

    // Get customer credit limit and balance
    const customerRec = search.lookupFields({
        type: search.Type.CUSTOMER,
        id: customerId,
        columns: ['creditlimit', 'balance']
    });

    const creditLimit = parseFloat(customerRec.creditlimit) || 0;
    const currentBalance = parseFloat(customerRec.balance) || 0;
    const newBalance = currentBalance + orderTotal;

    if (creditLimit > 0 && newBalance > creditLimit) {
        throw error.create({
            name: 'CREDIT_LIMIT_EXCEEDED',
            message: `Credit limit exceeded. Limit: $${creditLimit}, New Balance: $${newBalance}`
        });
    }
}
```

### Fulfillment
See [order-to-cash/fulfillment.md](order-to-cash/fulfillment.md)

**Automation:**
- Pick/pack/ship automation
- Shipping label generation
- Tracking number updates
- Inventory updates
- Customer notifications

**Integration Points:**
- Shipping carrier APIs (UPS, FedEx, USPS)
- Warehouse management systems
- Barcode scanning systems

### Invoicing
See [order-to-cash/invoicing.md](order-to-cash/invoicing.md)

**Automation:**
- Auto-invoice on fulfillment
- Billing schedules
- Subscription billing
- Proforma invoices
- Consolidated invoicing

**Billing Patterns:**
- One-time billing
- Recurring billing (monthly, annual)
- Usage-based billing
- Milestone billing
- Progress billing

### Payments
See [order-to-cash/payments.md](order-to-cash/payments.md)

**Automation:**
- Payment processing (RESTlet for payment gateway)
- Auto-application of payments
- Credit memo creation
- Refund processing
- Dunning management

**Payment Gateways:**
- Stripe integration
- PayPal integration
- Authorize.net
- Custom payment processors

### Revenue Recognition
See [order-to-cash/revenue.md](order-to-cash/revenue.md)

**ASC 606 Compliance:**
- Revenue arrangement creation
- Performance obligation identification
- Transaction price allocation
- Recognition schedule generation
- Deferred revenue tracking

## Procure-to-Pay (P2P)

### Requisitions and Purchase Orders
See [procure-to-pay/requisitions-pos.md](procure-to-pay/requisitions-pos.md)

**Automation:**
- Requisition approval workflow
- Auto-PO creation from requisition
- Vendor selection logic
- Budget checking
- Contract compliance

**Example - Auto-PO Creation:**
```javascript
function afterSubmit(scriptContext) {
    if (scriptContext.type === scriptContext.UserEventType.CREATE) {
        const requisition = scriptContext.newRecord;
        const status = requisition.getValue({ fieldId: 'status' });

        if (status === 'Approved') {
            // Create purchase order
            const po = record.transform({
                fromType: record.Type.PURCHASE_REQUISITION,
                fromId: requisition.id,
                toType: record.Type.PURCHASE_ORDER,
                isDynamic: false
            });

            const poId = po.save();
            log.audit('PO Created', `PO ${poId} from Requisition ${requisition.id}`);
        }
    }
}
```

### Receiving
See [procure-to-pay/receiving.md](procure-to-pay/receiving.md)

**Automation:**
- Item receipt creation
- Quantity verification
- Quality inspection workflow
- Inventory updates
- 3-way matching (PO, Receipt, Invoice)

### Vendor Bills
See [procure-to-pay/vendor-bills.md](procure-to-pay/vendor-bills.md)

**Automation:**
- Bill matching (PO + Receipt)
- Approval routing
- GL coding
- Payment terms calculation
- Duplicate detection

**3-Way Match:**
1. Purchase Order exists
2. Item Receipt recorded
3. Vendor Bill matches both
4. Tolerances within limits
5. Auto-approve or route for review

### Expense Reports
See [procure-to-pay/expense-reports.md](procure-to-pay/expense-reports.md)

**Automation:**
- Receipt OCR and data extraction
- Policy compliance checking
- Approval workflow
- GL allocation
- Credit card reconciliation

### Payments
See [procure-to-pay/payments.md](procure-to-pay/payments.md)

**Automation:**
- Payment batch generation
- Payment file creation (ACH, Wire)
- Check printing
- Payment confirmation
- 1099 tracking

## Workflows

### Approval Routing
See [workflows/approval-routing.md](workflows/approval-routing.md)

**Approval Patterns:**
- Sequential approval (Manager → Director → VP)
- Parallel approval (Multiple approvers simultaneously)
- Escalation (Auto-approve if no response)
- Conditional routing (Amount-based, Department-based)

**Example Workflow:**
```
Sales Order > $10,000
├─> Sales Manager (Required)
├─> Finance Director (Required if > $50,000)
└─> VP Sales (Required if > $100,000)
```

### Notification Automation
See [workflows/notification-automation.md](workflows/notification-automation.md)

**Notification Types:**
- Email notifications
- Internal messages
- Dashboard alerts
- External webhooks

**Triggers:**
- Record created
- Record updated
- Field changed
- Approval status changed
- Due date approaching
- Exception conditions

### Custom Workflow Actions
See [workflows/custom-workflows.md](workflows/custom-workflows.md)

**Workflow Action Scripts:**
- Complex calculations
- External API calls
- Record transformations
- Conditional logic
- Data validation

**Example - Custom Workflow Action:**
```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType WorkflowActionScript
 */
define(['N/record', 'N/https'], (record, https) => {

    function onAction(scriptContext) {
        const currentRecord = scriptContext.newRecord;
        const orderId = currentRecord.id;
        const customerEmail = currentRecord.getValue({ fieldId: 'email' });

        // Call external API to send notification
        const response = https.post({
            url: 'https://api.notification-service.com/send',
            headers: {
                'Authorization': 'Bearer ' + getApiKey(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                to: customerEmail,
                template: 'order_confirmation',
                variables: {
                    order_id: orderId,
                    order_total: currentRecord.getValue({ fieldId: 'total' })
                }
            })
        });

        if (response.code === 200) {
            return 'SUCCESS';
        } else {
            return 'FAILURE';
        }
    }

    return { onAction };
});
```

## Custom Records

### Record Design
See [custom-records/record-design.md](custom-records/record-design.md)

**Design Considerations:**
- Field types and constraints
- Record relationships (parent-child, lookup)
- Access controls
- Forms and sublists
- Search definitions

**Common Custom Records:**
- Project tracking
- Contract management
- Asset management
- Commission calculations
- Custom configuration

### Relationship Management
See [custom-records/relationship-management.md](custom-records/relationship-management.md)

**Relationship Types:**
- One-to-one (Customer → Primary Contact)
- One-to-many (Order → Line Items)
- Many-to-many (Products ↔ Categories)

**Implementation:**
- Custom record types
- Custom fields for foreign keys
- Saved searches for queries
- User Events for referential integrity

## Code Examples

### Complete Finance Automation
See [examples/finance-automation.md](examples/finance-automation.md)

**Includes:**
- Automated journal entries
- Month-end close checklist
- Accrual calculations
- Financial reporting

### Order-to-Cash Workflow
See [examples/order-to-cash-workflow.md](examples/order-to-cash-workflow.md)

**Includes:**
- Sales order validation
- Fulfillment automation
- Auto-invoicing
- Payment processing
- Revenue recognition

### Procure-to-Pay System
See [examples/procure-to-pay-system.md](examples/procure-to-pay-system.md)

**Includes:**
- Requisition workflow
- PO automation
- 3-way matching
- Payment processing
- Reporting

## Best Practices

### Transaction Automation
- ✅ Validate before creating transactions
- ✅ Log all automated transactions
- ✅ Provide audit trails
- ✅ Handle errors gracefully
- ✅ Test in sandbox extensively
- ❌ Don't skip validations
- ❌ Don't create orphan records
- ❌ Don't ignore governance limits

### Financial Accuracy
- ✅ Always balance debits and credits
- ✅ Use proper accounting periods
- ✅ Maintain referential integrity
- ✅ Document business rules
- ✅ Implement approval controls
- ❌ Don't hard-code account IDs
- ❌ Don't bypass approval workflows
- ❌ Don't modify closed periods

### Workflow Design
- ✅ Keep workflows simple and linear
- ✅ Provide clear error messages
- ✅ Log all workflow actions
- ✅ Test all approval paths
- ✅ Document business logic
- ❌ Don't create circular dependencies
- ❌ Don't mix workflow types unnecessarily
- ❌ Don't skip testing edge cases

## Performance Optimization

### Large Volume Processing
See [patterns/large-volume.md](patterns/large-volume.md)

**Strategies:**
- Use Map/Reduce for > 1000 records
- Batch operations in chunks
- Schedule during off-peak hours
- Monitor governance usage

### Search Optimization
- Use indexed fields in filters
- Limit columns returned
- Use summary searches when possible
- Cache search results

### Transaction Management
- Use isDynamic: false for better performance
- Avoid unnecessary record loads
- Use submitFields for simple updates
- Batch related transactions

## Compliance and Controls

### SOX Compliance
- Segregation of duties
- Approval workflows
- Audit trails
- Change management
- Access controls

### Financial Controls
- Budget checking
- Approval limits
- Dual authorization
- Reconciliation requirements
- Period locking

## Reference Documentation

### Complete File Index

**Finance:**
- [finance/journal-entries.md](finance/journal-entries.md)
- [finance/reconciliation.md](finance/reconciliation.md)
- [finance/period-close.md](finance/period-close.md)
- [finance/revenue-recognition.md](finance/revenue-recognition.md)
- [finance/intercompany.md](finance/intercompany.md)

**Order-to-Cash:**
- [order-to-cash/sales-orders.md](order-to-cash/sales-orders.md)
- [order-to-cash/fulfillment.md](order-to-cash/fulfillment.md)
- [order-to-cash/invoicing.md](order-to-cash/invoicing.md)
- [order-to-cash/payments.md](order-to-cash/payments.md)
- [order-to-cash/revenue.md](order-to-cash/revenue.md)

**Procure-to-Pay:**
- [procure-to-pay/requisitions-pos.md](procure-to-pay/requisitions-pos.md)
- [procure-to-pay/receiving.md](procure-to-pay/receiving.md)
- [procure-to-pay/vendor-bills.md](procure-to-pay/vendor-bills.md)
- [procure-to-pay/expense-reports.md](procure-to-pay/expense-reports.md)
- [procure-to-pay/payments.md](procure-to-pay/payments.md)

**Workflows:**
- [workflows/approval-routing.md](workflows/approval-routing.md)
- [workflows/notification-automation.md](workflows/notification-automation.md)
- [workflows/custom-workflows.md](workflows/custom-workflows.md)

**Custom Records:**
- [custom-records/record-design.md](custom-records/record-design.md)
- [custom-records/relationship-management.md](custom-records/relationship-management.md)

**Examples:**
- [examples/finance-automation.md](examples/finance-automation.md)
- [examples/order-to-cash-workflow.md](examples/order-to-cash-workflow.md)
- [examples/procure-to-pay-system.md](examples/procure-to-pay-system.md)
