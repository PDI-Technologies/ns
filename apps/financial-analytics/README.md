# Financial Analytics

Comprehensive financial analytics and reporting from NetSuite and Salesforce.

## Features

### Data Extraction
- **NetSuite Integration** - OAuth 2.0 authenticated access to vendor, customer, and transaction data
- **Salesforce Integration** - Revenue pipeline, opportunity, and customer data via MCP tools
- **Read-Only Enforcement** - Application only reads data, never writes

### Financial Analytics
- **Vendor Analysis** - Top vendors by spend, duplicate detection, payment terms
- **Revenue Analysis** - Monthly trends, growth rates, customer lifetime value
- **Pipeline Analysis** - Salesforce opportunity pipeline, weighted forecasts, industry breakdown
- **Financial KPIs** - Profitability metrics, efficiency ratios, cash flow metrics
- **Forecasting** - Time series analysis, seasonality detection, trend forecasting

### Data Storage
- **PostgreSQL** - Star schema for financial reporting
- **Analysis Cache** - Pre-computed metrics for fast querying
- **Schema Resilience** - Flexible JSONB fields for changing data

## Technology Stack

- **Language:** Python 3.12+
- **Package Manager:** UV (fast, deterministic)
- **CLI Framework:** Typer (type-safe commands)
- **Database:** PostgreSQL + SQLAlchemy ORM
- **HTTP Client:** httpx (async-capable, retries)
- **Data Analysis:** Pandas, NumPy
- **Validation:** Pydantic v2
- **Type Checking:** Pyright (strict mode)
- **Linting/Formatting:** Ruff
- **Console UI:** Rich (tables, progress bars)

## Prerequisites

- Python 3.12+
- PostgreSQL 13+ database
- NetSuite account with OAuth 2.0 credentials
- UV package manager

## Installation

### 1. Install UV

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and Install

```bash
cd apps/financial-analytics
uv sync
```

### 3. Configure

Create `.env` from template:

```bash
cp .env.example .env
# Edit .env with your credentials
```

Edit `config.yaml` to match your environment:

```yaml
database:
  host: localhost
  port: 5432
  name: financial_analytics

netsuite:
  account_id: "YOUR_ACCOUNT_ID"

salesforce:
  enabled: true  # Set to false to disable Salesforce integration

analytics:
  default_period_months: 12
  vendor_analysis_top_n: 25
  duplicate_threshold: 0.85
```

### 4. Initialize Database

```bash
uv run fin-analytics init
```

## Usage

### Sync Data from NetSuite and Salesforce

```bash
# Sync all data (NetSuite + Salesforce)
uv run fin-analytics sync

# Sync vendors only (NetSuite)
uv run fin-analytics sync --vendors-only

# Sync customers only (NetSuite)
uv run fin-analytics sync --customers-only

# Sync Salesforce only
uv run fin-analytics sync --salesforce-only

# Force full sync
uv run fin-analytics sync --full
```

### Run Financial Analysis

```bash
# Comprehensive analysis
uv run fin-analytics analyze

# Analyze last 6 months
uv run fin-analytics analyze --months 6
```

### Vendor Analysis

```bash
# Top 25 vendors by spend
uv run fin-analytics vendors

# Top 10 vendors
uv run fin-analytics vendors --top 10

# Detect duplicate vendors
uv run fin-analytics vendors --duplicates
```

### Revenue Analysis

```bash
# Revenue trends (NetSuite invoices)
uv run fin-analytics revenue

# Revenue for last 18 months
uv run fin-analytics revenue --months 18

# Customer lifetime value
uv run fin-analytics revenue --ltv
```

### Salesforce Pipeline Analysis

```bash
# Opportunity pipeline analysis
uv run fin-analytics pipeline

# Revenue by industry
uv run fin-analytics pipeline --by-industry
```

## Development

### Code Quality

```bash
# Type checking (strict mode - MUST pass)
uv run pyright

# Linting
uv run ruff check .

# Formatting
uv run ruff format .

# All checks
make typecheck && make lint
```

### Makefile Commands

```bash
make install    # Install dependencies
make init       # Initialize database
make sync       # Sync data from NetSuite
make typecheck  # Run Pyright
make lint       # Run Ruff linter
make format     # Format code
make clean      # Remove build artifacts
```

## Architecture

```
src/financial_analytics/
├── core/              # Configuration, exceptions, constants
│   ├── config.py      # Dual-source config (.env + YAML)
│   ├── exceptions.py  # Custom exceptions
│   └── constants.py   # Immutable values
├── extractors/        # NetSuite & Salesforce integration
│   ├── netsuite_auth.py    # OAuth 2.0
│   ├── netsuite_client.py  # Read-only HTTP client
│   ├── netsuite_models.py  # Pydantic models
│   └── netsuite_queries.py # Data extraction
├── db/                # Database layer
│   ├── models.py      # SQLAlchemy star schema
│   └── session.py     # Session management
├── analytics/         # Analysis engines
│   ├── vendor_analysis.py   # Vendor spend & duplicates
│   └── revenue_analysis.py  # Revenue trends & LTV
└── cli/               # CLI commands
    ├── main.py        # Typer app
    ├── init.py        # Database init
    ├── sync.py        # Data sync
    └── analyze.py     # Analysis commands
```

## Design Principles

### Fail-Fast Discipline
- No default values for critical configuration
- All errors propagate with clear messages
- Missing credentials or config = immediate failure

### Read-Only Enforcement
- NetSuite client only allows GET requests
- Raises `ReadOnlyViolationError` for write attempts
- Data flows one way: NetSuite → PostgreSQL → Analysis

### Type Safety
- Pyright strict mode enabled
- All functions have type hints
- Pydantic validation at API boundaries
- SQLAlchemy typed mappings

### Module Size Discipline
- All modules < 300 lines
- Clear separation of concerns
- Single responsibility per module

## Database Schema

### Dimension Tables
- `dim_vendors` - Vendor master data
- `dim_customers` - Customer master data
- `dim_accounts` - Chart of accounts

### Fact Tables
- `fact_vendor_bills` - Vendor transactions
- `fact_invoices` - Customer invoices

### Analysis Cache Tables
- `vendor_spend_analysis` - Pre-computed vendor metrics
- `revenue_trends` - Monthly revenue aggregations
- `financial_kpis` - Cached KPI calculations

## Configuration

### config.yaml (Required)

Application settings and tunable parameters.

### .env (Required)

Sensitive credentials (never commit):
- `NS_CLIENT_ID` - NetSuite OAuth consumer key
- `NS_CLIENT_SECRET` - NetSuite OAuth consumer secret
- `DB_USER` - PostgreSQL username
- `DB_PASSWORD` - PostgreSQL password

## Error Handling

All exceptions inherit from `FinancialAnalyticsError`:
- `ConfigurationError` - Missing or invalid config
- `NetSuiteConnectionError` - API connection failure
- `NetSuiteAPIError` - API error response
- `ReadOnlyViolationError` - Write attempt on read-only client
- `DatabaseError` - Database operation failure

Errors are caught only at top-level CLI for user-friendly messages.

## Related Applications

- **vendor-analysis** - Specialized vendor cost analysis CLI
- **financial-dashboard** - React PWA for visualization

## License

Internal PDI Technologies application.
