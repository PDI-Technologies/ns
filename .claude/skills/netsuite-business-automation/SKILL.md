---
name: netsuite-business-automation
description: Automates accounting, finance, and operations workflows in NetSuite including journal entries, account reconciliation, period close, order-to-cash (sales orders, fulfillment, invoicing, payments), procure-to-pay (requisitions, POs, vendor bills, expense reports), revenue recognition, subscription billing, and approval workflows. Use when building finance team automations, sales operations, procurement processes, or custom business workflows.
---

# NetSuite Business Automation

Comprehensive skill for automating accounting, finance, and operations workflows in NetSuite using SuiteScript 2.x.

## When to Use This Skill

Use this skill when you need to:
- Automate financial processes (journal entries, reconciliation, period close)
- Build order-to-cash workflows (sales orders → fulfillment → invoicing → revenue recognition)
- Automate procure-to-pay processes (requisitions → POs → receiving → vendor bills → payments)
- Create custom approval workflows
- Design custom record types and relationships
- Optimize performance for large-volume transaction processing

## Quick Start

### Getting Started

1. **Review SuiteScript Fundamentals**: See [/opt/ns/kb/suitescript-modules.md](/opt/ns/kb/suitescript-modules.md) for N/record, N/search, N/https APIs
2. **Authentication**: See [/opt/ns/kb/authentication.md](/opt/ns/kb/authentication.md) for OAuth 2.0 setup
3. **Deployment**: See [/opt/ns/kb/suitecloud-sdk-framework.md](/opt/ns/kb/suitecloud-sdk-framework.md) for SDF CLI tools

### Common Automation Patterns

| Business Process | Script Type | Typical Use Cases |
|-----------------|-------------|-------------------|
| **Finance** | User Event, Scheduled | Automated journal entries, accruals, reconciliation |
| **Order-to-Cash** | User Event, Workflow | Order validation, pricing, fulfillment, invoicing |
| **Procure-to-Pay** | User Event, Scheduled | PO automation, 3-way matching, payment processing |
| **Workflows** | Workflow Actions | Approval routing, notifications, state management |
| **Custom Records** | User Event, Client Script | Custom data models, business logic, validations |

## Documentation Structure

### Finance Automation
- **[Journal Entries](finance/journal-entries.md)** - Automated JE creation, reversal, intercompany eliminations
- **[Reconciliation](finance/reconciliation.md)** - Bank reconciliation, variance analysis, account monitoring
- **[Period Close](finance/period-close.md)** - Month-end close automation, checklist management
- **[Revenue Recognition](finance/revenue-recognition.md)** - ASC 606 compliance, deferred revenue, ratable recognition
- **[Intercompany](finance/intercompany.md)** - Elimination entries, currency translation, transfer pricing

### Order-to-Cash (O2C)
- **[Sales Orders](order-to-cash/sales-orders.md)** - Order validation, pricing, credit checks, approval routing
- **[Fulfillment](order-to-cash/fulfillment.md)** - Pick/pack/ship automation, carrier integration, tracking
- **[Invoicing](order-to-cash/invoicing.md)** - Billing schedules, subscription billing, consolidated invoicing
- **[Payments](order-to-cash/payments.md)** - Payment gateway integration, auto-application, credit memos
- **[Revenue](order-to-cash/revenue.md)** - Revenue arrangement creation, performance obligations, recognition schedules

### Procure-to-Pay (P2P)
- **[Requisitions & POs](procure-to-pay/requisitions-pos.md)** - Approval workflows, auto-PO creation, budget checking
- **[Receiving](procure-to-pay/receiving.md)** - Item receipts, quality inspection, inventory updates
- **[Vendor Bills](procure-to-pay/vendor-bills.md)** - 3-way matching, approval routing, duplicate detection
- **[Expense Reports](procure-to-pay/expense-reports.md)** - OCR integration, policy compliance, GL allocation
- **[Payments](procure-to-pay/payments.md)** - Payment batches, ACH/wire file generation, 1099 tracking

### Workflows
- **[Approval Routing](workflows/approval-routing.md)** - Sequential, parallel, escalation patterns
- **[Notification Automation](workflows/notification-automation.md)** - Email, webhooks, dashboard alerts
- **[Custom Workflows](workflows/custom-workflows.md)** - Workflow action scripts, complex logic, external integrations
- **[Custom Field Automation](workflows/custom-field-automation.md)** - Reading/writing custentity_*/custbody_* fields, defensive patterns, schema resilience

