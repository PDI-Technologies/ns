# Financial Dashboard - Complete React PWA Example

Build a production-ready financial analytics dashboard using React, shadcn/ui, and Progressive Web App features.

## Overview

This example demonstrates building a comprehensive financial dashboard with:
- Real-time metrics and KPIs
- Interactive charts and visualizations
- Revenue and cost analysis
- Responsive design for all devices
- PWA capabilities for offline access

## Tech Stack

- **React 18+** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **shadcn/ui** - Component library
- **Recharts** - Chart library
- **TanStack Query** - Data fetching and caching
- **Tailwind CSS** - Styling
- **Workbox** - PWA service worker

## Project Setup

### Initialize Project

```bash
# Create Vite project with React + TypeScript
npm create vite@latest financial-dashboard -- --template react-ts
cd financial-dashboard
npm install

# Install shadcn/ui
npx shadcn-ui@latest init

# Install dependencies
npm install recharts @tanstack/react-query date-fns
npm install -D @types/node
```

### Configure Vite for PWA

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'
import path from 'path'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'robots.txt', 'apple-touch-icon.png'],
      manifest: {
        name: 'Financial Dashboard',
        short_name: 'FinDash',
        description: 'Real-time financial analytics dashboard',
        theme_color: '#000000',
        icons: [
          {
            src: 'pwa-192x192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ]
      }
    })
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
```

## Core Components

### 1. Financial Metrics API

```typescript
// src/lib/api/financial-api.ts
export interface FinancialMetrics {
  revenue: number
  revenueGrowth: number
  expenses: number
  expenseGrowth: number
  profit: number
  profitMargin: number
  lastUpdated: string
}

export interface RevenueData {
  month: string
  revenue: number
  expenses: number
  profit: number
}

export interface VendorSpend {
  vendorName: string
  totalSpend: number
  transactionCount: number
}

export async function fetchFinancialMetrics(): Promise<FinancialMetrics> {
  // In production, fetch from your API
  const response = await fetch('/api/metrics')
  return response.json()
}

export async function fetchRevenueTrends(months: number = 12): Promise<RevenueData[]> {
  const response = await fetch(`/api/revenue-trends?months=${months}`)
  return response.json()
}

export async function fetchTopVendors(limit: number = 10): Promise<VendorSpend[]> {
  const response = await fetch(`/api/vendors/top?limit=${limit}`)
  return response.json()
}
```

### 2. Dashboard Layout

```typescript
// src/components/Dashboard.tsx
import { useQuery } from '@tanstack/react-query'
import { MetricCard } from './MetricCard'
import { RevenueTrendChart } from './RevenueTrendChart'
import { VendorSpendChart } from './VendorSpendChart'
import { fetchFinancialMetrics, fetchRevenueTrends, fetchTopVendors } from '@/lib/api/financial-api'

export function Dashboard() {
  const { data: metrics, isLoading: metricsLoading } = useQuery({
    queryKey: ['financial-metrics'],
    queryFn: fetchFinancialMetrics,
    refetchInterval: 60000, // Refresh every minute
  })

  const { data: revenueTrends, isLoading: trendsLoading } = useQuery({
    queryKey: ['revenue-trends'],
    queryFn: () => fetchRevenueTrends(12),
  })

  const { data: topVendors, isLoading: vendorsLoading } = useQuery({
    queryKey: ['top-vendors'],
    queryFn: () => fetchTopVendors(10),
  })

  if (metricsLoading || trendsLoading || vendorsLoading) {
    return <DashboardSkeleton />
  }

  return (
    <div className="min-h-screen bg-background p-4 md:p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h1 className="text-4xl font-bold">Financial Dashboard</h1>
          <p className="text-sm text-muted-foreground">
            Last updated: {new Date(metrics.lastUpdated).toLocaleString()}
          </p>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <MetricCard
            title="Revenue"
            value={metrics.revenue}
            growth={metrics.revenueGrowth}
            format="currency"
          />
          <MetricCard
            title="Expenses"
            value={metrics.expenses}
            growth={metrics.expenseGrowth}
            format="currency"
            invertGrowth
          />
          <MetricCard
            title="Profit Margin"
            value={metrics.profitMargin}
            format="percentage"
          />
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <RevenueTrendChart data={revenueTrends} />
          <VendorSpendChart data={topVendors} />
        </div>
      </div>
    </div>
  )
}
```

### 3. Metric Card Component

```typescript
// src/components/MetricCard.tsx
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ArrowUpIcon, ArrowDownIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

interface MetricCardProps {
  title: string
  value: number
  growth?: number
  format?: 'currency' | 'percentage' | 'number'
  invertGrowth?: boolean
}

