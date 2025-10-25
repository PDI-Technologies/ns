# Procure-to-Pay System Automation

Complete P2P automation from requisition through payment, demonstrating procurement workflow optimization.

## Scenario: P2P Process Overhaul

### Business Context

**Company:** Manufacturing company with $75M annual procurement spend
**Challenge:** Inefficient manual procurement process causing delays and maverick spend
**Pain Points:**
- Requisition approval delays (average 5 days)
- Manual PO creation (4 purchasing agents)
- No three-way match enforcement (payment errors common)
- 18% maverick spend (purchases outside approved vendors)
- 45-day average time from requisition to payment

### Solution Implementation

**Phase 1: Requisition Workflow (Month 1-2)**

Automated requisition approval and PO generation:
- Electronic requisition submission
- Auto-routing based on amount thresholds
- Budget validation at submission
- Auto-conversion to PO when approved

**Scripts Deployed:**
- User Event Script: Budget validation on requisition
- Workflow Action Script: Dynamic approval routing
- Scheduled Script: Auto-convert approved requisitions to POs

**Results:**
- Requisition approval time: 5 days → 8 hours (84% reduction)
- Budget overruns: 12/year → 0
- PO creation time: 30 min → Automated

**Phase 2: Three-Way Match Enforcement (Month 3-4)**

Mandatory PO-Receipt-Invoice matching:
- Cannot create vendor bill without PO and receipt
- Automated price variance detection
- Exception routing for variances > 5%

**Scripts Deployed:**
- User Event Script: Enforce three-way match on vendor bills
- User Event Script: Price variance detection
- Workflow: Route exceptions to procurement

**Results:**
- Payment errors: 35/month → 2/month (94% reduction)
- Vendor bill processing time: 45 min → 10 min (78% reduction)
- Audit findings: 8 → 0

**Phase 3: Payment Automation (Month 5-6)**

Automated payment batch processing:
- Weekly payment runs
- Early payment discount capture
- ACH file generation
- Automated payment notification to vendors

**Scripts Deployed:**
- Scheduled Script: Payment batch creation
- Scheduled Script: Early discount evaluation
- Map/Reduce Script: Generate ACH files

**Results:**
- Payment processing time: 2 days → 2 hours (93% reduction)
- Early payment discounts captured: $0 → $125K/year
- Vendor payment inquiries: 50/month → 5/month

### Final Results

**End-to-End P2P Metrics:**

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Req approval time | 5 days | 8 hours | 84% |
| PO creation | 30 min | Instant | 100% |
| Bill processing | 45 min | 10 min | 78% |
| Payment processing | 2 days | 2 hours | 93% |
| Maverick spend | 18% | 4% | 78% reduction |
| Payment errors | 35/month | 2/month | 94% |

**Annual Business Impact:**
- Labor savings: $280K (4 FTE purchasing, 2 FTE AP)
- Early payment discounts: $125K/year
- Maverick spend reduction: $1.05M/year (7% of $15M maverick)
- Error correction costs: $42K/year savings
- **Total annual savings: $1.5M**
- **ROI: 15x** (automation cost: $100K)

## Complete Workflow Code

**Requisition to PO:**
```javascript
// Workflow Action: Convert requisition to PO
function onAction(context) {
    const requisition = context.newRecord;

    const po = record.transform({
        fromType: record.Type.PURCHASE_REQUISITION,
        fromId: requisition.id,
        toType: record.Type.PURCHASE_ORDER
    });

    po.setValue({ fieldId: 'trandate', value: new Date() });

    const poId = po.save();

    // Email PO to vendor
    sendPOToVendor(poId);

    return 'SUCCESS';
}
```

**Three-Way Match:**
```javascript
// User Event: Enforce three-way match
function beforeSubmit(context) {
    const bill = context.newRecord;
    const poId = bill.getValue({ fieldId: 'createdfrom' });

    if (!poId) {
        throw error.create({
            name: 'NO_PO',
            message: 'Vendor bill must reference a PO'
        });
    }

    // Verify receipt exists
    const receipts = search.create({
        type: search.Type.ITEM_RECEIPT,
        filters: [['createdfrom', 'is', poId]]
    }).run().getRange({ start: 0, end: 1 });

    if (receipts.length === 0) {
        throw error.create({
            name: 'NO_RECEIPT',
            message: 'Cannot process bill without receipt'
        });
    }
}
```

## Key Success Factors

**Change Management:**
- Executive sponsorship from CFO
- Training for procurement team (2 weeks)
- Phased rollout (one department at a time)
- Weekly feedback sessions

**Data Quality:**
- Vendor master data cleanup (6 weeks)
- Item catalog standardization
- Chart of accounts simplification

**Integration:**
- Vendor portal for PO acknowledgment
- Barcode scanning for receiving
- Bank integration for ACH payments

## Related Documentation

- **[Requisitions/POs](../procure-to-pay/requisitions-pos.md)** - Requisition automation
- **[Vendor Bills](../procure-to-pay/vendor-bills.md)** - Three-way match
- **[Payments](../procure-to-pay/payments.md)** - Payment automation

---

*Case study demonstrating P2P automation delivering $1.5M annual savings and 15x ROI*
