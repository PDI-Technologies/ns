# Salesforce Financial Data Integration

Extract financial and revenue data from Salesforce for analysis, forecasting, and reporting.

## Overview

Salesforce CRM contains critical financial data for revenue analysis:
- **Opportunities** - Sales pipeline and revenue forecasting
- **Accounts** - Customer master data and relationships
- **Products** - Product catalog and pricing
- **Orders** - Customer orders and fulfillment
- **Contracts** - Recurring revenue and subscriptions
- **Custom Objects** - Domain-specific financial data

## MCP Tools Available

Two Salesforce MCP servers are available in this environment:

1. **pdi-salesforce-sse3** - Primary server with enhanced features
2. **pdi-salesforce-proxy** - Alternative server

Both provide identical core functionality for financial data extraction.

## Authentication

MCP servers handle authentication automatically. No manual OAuth configuration needed in your code.

## Query Operations (SOQL)

### Basic SOQL Query

```python
# Query opportunities for revenue analysis
result = mcp__pdi_salesforce_sse3__query(
    soql="""
        SELECT Id, Name, Amount, CloseDate, StageName, Probability,
               Account.Name, Account.Industry
        FROM Opportunity
        WHERE CloseDate >= THIS_YEAR
        ORDER BY CloseDate DESC
    """,
    pageSize=50
)

opportunities = result["records"]
```

### Pagination

Handle large result sets with pagination:

```python
def fetch_all_opportunities(start_date: str) -> list[dict]:
    """Fetch all opportunities with pagination."""
    all_records = []
    page_number = 1
    page_size = 50

    while True:
        result = mcp__pdi_salesforce_sse3__query(
            soql=f"""
                SELECT Id, Name, Amount, CloseDate, StageName
                FROM Opportunity
                WHERE CloseDate >= {start_date}
            """,
            pageNumber=page_number,
            pageSize=page_size
        )

        records = result.get("records", [])
        if not records:
            break

        all_records.extend(records)

        # Check if more pages
        if not result.get("hasMore", False):
            break

        page_number += 1

    return all_records
```

## Financial Data Extraction Patterns

### Revenue Analysis

**Opportunity pipeline analysis:**

```python
import pandas as pd
from datetime import datetime

def extract_revenue_pipeline():
    """Extract opportunity pipeline for revenue forecasting."""
    soql = """
        SELECT
            Id,
            Name,
            Amount,
            CloseDate,
            StageName,
            Probability,
            Type,
            Account.Name,
            Account.Industry,
            Owner.Name
        FROM Opportunity
        WHERE IsClosed = false
        AND Amount > 0
        ORDER BY CloseDate ASC
    """

    result = mcp__pdi_salesforce_sse3__query(soql=soql, pageSize=200)

    # Convert to DataFrame for analysis
    opportunities = []
    for record in result["records"]:
        opportunities.append({
            "id": record["Id"],
            "name": record["Name"],
            "amount": record["Amount"],
            "close_date": record["CloseDate"],
            "stage": record["StageName"],
            "probability": record["Probability"],
            "type": record.get("Type"),
            "account_name": record["Account"]["Name"],
            "industry": record["Account"].get("Industry"),
            "owner": record["Owner"]["Name"],
            "weighted_amount": record["Amount"] * (record["Probability"] / 100.0)
        })

    return pd.DataFrame(opportunities)
```

**Revenue by period analysis:**

```python
def analyze_revenue_by_quarter():
    """Analyze closed-won revenue by quarter."""
    soql = """
        SELECT
            CALENDAR_QUARTER(CloseDate) quarter,
            SUM(Amount) total_revenue,
            COUNT(Id) deal_count,
            AVG(Amount) avg_deal_size
        FROM Opportunity
        WHERE IsWon = true
        AND CloseDate >= LAST_N_YEARS:2
        GROUP BY CALENDAR_QUARTER(CloseDate)
        ORDER BY CALENDAR_QUARTER(CloseDate) DESC
    """

    result = mcp__pdi_salesforce_sse3__query(soql=soql)
    return pd.DataFrame(result["records"])
```

