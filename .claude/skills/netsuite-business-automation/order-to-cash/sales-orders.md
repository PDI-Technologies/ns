# Sales Order Automation

Automated sales order validation, pricing, credit checks, approval routing, and inventory allocation.

## Overview

Sales order automation ensures data accuracy, enforces business rules, and accelerates order processing. Key automation points:

**Common Automation Scenarios:**
- Credit limit validation before order approval
- Automatic pricing and discount application
- Inventory availability checks
- Order approval routing based on amount/customer
- Order confirmation email generation
- Integration with external order management systems

**Business Impact:**
- Reduce order processing time by 60-80%
- Eliminate manual pricing errors
- Enforce credit policies automatically
- Improve order accuracy to 99%+

## Credit Limit Validation

### User Event Script - beforeSubmit

Prevent order creation if customer exceeds credit limit.

```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType UserEventScript
 */
define(['N/record', 'N/search', 'N/error'], (record, search, error) => {

    function beforeSubmit(context) {
        if (context.type !== context.UserEventType.CREATE &&
            context.type !== context.UserEventType.EDIT) {
            return;
        }

        const salesOrder = context.newRecord;
        const customerId = salesOrder.getValue({ fieldId: 'entity' });
        const orderTotal = salesOrder.getValue({ fieldId: 'total' });

        // Get customer credit info
        const customerFields = search.lookupFields({
            type: search.Type.CUSTOMER,
            id: customerId,
            columns: ['creditlimit', 'balance', 'unbilleorders']
        });

        const creditLimit = parseFloat(customerFields.creditlimit) || 0;
        const currentBalance = parseFloat(customerFields.balance) || 0;
        const unbilledOrders = parseFloat(customerFields.unbilleorders) || 0;
        const totalExposure = currentBalance + unbilledOrders + orderTotal;

        if (creditLimit > 0 && totalExposure > creditLimit) {
            throw error.create({
                name: 'CREDIT_LIMIT_EXCEEDED',
                message: `Credit limit exceeded. Limit: $${creditLimit}, Exposure: $${totalExposure}`
            });
        }
    }

    return { beforeSubmit: beforeSubmit };
});
```

**Oracle NetSuite Documentation:**
- Customer Record: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N294135.html
- See also: `/opt/ns/kb/suitescript-modules.md` (N/search.lookupFields)

## Automatic Pricing

### beforeLoad + beforeSubmit

Apply pricing rules based on customer tier, volume, or promotions.

```javascript
function beforeSubmit(context) {
    const salesOrder = context.newRecord;
    const pricingTier = salesOrder.getValue({ fieldId: 'custbody_pricing_tier' });
    const lineCount = salesOrder.getLineCount({ sublistId: 'item' });

    for (let i = 0; i < lineCount; i++) {
        const itemId = salesOrder.getSublistValue({ sublistId: 'item', fieldId: 'item', line: i });
        const quantity = salesOrder.getSublistValue({ sublistId: 'item', fieldId: 'quantity', line: i });

        // Apply tier pricing
        const tierPrice = getTierPrice(itemId, pricingTier, quantity);
        if (tierPrice) {
            salesOrder.setSublistValue({ sublistId: 'item', fieldId: 'rate', line: i, value: tierPrice });
        }

        // Apply volume discount
        const discount = getVolumeDiscount(quantity);
        if (discount > 0) {
            salesOrder.setSublistValue({ sublistId: 'item', fieldId: 'custcol_discount_percent', line: i, value: discount });
        }
    }
}

function getVolumeDiscount(quantity) {
    if (quantity >= 100) return 15;
    if (quantity >= 50) return 10;
    if (quantity >= 25) return 5;
    return 0;
}
```

## Approval Workflow Routing

### beforeSubmit - Set Approval Status

Route orders for approval based on business rules.

