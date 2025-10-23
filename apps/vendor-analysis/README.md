# Vendor Analysis CLI

Read-only NetSuite vendor cost analysis and management application.

## Features

- Sync vendors and transactions from NetSuite (read-only via OAuth 2.0)
- Analyze vendor spend and identify top vendors
- Detect potential duplicate vendors using fuzzy matching
- Store data locally in PostgreSQL for fast analysis
- Fail-fast design with strict configuration validation

## Architecture

- **Language**: Python 3.12+
- **Package Manager**: UV
- **Linter/Formatter**: Ruff
- **Type Checker**: Pyright (strict mode)
- **CLI Framework**: Typer
- **Database**: PostgreSQL with SQLAlchemy
- **NetSuite Integration**: SuiteTalk REST API with OAuth 2.0

## Prerequisites

- Python 3.12+
- PostgreSQL database
- NetSuite account with OAuth 2.0 credentials
- UV package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)

## Setup

### 1. Install Dependencies

```bash
cd apps/vendor-analysis
uv sync
```

### 2. Configure Environment

Create `.env` file (from parent repo):
```bash
ln -s ../../.env .env
```

Or copy credentials:
```bash
# .env
NS_ACCOUNT_ID=your_account_id
NS_CLIENT_ID=your_consumer_key
NS_CLIENT_SECRET=your_consumer_secret
DB_USER=postgres
DB_PASSWORD=your_db_password
```

### 3. Configure Application

Edit `config.yaml` to customize settings (database, analysis thresholds, etc.)

### 4. Initialize Database

```bash
uv run vendor-analysis init-db
```

## Usage

### Sync Data from NetSuite

```bash
# Sync both vendors and transactions
uv run vendor-analysis sync

# Sync only vendors
uv run vendor-analysis sync --vendors-only

# Sync only transactions
uv run vendor-analysis sync --transactions-only
```

### Analyze Vendor Spend

```bash
# Show top 10 vendors
uv run vendor-analysis analyze

# Show top 25 vendors
uv run vendor-analysis analyze --top 25
```

### Find Duplicate Vendors

```bash
# Use default threshold (0.85)
uv run vendor-analysis duplicates

# Use custom threshold
uv run vendor-analysis duplicates --threshold 0.90
```

## Configuration

### config.yaml

All application settings are in `config.yaml`:

```yaml
database:
  host: localhost
  port: 5432
  name: vendor_analysis

application:
  log_level: INFO

analysis:
  duplicate_similarity_threshold: 0.85
  trend_analysis_months: 12
  top_vendors_default: 10
  page_size: 100
  max_retries: 3
  retry_delay_seconds: 2
```

**IMPORTANT**: Application fails if `config.yaml` is missing or invalid.

### .env

Credentials are stored in `.env`:

```
NS_ACCOUNT_ID=...
NS_CLIENT_ID=...
NS_CLIENT_SECRET=...
DB_USER=...
DB_PASSWORD=...
```

**IMPORTANT**: Application fails if any required credential is missing.

## Development

### Code Quality

```bash
# Type check (strict mode)
uv run pyright

# Lint and format
uv run ruff check .
uv run ruff format .

# All checks
uv run pyright && uv run ruff check . && uv run ruff format --check .
```

### Module Organization

All modules follow strict size limits (<300 lines):

- `core/` - Configuration, exceptions, constants
- `netsuite/` - NetSuite API client (read-only), auth, queries
- `db/` - Database models and session management
- `analysis/` - Vendor analysis logic (vendors, duplicates)
- `cli/` - CLI commands (main, sync, analyze, duplicates)

## Read-Only Guarantee

This application is **read-only by design**:

1. OAuth 2.0 client enforces GET-only requests
2. Attempting any write operation raises `ReadOnlyViolationError`
3. No database writes to NetSuite
4. All data stored locally for analysis

## Fail-Fast Discipline

- No default values (except in `config.yaml`)
- No try/catch swallowing
- No fallback mechanisms
- Missing config = immediate failure
- All errors propagate with clear messages

## License

Internal PDI Technologies application.
