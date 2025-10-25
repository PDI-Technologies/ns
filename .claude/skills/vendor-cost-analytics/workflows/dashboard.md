# Spend Analytics Dashboard

Dashboard component design for vendor spend visualization and monitoring.

## Overview

Effective spend dashboards provide at-a-glance insights into vendor performance, spend trends, and cost optimization opportunities.

**Dashboard Purposes:**
- Executive visibility (total spend, top vendors, trends)
- Operational monitoring (maverick spend, duplicates, variances)
- Analytics (deep-dive into categories, vendors, time periods)
- Alerts (threshold breaches, anomalies, issues)

**Design Principles:**
- Start with KPIs (most important metrics first)
- Progressive disclosure (summary → details)
- Actionable insights (not just data)
- Real-time or near-real-time updates
- Mobile-friendly responsive design

## Dashboard Components

### Executive Summary Cards

Key metrics displayed as cards at dashboard top.

**Component Specifications:**

```typescript
// Metric Card Component
interface MetricCard {
    label: string;          // "Total Vendor Spend"
    value: number | string; // "$12.5M"
    trend: number;          // +5.2% (vs prior period)
    trendDirection: 'up' | 'down' | 'neutral';
    status: 'good' | 'warning' | 'critical';
    icon: string;          // Icon identifier
}

// Example metrics:
const executiveMetrics: MetricCard[] = [
    {
        label: "Total Vendor Spend",
        value: "$12,456,789",
        trend: 5.2,
        trendDirection: "up",
        status: "warning", // Increased spend
        icon: "dollar-sign"
    },
    {
        label: "Active Vendors",
        value: "1,247",
        trend: -12.3,
        trendDirection: "down",
        status: "good", // Reduced vendor count
        icon: "users"
    },
    {
        label: "Maverick Spend",
        value: "8.3%",
        trend: -2.1,
        trendDirection: "down",
        status: "good", // Improving compliance
        icon: "alert-triangle"
    },
    {
        label: "Potential Duplicates",
        value: "47",
        trend: 0,
        trendDirection: "neutral",
        status: "warning",
        icon: "copy"
    }
];
```

**Implementation (React + shadcn/ui):**

```typescript
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

export function MetricCard({ metric }: { metric: MetricCard }) {
    const TrendIcon = metric.trendDirection === 'up' ? TrendingUp :
                      metric.trendDirection === 'down' ? TrendingDown : Minus;

    return (
        <Card>
            <CardHeader>
                <CardTitle className="text-sm font-medium">{metric.label}</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="text-2xl font-bold">{metric.value}</div>
                <div className="flex items-center text-xs text-muted-foreground">
                    <TrendIcon className="h-4 w-4 mr-1" />
                    <span>{Math.abs(metric.trend)}% vs last period</span>
                </div>
            </CardContent>
        </Card>
    );
}
```

### Top Vendors Table

Ranked list of vendors by spend.

**Table Specifications:**

| Column | Sort | Filter | Format |
|--------|------|--------|--------|
| Rank | No | No | #1, #2, #3... |
| Vendor Name | Yes | Search | Text |
| Total Spend | Yes | Range | Currency |
| % of Total | No | No | Percent |
| Transaction Count | Yes | No | Number |
| Avg Transaction | Yes | No | Currency |
| Last Transaction | Yes | Date | Date |
| Category | Yes | Multi-select | Badge |
| Status | No | Single-select | Badge |

**Implementation:**

```typescript
import { DataTable } from "@/components/ui/data-table";

const columns = [
    { accessorKey: "rank", header: "Rank" },
    { accessorKey: "vendorName", header: "Vendor Name" },
    {
        accessorKey: "totalSpend",
        header: "Total Spend",
        cell: ({ row }) => {
            const amount = parseFloat(row.getValue("totalSpend"));
            return new Intl.NumberFormat("en-US", {
                style: "currency",
                currency: "USD",
            }).format(amount);
        },
    },
    {
        accessorKey: "percentOfTotal",
        header: "% of Total",
        cell: ({ row }) => `${row.getValue("percentOfTotal").toFixed(1)}%`,
    },
    { accessorKey: "transactionCount", header: "Transactions" },
];

export function TopVendorsTable({ data }: { data: VendorSpend[] }) {
    return <DataTable columns={columns} data={data} />;
}
```

### Spend Trend Chart

Time series visualization of monthly spend.

**Chart Specifications:**
- Type: Line chart with area fill
- X-axis: Month (last 12-24 months)
- Y-axis: Total spend ($)
- Series: Total spend, Top 10 vendors, Top 20 vendors
- Interactivity: Hover for details, click to filter

**Implementation (Recharts):**

```typescript
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export function SpendTrendChart({ data }: { data: MonthlySpend[] }) {
    return (
        <ResponsiveContainer width="100%" height={350}>
            <AreaChart data={data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis tickFormatter={(value) => `$${value/1000}K`} />
                <Tooltip formatter={(value) => `$${value.toLocaleString()}`} />
                <Area
                    type="monotone"
                    dataKey="totalSpend"
                    stroke="#8884d8"
                    fill="#8884d8"
                    fillOpacity={0.6}
                />
            </AreaChart>
        </ResponsiveContainer>
    );
}
```

### Spend by Category (Treemap)