```javascript
function beforeSubmit(context) {
    if (context.type !== context.UserEventType.CREATE) return;

    const salesOrder = context.newRecord;
    const orderTotal = salesOrder.getValue({ fieldId: 'total' });
    const discount = salesOrder.getValue({ fieldId: 'discountrate' }) || 0;

    let requiresApproval = false;
    let approvalReason = [];

    // Rule 1: Order amount threshold
    if (orderTotal > 10000) {
        requiresApproval = true;
        approvalReason.push(`Order exceeds $10,000`);
    }

    // Rule 2: Discount threshold
    if (discount > 15) {
        requiresApproval = true;
        approvalReason.push(`Discount exceeds 15%`);
    }

    if (requiresApproval) {
        salesOrder.setValue({ fieldId: 'orderstatus', value: 'B' }); // Pending Approval
        salesOrder.setValue({ fieldId: 'custbody_approval_reason', value: approvalReason.join('; ') });
        salesOrder.setValue({ fieldId: 'custbody_approver', value: getApprover(orderTotal) });
    }
}

function getApprover(orderTotal) {
    if (orderTotal > 100000) return EXECUTIVE_APPROVER_ID;
    if (orderTotal > 50000) return DIRECTOR_APPROVER_ID;
    if (orderTotal > 10000) return MANAGER_APPROVER_ID;
    return SUPERVISOR_APPROVER_ID;
}
```

## RESTlet Integration

### External Order Creation

Accept orders from e-commerce platforms or third-party systems.

```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType Restlet
 */
define(['N/record', 'N/search'], (record, search) => {

    function post(requestBody) {
        try {
            if (!requestBody.customer_external_id || !requestBody.items) {
                return { success: false, error: 'Missing required fields' };
            }

            const customerId = findCustomerByExternalId(requestBody.customer_external_id);
            if (!customerId) {
                return { success: false, error: 'Customer not found' };
            }

            const salesOrder = record.create({ type: record.Type.SALES_ORDER, isDynamic: true });
            salesOrder.setValue({ fieldId: 'entity', value: customerId });

            for (const item of requestBody.items) {
                const itemId = findItemBySku(item.sku);
                if (!itemId) return { success: false, error: `Item not found: ${item.sku}` };

                salesOrder.selectNewLine({ sublistId: 'item' });
                salesOrder.setCurrentSublistValue({ sublistId: 'item', fieldId: 'item', value: itemId });
                salesOrder.setCurrentSublistValue({ sublistId: 'item', fieldId: 'quantity', value: item.quantity });
                salesOrder.commitLine({ sublistId: 'item' });
            }

            const orderId = salesOrder.save();
            return { success: true, netsuite_order_id: orderId };

        } catch (e) {
            return { success: false, error: e.message };
        }
    }

    return { post: post };
});
```

**Integration Use Cases:**
- E-commerce platforms (Shopify, BigCommerce)
- Mobile app orders
- EDI order feeds
- Marketplace orders (Amazon, eBay)

**Oracle NetSuite Documentation:**
- RESTlets: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4624454249.html
- See also: `/opt/ns/kb/restlets.md`, `/opt/ns/kb/authentication.md`

## Testing Checklist

1. **Credit Limit** - Order within limit (succeed), exceeding limit (fail)
2. **Pricing** - Tier pricing applied, volume discounts correct
3. **Approval** - Orders >$10K route to manager, >$50K to director
4. **Integration** - RESTlet accepts valid order, rejects invalid data

## Best Practices

### Data Validation
- Validate customer exists and is active
- Check item availability before adding
- Verify pricing before save
- Ensure required fields populated

### Performance
- Use `search.lookupFields()` instead of `record.load()` for reading
- Cache frequently accessed data (pricing tiers, approver lists)
- Use `isDynamic: true` only when needed
- Batch operations when processing multiple orders

### Security
- Validate user permissions before allowing overrides
- Audit all price changes
- Log approval decisions
- Restrict access to sensitive fields

## Related Documentation

- **[Fulfillment](fulfillment.md)** - Pick/pack/ship automation
- **[Invoicing](invoicing.md)** - Billing and invoice generation
- **[Approval Routing](../workflows/approval-routing.md)** - Workflow patterns

**Local KB:**
- `/opt/ns/kb/suitescript-modules.md` - N/record, N/search, N/email APIs
- `/opt/ns/kb/restlets.md` - RESTlet development patterns
- `/opt/ns/kb/authentication.md` - OAuth 2.0 for integrations

**Oracle NetSuite:**
- Sales Order Record: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N296361.html