### Customer Analysis

**Customer lifetime value data:**

```python
def extract_customer_revenue():
    """Extract customer revenue for CLV analysis."""
    soql = """
        SELECT
            Account.Id,
            Account.Name,
            Account.Type,
            Account.Industry,
            Account.CreatedDate,
            SUM(Amount) total_revenue,
            COUNT(Id) opportunity_count,
            AVG(Amount) avg_deal_size,
            MAX(CloseDate) last_purchase_date,
            MIN(CloseDate) first_purchase_date
        FROM Opportunity
        WHERE IsWon = true
        GROUP BY
            Account.Id,
            Account.Name,
            Account.Type,
            Account.Industry,
            Account.CreatedDate
        HAVING SUM(Amount) > 0
        ORDER BY SUM(Amount) DESC
    """

    result = mcp__pdi_salesforce_sse3__query(soql=soql, maxFetch=1000)
    return result["records"]
```

### Product Revenue Analysis

**Product mix and performance:**

```python
def extract_product_revenue():
    """Extract product revenue for mix analysis."""
    # Note: Requires OpportunityLineItem object
    soql = """
        SELECT
            Product2.Name product_name,
            Product2.Family product_family,
            SUM(TotalPrice) total_revenue,
            SUM(Quantity) total_quantity,
            COUNT(OpportunityId) opportunity_count,
            AVG(UnitPrice) avg_unit_price
        FROM OpportunityLineItem
        WHERE Opportunity.IsWon = true
        AND Opportunity.CloseDate >= THIS_YEAR
        GROUP BY
            Product2.Name,
            Product2.Family
        ORDER BY SUM(TotalPrice) DESC
    """

    result = mcp__pdi_salesforce_sse3__query(soql=soql, pageSize=100)
    return pd.DataFrame(result["records"])
```

## Multi-Level Relationship Queries

Salesforce allows traversing relationships in SOQL:

```python
def extract_account_hierarchy():
    """Extract account relationships for hierarchical analysis."""
    soql = """
        SELECT
            Id,
            Name,
            Type,
            AnnualRevenue,
            NumberOfEmployees,
            Parent.Name,
            Parent.Id,
            (SELECT Amount, CloseDate, StageName
             FROM Opportunities
             WHERE CloseDate >= THIS_YEAR)
        FROM Account
        WHERE Type = 'Customer'
        ORDER BY AnnualRevenue DESC
    """

    result = mcp__pdi_salesforce_sse3__query(soql=soql, pageSize=50)
    return result["records"]
```

## CRUD Operations

### Create Records

```python
# Create opportunity
new_opp = mcp__pdi_salesforce_sse3__create(
    sObjectType="Opportunity",
    record={
        "Name": "Q1 Enterprise Deal",
        "Amount": 150000.00,
        "CloseDate": "2025-03-31",
        "StageName": "Prospecting",
        "AccountId": "001XXXXXXXXXXXXXXX"
    }
)

opportunity_id = new_opp["id"]
```

### Update Records

```python
# Update opportunity stage
mcp__pdi_salesforce_sse3__update(
    sObjectType="Opportunity",
    id="006XXXXXXXXXXXXXXX",
    record={
        "StageName": "Closed Won",
        "Probability": 100
    }
)
```

### Bulk Operations

```python
# Bulk create opportunities
opportunities_to_create = [
    {"Name": "Deal 1", "Amount": 10000, "CloseDate": "2025-12-31", "StageName": "Prospecting"},
    {"Name": "Deal 2", "Amount": 25000, "CloseDate": "2025-12-31", "StageName": "Prospecting"},
    {"Name": "Deal 3", "Amount": 15000, "CloseDate": "2025-12-31", "StageName": "Prospecting"},
]

result = mcp__pdi_salesforce_sse3__bulkCreate(
    sObjectType="Opportunity",
    records=opportunities_to_create
)
```

