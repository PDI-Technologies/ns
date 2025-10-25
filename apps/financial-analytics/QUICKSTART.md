# Financial Analytics - Quick Start Guide

## Installation (5 minutes)

```bash
cd /opt/ns/apps/financial-analytics

# 1. Install dependencies
uv sync

# 2. Configure credentials
cp .env.example .env
# Edit .env with your NetSuite and Salesforce credentials

# 3. Configure settings
# Edit config.yaml - update database connection and NetSuite account_id

# 4. Initialize database
uv run fin-analytics init
```

## First Sync (15-30 minutes depending on data volume)

```bash
# Sync everything
uv run fin-analytics sync

# Or sync incrementally
uv run fin-analytics sync --vendors-only          # NetSuite vendors
uv run fin-analytics sync --customers-only        # NetSuite customers  
uv run fin-analytics sync --salesforce-only       # Salesforce opportunities
```

## Run Analysis

```bash
# Comprehensive overview
uv run fin-analytics analyze

# Vendor cost analysis
uv run fin-analytics vendors --top 25
uv run fin-analytics vendors --duplicates

# Revenue analysis
uv run fin-analytics revenue --months 12
uv run fin-analytics revenue --ltv

# Salesforce pipeline (requires Salesforce sync)
uv run fin-analytics pipeline
uv run fin-analytics pipeline --by-industry
```

## Troubleshooting

### Configuration Errors

**Error:** `Configuration file not found: config.yaml`
**Fix:** Ensure you're in `/opt/ns/apps/financial-analytics/` directory

**Error:** `Arguments missing for parameters "ns_client_id"`
**Fix:** Create `.env` file with required credentials

### Database Errors

**Error:** `Failed to create database session`
**Fix:** Ensure PostgreSQL is running and credentials in `.env` are correct

**Error:** Database connection refused
**Fix:** Check `config.yaml` database host/port settings

### NetSuite Errors

**Error:** `Failed to obtain OAuth 2.0 token`
**Fix:** Verify NS_CLIENT_ID and NS_CLIENT_SECRET in `.env` are correct

**Error:** `NetSuite API error (HTTP 401)`
**Fix:** OAuth credentials may be invalid or expired

### Salesforce Errors

**Error:** `Salesforce integration is not enabled`
**Fix:** Set `SF_ENABLED=true` in `.env` and `enabled: true` in `config.yaml`

**Error:** MCP tool not available
**Fix:** Ensure Claude Code environment has pdi-salesforce-sse3 MCP server configured

## Daily Usage

```bash
# Morning: Sync latest data
uv run fin-analytics sync

# Analyze vendor spend for procurement review
uv run fin-analytics vendors --top 50

# Check revenue pipeline for sales forecast
uv run fin-analytics pipeline

# Monthly: Run comprehensive analysis
uv run fin-analytics analyze --months 12
```

## Development

```bash
# Code quality checks
make typecheck  # Pyright strict mode
make lint       # Ruff linting
make format     # Code formatting

# Clean build artifacts
make clean
```

## Next Steps

1. **Schedule regular syncs** - Set up cron job or scheduled task for daily sync
2. **Build dashboards** - Use data in PostgreSQL for Tableau/PowerBI/Custom dashboards
3. **Export reports** - Add CSV/Excel export commands (future enhancement)
4. **Add forecasting** - Implement time series forecasting (future enhancement)
