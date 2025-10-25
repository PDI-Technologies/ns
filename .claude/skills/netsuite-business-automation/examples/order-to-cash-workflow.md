# Order-to-Cash Workflow Automation

End-to-end O2C automation from quote to cash, demonstrating sales order processing, fulfillment, invoicing, and payment.

## Scenario: E-Commerce Integration

### Business Context

**Company:** Consumer goods distributor with $30M annual revenue
**Challenge:** Manual order entry from e-commerce site creating bottlenecks
**Pain Points:**
- 200-300 orders per day entered manually (6 FTE staff)
- Order entry errors (5% error rate)
- 24-48 hour delay from order to fulfillment
- Customer complaints about delayed shipments
- Manual invoicing after shipment

### Solution Implementation

**Phase 1: Order Integration (Month 1)**

RESTlet integration between e-commerce platform and NetSuite:
- Orders flow automatically from website to NetSuite
- Real-time inventory availability
- Automated credit checks
- Auto-approval for orders < $500

**Scripts Deployed:**
- RESTlet: Receive orders from e-commerce API
- User Event Script: Credit limit validation
- Workflow: Auto-approve low-value orders

**Results:**
- Manual order entry eliminated: 6 FTE redeployed to customer service
- Order entry errors: 5% → 0.1%
- Order-to-fulfillment time: 24-48 hours → 2-4 hours

**Phase 2: Auto-Fulfillment (Month 2-3)**

Automated fulfillment workflow:
- Auto-create item fulfillment when order approved
- Integration with shipping carrier (UPS API)
- Automatic tracking number capture
- Customer shipping notification

**Scripts Deployed:**
- User Event Script: Auto-create fulfillment on approval
- RESTlet: Receive tracking updates from UPS
- Scheduled Script: Send shipping notifications

**Results:**
- Fulfillment processing time: 4 hours → 30 minutes
- Shipping errors: 3% → 0.5%
- Customer satisfaction scores: +22 points

**Phase 3: Auto-Invoicing (Month 4)**

Automated invoice generation and delivery:
- Invoice created immediately after fulfillment
- PDF invoice emailed to customer
- Payment gateway integration

**Scripts Deployed:**
- User Event Script: Create invoice from fulfillment
- Scheduled Script: Email invoices with PDF
- RESTlet: Payment gateway webhook

**Results:**
- Invoice cycle time: 24 hours → Instant
- DSO (days sales outstanding): 42 days → 31 days (26% improvement)
- Cash flow improvement: $750K working capital released

### Final Results

**End-to-End Order-to-Cash Metrics:**

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Order entry time | 15 min/order | Automated | 100% |
| Order entry FTEs | 6 | 0 | 6 redeployed |
| Order accuracy | 95% | 99.9% | 4.9% |
| Order-to-ship | 36 hours | 3 hours | 92% |
| Invoice cycle | 24 hours | Instant | 100% |
| DSO | 42 days | 31 days | 26% |

**Annual Business Impact:**
- Labor savings: $360K (6 FTE)
- Cash flow improvement: $750K (one-time)
- Error reduction savings: $45K/year (returns, credits)
- Customer satisfaction: +22 NPS points

## Code Highlights

**E-Commerce Order Integration:**
```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType Restlet
 */
define(['N/record'], (record) => {
    function post(orderData) {
        const salesOrder = record.create({
            type: record.Type.SALES_ORDER,
            isDynamic: true
        });

        salesOrder.setValue({ fieldId: 'entity', value: findOrCreateCustomer(orderData.customer) });
        salesOrder.setValue({ fieldId: 'custbody_ecommerce_order_id', value: orderData.orderId });

        for (const item of orderData.items) {
            salesOrder.selectNewLine({ sublistId: 'item' });
            salesOrder.setCurrentSublistValue({ sublistId: 'item', fieldId: 'item', value: item.sku });
            salesOrder.setCurrentSublistValue({ sublistId: 'item', fieldId: 'quantity', value: item.quantity });
            salesOrder.commitLine({ sublistId: 'item' });
        }

        const soId = salesOrder.save();
        return { success: true, salesOrderId: soId };
    }

    return { post: post };
});
```

## Related Documentation

- **[Sales Orders](../order-to-cash/sales-orders.md)** - Order creation patterns
- **[Fulfillment](../order-to-cash/fulfillment.md)** - Fulfillment automation
- **[Invoicing](../order-to-cash/invoicing.md)** - Invoice automation

---

*Case study demonstrating O2C automation reducing cycle time from 4 days to 4 hours*
