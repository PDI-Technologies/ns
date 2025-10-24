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

- **Python 3.12+** - Check: `python3 --version`
- **PostgreSQL database** - One of:
  - Existing Supabase local instance (recommended if already running)
  - Docker: `docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:17`
  - Native PostgreSQL installation
- **NetSuite account** with OAuth 2.0 credentials (see Setup section)
- **UV package manager** - Install: `curl -LsSf https://astral.sh/uv/install.sh | sh`

## Quick Setup (Recommended)

### Using Make (Simplest)

```bash
cd apps/vendor-analysis
make setup
```

### Using Bootstrap Script Directly

Use the idempotent bootstrap script for automated setup:

```bash
cd apps/vendor-analysis

# Install Rich (bootstrap script dependency, also used by main CLI)
pip install rich
# Or: uv pip install rich

# Run bootstrap (will install all other dependencies)
python3 scripts/bootstrap.py
```

**Note**: Rich must be installed separately because bootstrap.py runs *before* `uv sync`. After bootstrap completes, Rich will also be available as part of the main application dependencies.

The bootstrap script will:
- Check Python 3.12+
- Install/verify UV package manager
- Install dependencies
- Validate configuration files
- Check database connectivity
- Initialize database schema
- Verify CLI is working

**Idempotent**: Safe to run multiple times. See [scripts/README.md](scripts/README.md) for details.

## Manual Setup

If you prefer manual setup or the bootstrap fails:

### 1. Install Dependencies

```bash
cd apps/vendor-analysis
uv sync
```

This installs:
- Typer (CLI framework)
- httpx (HTTP client for NetSuite API)
- SQLAlchemy (ORM)
- Pandas (data analysis)
- Rich (terminal formatting)
- Pydantic (config validation)
- PyYAML (YAML parsing)
- psycopg2-binary (PostgreSQL driver)

### 2. Configure Database

#### Option A: Use Existing Supabase Instance (Recommended)

If you have Supabase running locally:

```bash
# Check if Supabase PostgreSQL is running
docker ps | grep supabase_db

# Create dedicated database (isolated from other apps)
docker exec -e PGPASSWORD=postgres supabase_db_supabase \
  psql -U supabase_admin -d postgres \
  -c "CREATE DATABASE vendor_analysis OWNER supabase_admin;"
```

Update `config.yaml`:
```yaml
database:
  host: localhost
  port: 54322              # Supabase port
  name: vendor_analysis
```

#### Option B: Use Standalone PostgreSQL

If using Docker:
```bash
docker run -d --name vendor-analysis-db \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=vendor_analysis \
  postgres:17
```

Update `config.yaml`:
```yaml
database:
  host: localhost
  port: 5432
  name: vendor_analysis
```

### 3. Configure NetSuite Credentials

#### Get OAuth 2.0 Credentials from NetSuite:

1. **Navigate to Integration Record**:
   - Setup > Integration > Manage Integrations > New

2. **Create Integration**:
   - Name: "Vendor Analysis CLI"
   - State: Enabled
   - Authentication: OAuth 2.0

3. **Copy Credentials**:
   - Consumer Key → `NS_CLIENT_ID`
   - Consumer Secret → `NS_CLIENT_SECRET`
   - Account ID → `NS_ACCOUNT_ID` (from URL: `https://{ACCOUNT_ID}.app.netsuite.com`)

4. **Save to `.env`**:

```bash
# From parent repository (if .env exists there)
ln -s ../../.env .env

# Or create new .env file
cat > .env << 'EOF'
# NetSuite OAuth 2.0
NS_ACCOUNT_ID=123456
NS_CLIENT_ID=your_consumer_key_here
NS_CLIENT_SECRET=your_consumer_secret_here

# Database (use credentials from step 2)
DB_USER=supabase_admin    # or postgres
DB_PASSWORD=postgres
EOF
```

**IMPORTANT**: Never commit `.env` to git (already in `.gitignore`)

### 4. Configure Application Settings

Edit `config.yaml` to customize:

```yaml
database:
  host: localhost
  port: 54322              # 5432 for standalone PostgreSQL
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

### 5. Initialize Database Schema

```bash
uv run vendor-analysis init-db
```

This creates tables:
- `vendors` - Vendor records from NetSuite
- `transactions` - Vendor bills/transactions
- `analysis_results` - Cached analysis results

### 6. Verify Setup

```bash
# Test CLI
uv run vendor-analysis --help

# Test database connection (will sync from NetSuite)
uv run vendor-analysis sync --vendors-only
```

## Usage

### Using Make (Recommended)

```bash
# Sync data from NetSuite
make sync

# Analyze vendor spend (top 10)
make analyze

# Find duplicate vendors
make duplicates

# With parameters
make analyze-top N=25
make duplicates-threshold T=0.90
```

**See all commands:**
```bash
make help
```

### Using UV Directly

```bash
# Sync both vendors and transactions
uv run vendor-analysis sync

# Sync only vendors
uv run vendor-analysis sync --vendors-only

# Sync only transactions
uv run vendor-analysis sync --transactions-only

# Analyze vendor spend
uv run vendor-analysis analyze --top 25

# Find duplicate vendors
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
