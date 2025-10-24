# Makefile for vendor-analysis
# Conservative wrapper around UV commands

.PHONY: help install setup sync analyze duplicates init-db typecheck lint format clean bootstrap-log

# Default target - show help
help:
	@echo "Vendor Analysis - Available Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install       Install dependencies (uv sync)"
	@echo "  make setup         Run bootstrap script (full setup)"
	@echo ""
	@echo "Database:"
	@echo "  make init-db       Initialize database schema"
	@echo ""
	@echo "Operations:"
	@echo "  make sync          Sync vendors and transactions from NetSuite"
	@echo "  make analyze       Analyze vendor spend (top 10)"
	@echo "  make duplicates    Find potential duplicate vendors"
	@echo ""
	@echo "Development:"
	@echo "  make typecheck     Run Pyright type checker (strict)"
	@echo "  make lint          Run Ruff linter"
	@echo "  make format        Format code with Ruff"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean         Remove generated files and logs"
	@echo "  make bootstrap-log View bootstrap.log"

# Install dependencies with UV
install:
	uv sync

# Run full bootstrap setup
setup:
	@echo "Running bootstrap script..."
	@python3 scripts/bootstrap.py

# Initialize database schema
init-db:
	uv run vendor-analysis init-db

# Sync data from NetSuite
sync:
	uv run vendor-analysis sync

# Sync only vendors
sync-vendors:
	uv run vendor-analysis sync --vendors-only

# Sync only transactions
sync-transactions:
	uv run vendor-analysis sync --transactions-only

# Analyze vendor spend (default top 10)
analyze:
	uv run vendor-analysis analyze

# Analyze top N vendors (e.g., make analyze-top N=25)
analyze-top:
	uv run vendor-analysis analyze --top $(N)

# Find duplicate vendors
duplicates:
	uv run vendor-analysis duplicates

# Find duplicates with custom threshold (e.g., make duplicates-threshold T=0.90)
duplicates-threshold:
	uv run vendor-analysis duplicates --threshold $(T)

# Run type checker (strict mode)
typecheck:
	uv run pyright

# Run linter
lint:
	uv run ruff check .

# Format code
format:
	uv run ruff format .

# Clean generated files
clean:
	@echo "Cleaning generated files..."
	@rm -f bootstrap.log
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Cleaned"

# View bootstrap log
bootstrap-log:
	@if [ -f bootstrap.log ]; then \
		less bootstrap.log; \
	else \
		echo "bootstrap.log not found. Run 'make setup' first."; \
	fi