## Schema Discovery

### Find Custom Objects

```python
# List all custom objects (including financial custom objects)
result = mcp__pdi_salesforce_sse3__listCustomObjects(
    searchPattern="Revenue",  # Find revenue-related objects
    pageSize=50
)

for obj in result["objects"]:
    print(f"{obj['name']}: {obj['label']}")
```

### Describe Object Fields

```python
# Get fields for custom financial object
result = mcp__pdi_salesforce_sse3__describeSObject(
    sObjectType="Revenue_Recognition__c",
    includeRelationships=True,
    pageSize=100
)

for field in result["fields"]:
    print(f"{field['name']} ({field['type']}): {field['label']}")
```

## Search Operations (SOSL)

SOSL searches across multiple objects:

```python
# Search for customer across Account, Contact, Opportunity
result = mcp__pdi_salesforce_sse3__search(
    query="FIND {Acme Corp} IN ALL FIELDS RETURNING Account(Name, Industry), Opportunity(Name, Amount, CloseDate)"
)

accounts = result.get("Account", [])
opportunities = result.get("Opportunity", [])
```

## Complete Revenue Analysis Example

```python
import pandas as pd
from datetime import datetime, timedelta

class SalesforceRevenueAnalyzer:
    """Extract and analyze Salesforce revenue data."""

    def extract_closed_won_revenue(self, months_back: int = 12) -> pd.DataFrame:
        """Extract closed-won opportunities for period."""
        start_date = datetime.now() - timedelta(days=months_back * 30)

        soql = f"""
            SELECT
                Id,
                Name,
                Amount,
                CloseDate,
                StageName,
                Type,
                Account.Name,
                Account.Industry,
                Owner.Name
            FROM Opportunity
            WHERE IsWon = true
            AND CloseDate >= {start_date.strftime('%Y-%m-%d')}
            ORDER BY CloseDate DESC
        """

        all_records = []
        page = 1

        while True:
            result = mcp__pdi_salesforce_sse3__query(
                soql=soql,
                pageNumber=page,
                pageSize=200
            )

            records = result.get("records", [])
            if not records:
                break

            all_records.extend(records)

            if not result.get("hasMore", False):
                break

            page += 1

        # Convert to DataFrame
        opportunities = []
        for record in all_records:
            opportunities.append({
                "id": record["Id"],
                "name": record["Name"],
                "amount": record["Amount"],
                "close_date": pd.to_datetime(record["CloseDate"]),
                "stage": record["StageName"],
                "type": record.get("Type"),
                "account_name": record["Account"]["Name"],
                "industry": record["Account"].get("Industry"),
                "owner": record["Owner"]["Name"]
            })

        return pd.DataFrame(opportunities)

    def calculate_monthly_revenue(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate revenue by month."""
        df["month"] = df["close_date"].dt.to_period("M")

        monthly = df.groupby("month").agg({
            "amount": ["sum", "mean", "count"]
        }).round(2)

        monthly.columns = ["total_revenue", "avg_deal_size", "deal_count"]
        monthly["revenue_growth"] = monthly["total_revenue"].pct_change()

        return monthly

    def analyze_by_industry(self, df: pd.DataFrame) -> pd.DataFrame:
        """Analyze revenue by customer industry."""
        industry_analysis = df.groupby("industry").agg({
            "amount": ["sum", "mean", "count"]
        }).round(2)

        industry_analysis.columns = ["total_revenue", "avg_deal_size", "deal_count"]
        industry_analysis = industry_analysis.sort_values("total_revenue", ascending=False)

        return industry_analysis

    def generate_report(self, months_back: int = 12):
        """Generate complete revenue analysis report."""
        # Extract data
        df = self.extract_closed_won_revenue(months_back)

        # Calculate metrics
        total_revenue = df["amount"].sum()
        deal_count = len(df)
        avg_deal_size = df["amount"].mean()

        # Analyze by period
        monthly_revenue = self.calculate_monthly_revenue(df)

        # Analyze by industry
        industry_revenue = self.analyze_by_industry(df)

        return {
            "summary": {
                "total_revenue": total_revenue,
                "deal_count": deal_count,
                "avg_deal_size": avg_deal_size
            },
            "monthly_revenue": monthly_revenue,
            "industry_revenue": industry_revenue,
            "raw_data": df
        }
```

