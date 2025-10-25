# Cost Analysis CLI - Complete Example

This document showcases the **vendor-analysis** CLI application from `/opt/ns/apps/vendor-analysis` as a production reference implementation of vendor cost analytics.

## Contents

- [Application Overview](#application-overview)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration Architecture](#configuration-architecture)
  - [Dual-Source Configuration Pattern](#dual-source-configuration-pattern)
  - [Configuration Implementation](#configuration-implementation)
- [Data Layer Architecture](#data-layer-architecture)
  - [Database Models](#database-models)
  - [Sync Pattern](#sync-pattern)
- [NetSuite Integration Layer](#netsuite-integration-layer)
  - [Read-Only HTTP Client](#read-only-http-client)
- [Analysis Layer](#analysis-layer)
  - [Vendor Spend Analysis](#vendor-spend-analysis)
  - [Duplicate Detection](#duplicate-detection)
- [CLI Layer](#cli-layer)
  - [Main CLI Application](#main-cli-application)
  - [Analyze Command with Rich Output](#analyze-command-with-rich-output)
- [Usage Examples](#usage-examples)
- [Development Workflow](#development-workflow)
- [Key Takeaways](#key-takeaways)

## Application Overview

The vendor-analysis application is a Python 3.12+ CLI tool that demonstrates enterprise-grade financial analytics patterns:

- Read-only NetSuite integration (OAuth 2.0)
- Local PostgreSQL data warehouse
- Vendor spend analysis and ranking
- Duplicate vendor detection
- Fail-fast configuration management
- Strict type safety with Pyright

## Architecture

```
vendor-analysis/
├── src/vendor_analysis/
│   ├── core/           # Configuration, exceptions, constants
│   ├── netsuite/       # NetSuite API integration
│   ├── db/             # PostgreSQL layer
│   ├── analysis/       # Business logic
│   └── cli/            # CLI commands
├── config.yaml         # Application settings (REQUIRED)
├── .env                # Credentials (REQUIRED)
└── pyproject.toml      # Python dependencies
```

### Technology Stack

- **Python 3.12+** with strict type hints (Pyright)
- **UV** package manager
- **Typer** CLI framework
- **SQLAlchemy** ORM with PostgreSQL
- **Pydantic** for validation
- **Pandas** for aggregation
- **httpx** for HTTP with retry logic
- **Rich** for terminal UI

## Installation

```bash
cd apps/vendor-analysis

# Install dependencies
uv sync

# Initialize database
uv run vendor-analysis init-db
```

## Configuration Architecture

### Dual-Source Configuration Pattern

The application uses a fail-fast dual-source configuration:

1. **`.env`** - Sensitive credentials (REQUIRED)
2. **`config.yaml`** - Application settings (REQUIRED)

Missing either file causes immediate failure with clear error messages.

**`.env` example:**
```bash
# NetSuite OAuth 2.0 credentials
NS_ACCOUNT_ID=your_account_id
NS_CLIENT_ID=your_consumer_key
NS_CLIENT_SECRET=your_consumer_secret

# Database credentials
DB_USER=postgres
DB_PASSWORD=your_db_password
```

**`config.yaml` example:**
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

### Configuration Implementation

**File:** `src/vendor_analysis/core/config.py`

```python
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class DatabaseConfig(BaseModel):
    """Database configuration from YAML."""
    host: str
    port: int
    name: str

class AnalysisConfig(BaseModel):
    """Analysis configuration from YAML."""
    duplicate_similarity_threshold: float
    trend_analysis_months: int
    top_vendors_default: int
    page_size: int
    max_retries: int
    retry_delay_seconds: int

class YAMLConfig(BaseModel):
    """Complete YAML configuration structure."""
    database: DatabaseConfig
    application: ApplicationConfig
    analysis: AnalysisConfig

class Settings(BaseSettings):
    """
    Application settings from .env and config.yaml.

    FAIL-FAST: All credentials are REQUIRED from .env
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # NetSuite OAuth 2.0 credentials (REQUIRED)
    ns_account_id: str = Field(..., description="NetSuite account ID")
    ns_client_id: str = Field(..., description="OAuth 2.0 consumer key")
    ns_client_secret: str = Field(..., description="OAuth 2.0 consumer secret")

    # Database credentials (REQUIRED)
    db_user: str = Field(..., description="Database user")
    db_password: str = Field(..., description="Database password")

    # YAML config (loaded separately)
    _yaml_config: YAMLConfig | None = None

    @field_validator("ns_account_id", "ns_client_id", "ns_client_secret", mode="before")
    @classmethod
    def validate_required_env(cls, v: Any, info: Any) -> str:
        """Ensure required environment variables are set."""
        if not v:
            raise ConfigurationError(
                f"{info.field_name} is required in .env file"
            )
        return str(v)

    @property
    def yaml_config(self) -> YAMLConfig:
        """Get YAML configuration (lazy loaded)."""
        if self._yaml_config is None:
            config_path = Path("config.yaml")
            self._yaml_config = load_yaml_config(config_path)
        return self._yaml_config

    @property
    def database_url(self) -> str:
        """PostgreSQL connection URL from .env + config.yaml."""
        db_config = self.yaml_config.database
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{db_config.host}:{db_config.port}/{db_config.name}"
        )
```

**Key Design Principles:**

1. **No defaults for critical settings** - Forces explicit configuration
2. **Fail-fast validation** - Errors on startup, not during execution
3. **Pydantic models** - Type-safe configuration with clear errors
4. **Lazy loading** - YAML loaded when first accessed
5. **Composite properties** - `database_url` combines .env + YAML

## Data Layer Architecture

### Database Models

**File:** `src/vendor_analysis/db/models.py`

```python
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""
    pass

class VendorRecord(Base):
    """Vendor master data from NetSuite."""

    __tablename__ = "vendors"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(500))
    email: Mapped[str | None] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(50))
    is_inactive: Mapped[bool] = mapped_column(Boolean, default=False)
    currency: Mapped[str | None] = mapped_column(String(3))
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("ix_vendors_entity_id", "entity_id"),
        Index("ix_vendors_company_name", "company_name"),
    )

class TransactionRecord(Base):
    """Vendor transaction data from NetSuite."""

    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    vendor_id: Mapped[str] = mapped_column(String(50), nullable=False)
    tran_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    tran_type: Mapped[str | None] = mapped_column(String(50))
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str | None] = mapped_column(String(3))
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("ix_transactions_vendor_id", "vendor_id"),
        Index("ix_transactions_tran_date", "tran_date"),
    )
```

**Design Patterns:**

1. **Mapped type hints** - Python 3.12+ syntax for clarity
2. **UTC timestamps** - All datetime values use UTC
3. **Indexes on query columns** - Optimized for analytics queries
4. **Nullable fields** - Only when truly optional
5. **No foreign key constraints** - Read-only system, data comes from NetSuite

## NetSuite Integration Layer

### Read-Only HTTP Client

**File:** `src/vendor_analysis/netsuite/client.py`

```python
import httpx
from vendor_analysis.core.constants import ALLOWED_HTTP_METHODS
from vendor_analysis.core.exceptions import ReadOnlyViolationError

class NetSuiteClient:
    """
    Read-only NetSuite client with fail-fast enforcement.

    CRITICAL: Only GET requests are allowed.
    """

    def __init__(self, auth: NetSuiteAuth, base_url: str, settings: Settings):
        self.auth = auth
        self.base_url = base_url
        self.settings = settings

    def _enforce_read_only(self, method: str) -> None:
        """
        Enforce read-only access.

        Raises:
            ReadOnlyViolationError: If method is not GET
        """
        if method.upper() not in ALLOWED_HTTP_METHODS:
            raise ReadOnlyViolationError(
                f"Write operation attempted: {method}. "
                f"This application is READ-ONLY. "
                f"Allowed methods: {ALLOWED_HTTP_METHODS}"
            )

    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """
        Make HTTP request with retries and error handling.

        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional httpx request parameters

        Returns:
            Response JSON

        Raises:
            ReadOnlyViolationError: If method is not GET
            NetSuiteConnectionError: Connection failures
            NetSuiteAPIError: API errors
        """
        self._enforce_read_only(method)

        url = f"{self.base_url}{endpoint}"
        headers = {"Authorization": f"Bearer {self.auth.get_token()}"}

        for attempt in range(self.settings.max_retries):
            try:
                with httpx.Client() as client:
                    response = client.request(
                        method,
                        url,
                        headers=headers,
                        timeout=30.0,
                        **kwargs
                    )
                    response.raise_for_status()
                    return response.json()

            except httpx.HTTPError as e:
                if attempt == self.settings.max_retries - 1:
                    raise NetSuiteAPIError(f"API request failed: {e}") from e
                time.sleep(self.settings.retry_delay)

    def get_record(self, record_type: str, record_id: str) -> dict:
        """Get single record by ID (READ-ONLY)."""
        return self._request("GET", f"/record/v1/{record_type}/{record_id}")

    def query_records(self, query: str, limit: int = 100, offset: int = 0) -> dict:
        """Query records (READ-ONLY)."""
        params = {"q": query, "limit": limit, "offset": offset}
        return self._request("GET", "/query/v1/suiteql", params=params)
```

**Security Features:**

1. **Method whitelist** - Only GET allowed (`ALLOWED_HTTP_METHODS = frozenset(["GET"])`)
2. **Pre-request validation** - Fails before sending request
3. **Immutable constants** - `frozenset` prevents modification
4. **Clear error messages** - Explains why operation was blocked

## Analysis Layer

### Vendor Spend Analysis

**File:** `src/vendor_analysis/analysis/vendors.py`

```python
from dataclasses import dataclass
from datetime import datetime

import pandas as pd
from sqlalchemy.orm import Session

@dataclass
class VendorSpendSummary:
    """Vendor spend summary data."""

    vendor_id: str
    vendor_name: str
    total_spend: float
    transaction_count: int
    average_transaction: float
    currency: str | None
    last_transaction_date: datetime | None

def analyze_vendor_spend(
    session: Session,
    settings: Settings,
    vendor_id: str | None = None,
) -> list[VendorSpendSummary]:
    """
    Analyze vendor spend with transaction aggregation.

    Pattern: SQLAlchemy query -> Pandas aggregation -> Sorted results
    """
    query = session.query(TransactionRecord)
    if vendor_id:
        query = query.filter(TransactionRecord.vendor_id == vendor_id)

    transactions = query.all()

    if not transactions:
        return []

    # Convert to pandas for analysis
    df = pd.DataFrame([
        {
            "vendor_id": t.vendor_id,
            "amount": t.amount,
            "tran_date": t.tran_date,
            "currency": t.currency,
        }
        for t in transactions
    ])

    summary_data: list[VendorSpendSummary] = []

    for vendor_id_group, group_df in df.groupby("vendor_id"):
        vendor = session.query(VendorRecord).filter_by(id=str(vendor_id_group)).first()
        if not vendor:
            continue

        summary = VendorSpendSummary(
            vendor_id=str(vendor_id_group),
            vendor_name=vendor.company_name or vendor.entity_id,
            total_spend=float(group_df["amount"].sum()),
            transaction_count=len(group_df),
            average_transaction=float(group_df["amount"].mean()),
            currency=group_df["currency"].iloc[0] if not group_df["currency"].isna().all() else None,
            last_transaction_date=group_df["tran_date"].max(),
        )
        summary_data.append(summary)

    # Sort by total spend descending
    summary_data.sort(key=lambda x: x.total_spend, reverse=True)

    return summary_data
```

### Duplicate Detection

**File:** `src/vendor_analysis/analysis/duplicates.py`

```python
from dataclasses import dataclass
from difflib import SequenceMatcher

from sqlalchemy.orm import Session

@dataclass
class DuplicatePair:
    """Potential duplicate vendor pair."""

    vendor_1_id: str
    vendor_1_name: str
    vendor_2_id: str
    vendor_2_name: str
    similarity_score: float

def calculate_similarity(str1: str, str2: str) -> float:
    """
    Calculate similarity between two strings.

    Uses difflib SequenceMatcher (standard library, no ML dependencies)
    """
    if not str1 or not str2:
        return 0.0

    # Normalize strings
    s1 = str1.lower().strip()
    s2 = str2.lower().strip()

    return SequenceMatcher(None, s1, s2).ratio()

def detect_duplicate_vendors(
    session: Session,
    settings: Settings,
    threshold: float | None = None,
) -> list[DuplicatePair]:
    """
    Detect potential duplicate vendors using fuzzy matching.

    Complexity: O(n^2) - Acceptable for vendor counts < 10,000
    """
    if threshold is None:
        threshold = settings.duplicate_threshold

    vendors = session.query(VendorRecord).filter_by(is_inactive=False).all()
    duplicates: list[DuplicatePair] = []

    # Compare all pairs
    for i, vendor1 in enumerate(vendors):
        name1 = vendor1.company_name or vendor1.entity_id

        for vendor2 in vendors[i + 1:]:
            name2 = vendor2.company_name or vendor2.entity_id

            similarity = calculate_similarity(name1, name2)

            if similarity >= threshold:
                duplicates.append(
                    DuplicatePair(
                        vendor_1_id=vendor1.id,
                        vendor_1_name=name1,
                        vendor_2_id=vendor2.id,
                        vendor_2_name=name2,
                        similarity_score=similarity,
                    )
                )

    # Sort by similarity score descending
    duplicates.sort(key=lambda x: x.similarity_score, reverse=True)

    return duplicates
```

## CLI Layer

### Main CLI Application

**File:** `src/vendor_analysis/cli/main.py`

```python
import typer
from rich.console import Console

app = typer.Typer(
    name="vendor-analysis",
    help="Vendor cost analysis and management for NetSuite",
    add_completion=False,
)
console = Console()

@app.command()
def init_db():
    """Initialize database schema."""
    from vendor_analysis.core.config import get_settings
    from vendor_analysis.db.session import init_database

    settings = get_settings()
    init_database(settings)
    console.print("[green]Database initialized successfully")

@app.command()
def sync(
    vendors_only: bool = typer.Option(False, "--vendors-only"),
    transactions_only: bool = typer.Option(False, "--transactions-only"),
):
    """Sync data from NetSuite."""
    from vendor_analysis.cli.sync import sync_command

    sync_command(vendors_only, transactions_only)

@app.command()
def analyze(
    top: int = typer.Option(None, "--top", help="Number of top vendors"),
):
    """Analyze vendor spend."""
    from vendor_analysis.cli.analyze import analyze_command

    analyze_command(top)

@app.command()
def duplicates(
    threshold: float = typer.Option(None, "--threshold", min=0.0, max=1.0),
):
    """Detect duplicate vendors."""
    from vendor_analysis.cli.duplicates import duplicates_command

    duplicates_command(threshold)

def main():
    """Entry point with error handling."""
    try:
        app()
    except Exception as e:
        console.print(f"[red]Error: {e}")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    main()
```

### Analyze Command with Rich Output

**File:** `src/vendor_analysis/cli/analyze.py`

```python
from rich.console import Console
from rich.table import Table

from vendor_analysis.analysis.vendors import get_top_vendors
from vendor_analysis.core.config import get_settings
from vendor_analysis.db.session import get_session

console = Console()

def analyze_command(top: int | None = None):
    """Run vendor spend analysis."""
    settings = get_settings()
    session = get_session(settings)

    console.print("[cyan]Analyzing vendor spend...")

    summaries = get_top_vendors(session, settings, top_n=top)

    if not summaries:
        console.print("[yellow]No vendor data found. Run 'sync' first.")
        return

    # Create Rich table
    table = Table(title=f"Top {len(summaries)} Vendors by Spend")
    table.add_column("Rank", style="cyan", justify="right")
    table.add_column("Vendor Name", style="white")
    table.add_column("Total Spend", style="green", justify="right")
    table.add_column("Transactions", style="yellow", justify="right")
    table.add_column("Avg Transaction", style="magenta", justify="right")

    for i, vendor in enumerate(summaries, 1):
        table.add_row(
            str(i),
            vendor.vendor_name,
            f"${vendor.total_spend:,.2f}",
            str(vendor.transaction_count),
            f"${vendor.average_transaction:,.2f}",
        )

    console.print(table)
```

## Usage Examples

### Initialize Database

```bash
uv run vendor-analysis init-db
```

Output:
```
Database initialized successfully
```

### Sync Data from NetSuite

```bash
# Sync both vendors and transactions
uv run vendor-analysis sync

# Sync only vendors
uv run vendor-analysis sync --vendors-only

# Sync only transactions
uv run vendor-analysis sync --transactions-only
```

Output:
```
Syncing vendors... 89/89 [████████████████████] 100%
Syncing transactions... 234/234 [███████████████] 100%
Sync completed successfully
```

### Analyze Vendor Spend

```bash
# Default top 10 vendors
uv run vendor-analysis analyze

# Top 25 vendors
uv run vendor-analysis analyze --top 25
```

Output:
```
Top 10 Vendors by Spend
─────────────────────────────────────────────
Rank  Vendor Name           Total Spend  Txns
─────────────────────────────────────────────
  1   Office Supplies Co    $125,450.00   89
  2   Tech Solutions Inc    $98,230.50    23
  3   Shipping Partners     $76,890.25   156
  4   Marketing Agency      $65,000.00    12
  5   Cloud Services LLC    $52,400.00    12
...
```

### Detect Duplicate Vendors

```bash
# Default threshold (0.85)
uv run vendor-analysis duplicates

# Custom threshold (0.90)
uv run vendor-analysis duplicates --threshold 0.90
```

Output:
```
Potential Duplicate Vendors
────────────────────────────────────────────
Vendor 1              Vendor 2            Score
────────────────────────────────────────────
Office Supply Co      Office Supplies Co  95.2%
ABC Company           ABC Co              92.3%
Tech Solutions Inc    Tech Solutions LLC  88.7%
...
```

## Development Workflow

### Code Quality Checks

```bash
# Type checking (strict mode, MUST pass)
uv run pyright

# Linting
uv run ruff check .

# Formatting
uv run ruff format .

# All checks
uv run pyright && uv run ruff check . && uv run ruff format --check .
```

### Testing Workflow

1. Configure `.env` and `config.yaml`
2. Run `init-db` to create schema
3. Run `sync` to fetch data from NetSuite
4. Run `analyze` or `duplicates` to verify analysis logic

## Key Takeaways

### Architectural Patterns

1. **Fail-Fast Configuration** - No defaults, immediate failures
2. **Read-Only Enforcement** - Multiple layers of protection
3. **Type Safety** - Pyright strict mode, Pydantic validation
4. **Data Validation Boundaries** - Pydantic at API, SQLAlchemy at DB
5. **Module Size Limits** - All files under 300 lines

### Technology Choices

1. **UV over pip** - Faster, deterministic dependency resolution
2. **Typer over argparse** - Type-safe CLI with auto-docs
3. **Pandas for aggregation** - Rich time-series operations
4. **difflib for fuzzy matching** - Standard library, no ML overhead
5. **Rich for terminal UI** - Professional CLI output

### Production Best Practices

1. **Decimal for currency** - Avoid float precision errors
2. **UTC for timestamps** - Timezone consistency
3. **Indexes on query columns** - Performance optimization
4. **Retry logic with backoff** - Resilient API calls
5. **Audit trails** - `synced_at` timestamps on all records

## Source Code

Full source code available at:
```
/opt/ns/apps/vendor-analysis/
```

## Related Documentation

- [Vendor Analytics Reference](../reference/vendor-analytics.md) - Detailed vendor analytics patterns
- [NetSuite Integration](../integrations/netsuite.md) - NetSuite data extraction
- [CLAUDE.md](/opt/ns/CLAUDE.md) - Repository development guide