### Custom Records
- **[Record Design](custom/record-design.md)** - Field types, forms, sublists, search definitions
- **[Relationship Management](custom/relationship-management.md)** - One-to-many, many-to-many patterns

### Performance & Patterns
- **[Large Volume Processing](patterns/large-volume.md)** - Map/Reduce scripts, batch processing, governance optimization

## Complete Examples

### End-to-End Implementations
- **[Finance Automation](examples/finance-automation.md)** - Complete month-end close automation
- **[Order-to-Cash Workflow](examples/order-to-cash-workflow.md)** - Sales order through revenue recognition
- **[Procure-to-Pay System](examples/procure-to-pay-system.md)** - Requisition through payment processing

## Best Practices

### Script Development
- Use **isDynamic: false** for better performance in scheduled/batch scripts
- Use **isDynamic: true** only when needed (client scripts, interactive UIs)
- Always validate data before creating transactions
- Implement comprehensive error handling and logging
- Test extensively in sandbox before production deployment

### Transaction Automation
- Validate before creating financial transactions
- Maintain audit trails for all automated transactions
- Handle errors gracefully with retry logic
- Never skip approval workflows
- Always balance debits and credits in journal entries

### Governance Management
- Use **Map/Reduce** for processing >1000 records
- Monitor governance usage (10,000 units per scheduled script)
- Schedule intensive scripts during off-peak hours (2-6 AM Pacific)
- Use **search.create()** instead of N/query for better governance
- Cache frequently accessed data

### Performance Optimization
- Use indexed fields in search filters
- Limit columns returned in searches
- Use **submitFields()** for simple field updates
- Avoid unnecessary record loads
- Batch related operations together

### Security & Compliance
- Implement segregation of duties
- Require approval workflows for financial transactions
- Maintain comprehensive audit trails
- Lock periods after close to prevent modifications
- Follow SOX compliance requirements for change management

## Related Skills

**[Vendor Cost Analytics](../vendor-cost-analytics/SKILL.md)** - Use for:
- Duplicate vendor detection in procure-to-pay workflows
- Vendor spend analysis for approval thresholds
- Payment terms optimization

## Additional Resources

### Local Knowledge Base
All files located in `/opt/ns/kb/`:
- **suitescript-modules.md** - Complete API reference for N/record, N/search, N/https, N/email, N/task
- **authentication.md** - OAuth 2.0 implementation guide
- **suitecloud-sdk-framework.md** - SDF CLI deployment workflows
- **restlets.md** - Custom REST endpoint development
- **suitetalk-rest-api.md** - Standard REST web services

### Oracle NetSuite Documentation
- **SuiteScript 2.x API**: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/
- **Help Center**: Setup > Company > Enable Features > SuiteCloud
- **SuiteAnswers**: https://netsuite.custhelp.com/

## Script Type Selection Guide

**User Event Scripts** - Trigger on record events (beforeLoad, beforeSubmit, afterSubmit)
- Order validation, automatic field population, related record creation
- Governance: 1,000 units

**Scheduled Scripts** - Run at scheduled intervals or on-demand
- Batch processing, nightly jobs, data synchronization
- Governance: 10,000 units
- Schedule during off-peak hours

**Map/Reduce Scripts** - Process large datasets with automatic parallelization
- Processing >1000 records, complex aggregations, heavy computations
- Governance: Auto-yielding with queue management

**Workflow Action Scripts** - Custom actions within NetSuite workflows
- Complex calculations, external API calls, conditional routing
- Governance: 1,000 units

**Client Scripts** - Run in user's browser
- Real-time validation, field calculations, UI enhancements
- No governance limits (runs client-side)

**RESTlets** - Custom REST API endpoints
- External integrations, mobile apps, third-party systems
- Governance: 1,000 units per request

## Deployment Workflow

1. **Develop**: Write SuiteScript in IDE with SDF project structure
2. **Test**: Deploy to sandbox, run unit tests, verify governance usage
3. **Review**: Code review, check for governance issues, validate error handling
4. **Deploy**: Use SDF CLI or SuiteCloud Extension to deploy to production
5. **Monitor**: Track script execution logs, governance usage, error rates

See [/opt/ns/kb/suitecloud-sdk-framework.md](/opt/ns/kb/suitecloud-sdk-framework.md) for detailed deployment instructions.

---

*For specific implementation details, navigate to the topic files listed above.*