Hierarchical spend visualization by category.

**Chart Specifications:**
- Type: Treemap
- Levels: Category → Subcategory → Vendor
- Size: Proportional to spend amount
- Color: Category-based color coding
- Interactivity: Click to drill down

### Duplicate Vendor Alerts

Table of potential duplicate vendors requiring review.

**Table Specifications:**

| Column | Description | Format |
|--------|-------------|--------|
| Vendor 1 | First vendor name | Text |
| Vendor 2 | Second vendor name | Text |
| Similarity | Match confidence | Percent + Badge |
| Combined Spend | Total spend across both | Currency |
| Est. Savings | Consolidation savings | Currency |
| Action | Review/Merge/Dismiss | Button group |

**Implementation:**

```typescript
export function DuplicateAlertsTable({ duplicates }: { duplicates: DuplicatePair[] }) {
    return (
        <Table>
            <TableHeader>
                <TableRow>
                    <TableHead>Vendor 1</TableHead>
                    <TableHead>Vendor 2</TableHead>
                    <TableHead>Similarity</TableHead>
                    <TableHead>Combined Spend</TableHead>
                    <TableHead>Actions</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {duplicates.map((dup) => (
                    <TableRow key={dup.id}>
                        <TableCell>{dup.vendor_1_name}</TableCell>
                        <TableCell>{dup.vendor_2_name}</TableCell>
                        <TableCell>
                            <Badge variant={dup.similarity >= 0.95 ? "destructive" : "warning"}>
                                {(dup.similarity * 100).toFixed(0)}%
                            </Badge>
                        </TableCell>
                        <TableCell>${dup.combined_spend.toLocaleString()}</TableCell>
                        <TableCell>
                            <Button variant="outline" size="sm">Review</Button>
                        </TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    );
}
```

### Vendor Concentration Chart

Pareto chart showing vendor concentration.

**Chart Specifications:**
- Type: Combo chart (bar + line)
- Bars: Individual vendor spend (sorted descending)
- Line: Cumulative percentage
- Highlight: 80% threshold line (Pareto principle)
- X-axis: Vendor rank
- Y-axis (left): Spend amount
- Y-axis (right): Cumulative percentage

## Dashboard Layouts

### Executive View

**Layout:**
```
┌─────────────────────────────────────────────┐
│  Metric Cards (4 across)                    │
│  [Total Spend] [Vendors] [Maverick] [Dupes] │
├─────────────────────────────────────────────┤
│  Spend Trend Chart (12 months)              │
│  [Line chart with area fill]                │
├─────────────────────────────────────────────┤
│  Top 10 Vendors         │  Spend by Category│
│  [Table]                │  [Pie or Treemap] │
└─────────────────────────────────────────────┘
```

**Refresh:** Daily or on-demand

### Operational View

**Layout:**
```
┌─────────────────────────────────────────────┐
│  Filters: [Date Range] [Category] [Vendor]  │
├─────────────────────────────────────────────┤
│  Detailed Vendor List (searchable, sortable)│
│  [Data table with 20+ columns]              │
├─────────────────────────────────────────────┤
│  Duplicate Alerts      │  Price Variances   │
│  [Alert table]         │  [Exception table] │
└─────────────────────────────────────────────┘
```

**Refresh:** Real-time or hourly

### Analytics View

**Layout:**
```
┌─────────────────────────────────────────────┐
│  Advanced Filters + Date Selectors          │
├─────────────────────────────────────────────┤
│  Vendor Concentration  │  Kraljic Matrix    │
│  [Pareto chart]        │  [Scatter plot]    │
├─────────────────────────────────────────────┤
│  Spend Trends by Category (multi-series)    │
│  [Line chart with multiple lines]           │
├─────────────────────────────────────────────┤
│  Drill-Down Table (click chart to populate) │
│  [Detailed transaction view]                │
└─────────────────────────────────────────────┘
```

**Refresh:** On-demand

## Best Practices

### Dashboard Design
- Most important metrics at top (F-pattern reading)
- Limit to 7-10 key metrics (avoid overload)
- Use color coding consistently (red = bad, green = good)
- Provide context (vs prior period, vs budget, vs benchmark)
- Enable drill-down (summary → detail)

### Performance
- Cache expensive calculations
- Paginate large tables (20-50 rows per page)
- Lazy load detail views
- Optimize database queries (indexed fields)
- Use materialized views for complex aggregations

### Interactivity
- Filter by date range, category, vendor
- Search/autocomplete for vendor selection
- Click chart to filter table
- Export to Excel/CSV
- Save custom views/filters

### Mobile Responsiveness
- Stack cards vertically on mobile
- Horizontal scroll for tables
- Simplified charts on small screens
- Touch-friendly controls (larger buttons)

## Related Documentation

- **[Spend Analysis](../reference/spend-analysis.md)** - Data for dashboard metrics
- **[Duplicate Detection](../reference/duplicate-detection.md)** - Duplicate alerts component
- **[Cost Optimization](../reference/cost-optimization.md)** - Savings opportunities display

**For UI Components:**
- Use shadcn/ui MCP: `mcp__shadcn__getComponent('data-table')`, `mcp__shadcn__getComponent('area-chart-01')`

---

*Generic dashboard design patterns for vendor spend analytics visualization*