export function MetricCard({
  title,
  value,
  growth,
  format = 'number',
  invertGrowth = false
}: MetricCardProps) {
  const formattedValue = formatValue(value, format)
  const isPositiveGrowth = invertGrowth ? growth < 0 : growth > 0

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-bold">{formattedValue}</div>
        {growth !== undefined && (
          <div className="flex items-center mt-2 text-sm">
            {isPositiveGrowth ? (
              <ArrowUpIcon className="w-4 h-4 mr-1 text-green-600" />
            ) : (
              <ArrowDownIcon className="w-4 h-4 mr-1 text-red-600" />
            )}
            <span className={cn(
              isPositiveGrowth ? 'text-green-600' : 'text-red-600'
            )}>
              {Math.abs(growth).toFixed(1)}%
            </span>
            <span className="text-muted-foreground ml-1">vs last period</span>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function formatValue(value: number, format: string): string {
  switch (format) {
    case 'currency':
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }).format(value)
    case 'percentage':
      return `${value.toFixed(1)}%`
    default:
      return value.toLocaleString()
  }
}
```

### 4. Revenue Trend Chart

```typescript
// src/components/RevenueTrendChart.tsx
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { RevenueData } from '@/lib/api/financial-api'

interface RevenueTrendChartProps {
  data: RevenueData[]
}

export function RevenueTrendChart({ data }: RevenueTrendChartProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Revenue Trends (12 Months)</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              dataKey="month"
              className="text-xs"
              tick={{ fill: 'hsl(var(--muted-foreground))' }}
            />
            <YAxis
              className="text-xs"
              tick={{ fill: 'hsl(var(--muted-foreground))' }}
              tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'hsl(var(--card))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '6px',
              }}
              formatter={(value: number) => [`$${value.toLocaleString()}`, '']}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="revenue"
              stroke="hsl(var(--primary))"
              strokeWidth={2}
              name="Revenue"
            />
            <Line
              type="monotone"
              dataKey="expenses"
              stroke="hsl(var(--destructive))"
              strokeWidth={2}
              name="Expenses"
            />
            <Line
              type="monotone"
              dataKey="profit"
              stroke="hsl(var(--success))"
              strokeWidth={2}
              name="Profit"
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
```

### 5. Vendor Spend Chart

```typescript
// src/components/VendorSpendChart.tsx
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { VendorSpend } from '@/lib/api/financial-api'

interface VendorSpendChartProps {
  data: VendorSpend[]
}

export function VendorSpendChart({ data }: VendorSpendChartProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Top Vendors by Spend</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              type="number"
              tick={{ fill: 'hsl(var(--muted-foreground))' }}
              tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
            />
            <YAxis
              type="category"
              dataKey="vendorName"
              tick={{ fill: 'hsl(var(--muted-foreground))' }}
              width={150}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'hsl(var(--card))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '6px',
              }}
              formatter={(value: number) => [`$${value.toLocaleString()}`, 'Spend']}
            />
            <Bar dataKey="totalSpend" fill="hsl(var(--primary))" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
```

## Backend API Implementation

### Python FastAPI Backend

```python
# api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import create_engine

app = FastAPI(title="Financial Dashboard API")

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
DB_URL = "postgresql://user:pass@localhost/analytics"
engine = create_engine(DB_URL)

@app.get("/api/metrics")
def get_financial_metrics():
    """Get current financial metrics with growth rates."""
    current_period = datetime.now().replace(day=1)
    prior_period = current_period - timedelta(days=30)

    # Current period metrics
    current_query = f"""
        SELECT
            SUM(CASE WHEN type = 'Revenue' THEN amount ELSE 0 END) as revenue,
            SUM(CASE WHEN type = 'Expense' THEN amount ELSE 0 END) as expenses
        FROM transactions
        WHERE tran_date >= '{current_period.date()}'
    """
    current = pd.read_sql(current_query, engine).iloc[0]

    # Prior period metrics
    prior_query = f"""
        SELECT
            SUM(CASE WHEN type = 'Revenue' THEN amount ELSE 0 END) as revenue,
            SUM(CASE WHEN type = 'Expense' THEN amount ELSE 0 END) as expenses
        FROM transactions
        WHERE tran_date >= '{prior_period.date()}'
        AND tran_date < '{current_period.date()}'
    """
    prior = pd.read_sql(prior_query, engine).iloc[0]

    # Calculate metrics
    profit = current["revenue"] - current["expenses"]
    profit_margin = (profit / current["revenue"] * 100) if current["revenue"] > 0 else 0

    revenue_growth = ((current["revenue"] - prior["revenue"]) / prior["revenue"] * 100)
    expense_growth = ((current["expenses"] - prior["expenses"]) / prior["expenses"] * 100)

    return {
        "revenue": float(current["revenue"]),
        "revenueGrowth": float(revenue_growth),
        "expenses": float(current["expenses"]),
        "expenseGrowth": float(expense_growth),
        "profit": float(profit),
        "profitMargin": float(profit_margin),
        "lastUpdated": datetime.now().isoformat()
    }