## Integration with NetSuite

Bi-directional sync pattern for quote-to-cash:

```python
def sync_salesforce_to_netsuite(opportunity_id: str):
    """Sync closed-won opportunity to NetSuite sales order."""
    # 1. Fetch opportunity from Salesforce
    opp = mcp__pdi_salesforce_sse3__retrieve(
        sObjectType="Opportunity",
        ids=[opportunity_id],
        fields=["Name", "Amount", "CloseDate", "AccountId"]
    )

    # 2. Create sales order in NetSuite (using netsuite integration)
    # See netsuite.md for NetSuite API calls

    # 3. Update Salesforce with NetSuite order ID
    mcp__pdi_salesforce_sse3__update(
        sObjectType="Opportunity",
        id=opportunity_id,
        record={
            "NetSuite_Order_ID__c": netsuite_order_id  # Custom field
        }
    )
```

## Error Handling

```python
def safe_salesforce_query(soql: str, max_retries: int = 3):
    """Execute SOQL with error handling."""
    for attempt in range(max_retries):
        try:
            result = mcp__pdi_salesforce_sse3__query(soql=soql)
            return result
        except Exception as e:
            if "INVALID_FIELD" in str(e):
                # Field doesn't exist, don't retry
                raise ValueError(f"Invalid SOQL field: {e}")

            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise
```

## Best Practices

### Query Optimization

1. **Select specific fields** - Don't use `SELECT *`
2. **Filter early** - Use WHERE clause to limit results
3. **Index fields** - Query on indexed fields (Id, CreatedDate, custom indexed fields)
4. **Limit relationships** - Maximum 5 parent-to-child relationships
5. **Use LIMIT** - Add LIMIT clause for testing queries

### Data Validation

```python
from decimal import Decimal

def validate_opportunity_data(record: dict):
    """Validate opportunity financial data."""
    # Check required fields
    required = ["Id", "Amount", "CloseDate", "StageName"]
    missing = [f for f in required if f not in record or record[f] is None]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")

    # Validate amount
    if record["Amount"] < 0:
        raise ValueError(f"Negative amount not allowed: {record['Amount']}")

    # Validate date format
    try:
        close_date = datetime.fromisoformat(record["CloseDate"])
    except:
        raise ValueError(f"Invalid date format: {record['CloseDate']}")

    return True
```

### Bulk Operations

Use bulk APIs for >200 records:

```python
def bulk_update_opportunities(updates: list[dict]):
    """Bulk update opportunities efficiently."""
    # Chunk into batches of 200 (Salesforce limit)
    batch_size = 200

    for i in range(0, len(updates), batch_size):
        batch = updates[i:i + batch_size]

        result = mcp__pdi_salesforce_sse3__bulkUpdate(
            sObjectType="Opportunity",
            records=batch
        )

        # Check for errors
        for idx, item in enumerate(result):
            if not item.get("success"):
                print(f"Failed to update {batch[idx]['Id']}: {item.get('errors')}")
```

## Related Resources

- **Salesforce MCP Skill:** `.claude/skills/salesforce-mcp-distilled/`
- **NetSuite Integration:** `netsuite.md` (for quote-to-cash sync)
- **Revenue Analytics:** `../reference/revenue-analytics.md`

## Official Documentation

- **SOQL Reference:** https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/
- **Salesforce API:** https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/
- **Opportunity Object:** https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_opportunity.htm