@app.get("/api/revenue-trends")
def get_revenue_trends(months: int = 12):
    """Get monthly revenue trends."""
    query = f"""
        SELECT
            TO_CHAR(tran_date, 'YYYY-MM') as month,
            SUM(CASE WHEN type = 'Revenue' THEN amount ELSE 0 END) as revenue,
            SUM(CASE WHEN type = 'Expense' THEN amount ELSE 0 END) as expenses
        FROM transactions
        WHERE tran_date >= CURRENT_DATE - INTERVAL '{months} months'
        GROUP BY TO_CHAR(tran_date, 'YYYY-MM')
        ORDER BY month ASC
    """

    df = pd.read_sql(query, engine)
    df["profit"] = df["revenue"] - df["expenses"]

    return df.to_dict('records')

@app.get("/api/vendors/top")
def get_top_vendors(limit: int = 10):
    """Get top vendors by spend."""
    query = f"""
        SELECT
            v.company_name as vendorName,
            SUM(vb.amount) as totalSpend,
            COUNT(vb.id) as transactionCount
        FROM vendors v
        JOIN vendor_bills vb ON v.id = vb.vendor_id
        WHERE vb.status = 'Paid'
        GROUP BY v.company_name
        ORDER BY totalSpend DESC
        LIMIT {limit}
    """

    df = pd.read_sql(query, engine)
    return df.to_dict('records')
```

## Deployment

### Build for Production

```bash
# Build optimized production bundle
npm run build

# Preview production build
npm run preview
```

### Deploy to Vercel

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel --prod
```

### Environment Configuration

```bash
# .env.production
VITE_API_URL=https://api.yourdomain.com
```

## PWA Features

### Service Worker Strategy

```typescript
// src/sw.ts - Custom service worker
import { precacheAndRoute } from 'workbox-precaching'
import { registerRoute } from 'workbox-routing'
import { CacheFirst, NetworkFirst } from 'workbox-strategies'
import { ExpirationPlugin } from 'workbox-expiration'

// Precache all build assets
precacheAndRoute(self.__WB_MANIFEST)

// Cache API responses with network-first strategy
registerRoute(
  ({ url }) => url.pathname.startsWith('/api/'),
  new NetworkFirst({
    cacheName: 'api-cache',
    plugins: [
      new ExpirationPlugin({
        maxEntries: 50,
        maxAgeSeconds: 5 * 60, // 5 minutes
      }),
    ],
  })
)

// Cache static assets with cache-first strategy
registerRoute(
  ({ request }) => request.destination === 'image' ||
                   request.destination === 'font',
  new CacheFirst({
    cacheName: 'static-assets',
    plugins: [
      new ExpirationPlugin({
        maxEntries: 100,
        maxAgeSeconds: 30 * 24 * 60 * 60, // 30 days
      }),
    ],
  })
)
```

## Testing

```typescript
// src/components/__tests__/MetricCard.test.tsx
import { render, screen } from '@testing-library/react'
import { MetricCard } from '../MetricCard'

describe('MetricCard', () => {
  it('renders currency value correctly', () => {
    render(
      <MetricCard
        title="Revenue"
        value={125000}
        growth={15.5}
        format="currency"
      />
    )

    expect(screen.getByText('Revenue')).toBeInTheDocument()
    expect(screen.getByText('$125,000')).toBeInTheDocument()
    expect(screen.getByText('15.5%')).toBeInTheDocument()
  })
})
```

## Performance Optimization

1. **Code Splitting** - Dynamic imports for routes
2. **Image Optimization** - WebP format with fallbacks
3. **Bundle Size** - Tree shaking and lazy loading
4. **Caching Strategy** - React Query + Service Worker
5. **Prefetching** - Preload critical API calls

## Related Resources

- **React PWA Designer Skill:** `.claude/skills/react-pwa-designer/`
- **shadcn/ui Components:** https://ui.shadcn.com
- **Recharts Documentation:** https://recharts.org
- **TanStack Query:** https://tanstack.com/query

## Complete Example Repository

See `/opt/ns/apps/vendor-analysis/` for backend financial data extraction patterns that can power this dashboard.
