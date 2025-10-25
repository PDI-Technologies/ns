# NetSuite Operations Repository
# Build, packaging, and development tasks

.PHONY: help install build typecheck lint format clean test vendor-analysis install-libs typecheck-libs lint-libs format-libs install-fin build-fin clean-fin

# Default target
help:
	@echo "NetSuite Operations - Build & Development"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install           Install all dependencies (libs + apps)"
	@echo "  make install-libs      Install shared libraries only"
	@echo "  make install-vendor    Install vendor-analysis dependencies"
	@echo "  make install-fin       Install financial-analytics dependencies"
	@echo ""
	@echo "Build & Package:"
	@echo "  make build             Build all applications"
	@echo "  make build-vendor      Build vendor-analysis package"
	@echo "  make build-fin         Build financial-analytics package"
	@echo ""
	@echo "Code Quality:"
	@echo "  make typecheck         Run type checking (libs + apps)"
	@echo "  make typecheck-libs    Run type checking (libs only)"
	@echo "  make lint              Run linting (libs + apps)"
	@echo "  make lint-libs         Run linting (libs only)"
	@echo "  make format            Format code (libs + apps)"
	@echo "  make format-libs       Format code (libs only)"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean             Remove generated files and build artifacts"
	@echo "  make clean-vendor      Clean vendor-analysis only"
	@echo "  make clean-fin         Clean financial-analytics only"
	@echo ""
	@echo "Application Bootstrapping:"
	@echo "  make bootstrap-vendor  Run vendor-analysis bootstrap script"
	@echo ""
	@echo "Vendor Analysis CLI:"
	@echo "  make vendor-analysis -- <command> [options]"
	@echo ""
	@echo "  Examples:"
	@echo "    make vendor-analysis -- sync"
	@echo "    make vendor-analysis -- sync --vendors-only"
	@echo "    make vendor-analysis -- analyze --top 25"
	@echo "    make vendor-analysis -- duplicates --threshold 0.90"
	@echo ""
	@echo "  Note: The '--' separator is required for commands with flags"

# Install all dependencies
install: install-libs install-vendor install-fin

# Install shared libraries
install-libs:
	@echo "Installing shared libraries..."
	@cd libs/logger && uv sync

# Install vendor-analysis dependencies
install-vendor:
	@echo "Installing vendor-analysis dependencies..."
	@cd apps/vendor-analysis && uv sync

# Install financial-analytics dependencies
install-fin:
	@echo "Installing financial-analytics dependencies..."
	@cd apps/financial-analytics && uv sync

# Build all applications
build: build-vendor build-fin

# Build vendor-analysis package
build-vendor:
	@echo "Building vendor-analysis package..."
	@cd apps/vendor-analysis && uv build

# Build financial-analytics package
build-fin:
	@echo "Building financial-analytics package..."
	@cd apps/financial-analytics && uv build

# Run type checking on all apps and libs
typecheck: typecheck-libs
	@echo "Type checking vendor-analysis..."
	@cd apps/vendor-analysis && uv run pyright || true
	@echo "Type checking financial-analytics..."
	@cd apps/financial-analytics && uv run pyright || true

# Type check shared libraries
typecheck-libs:
	@echo "Type checking libs/logger..."
	@cd libs/logger && uv run pyright || true

# Run linting on all apps and libs
lint: lint-libs
	@echo "Linting vendor-analysis..."
	@cd apps/vendor-analysis && uv run ruff check . || true
	@echo "Linting financial-analytics..."
	@cd apps/financial-analytics && uv run ruff check . || true

# Lint shared libraries
lint-libs:
	@echo "Linting libs/logger..."
	@cd libs/logger && uv run ruff check . || true

# Format all apps and libs
format: format-libs
	@echo "Formatting vendor-analysis..."
	@cd apps/vendor-analysis && uv run ruff format .
	@echo "Formatting financial-analytics..."
	@cd apps/financial-analytics && uv run ruff format .

# Format shared libraries
format-libs:
	@echo "Formatting libs/logger..."
	@cd libs/logger && uv run ruff format .

# Clean all generated files
clean: clean-vendor clean-fin
	@echo "Cleaning repository root..."
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✓ Repository cleaned"

# Clean vendor-analysis
clean-vendor:
	@echo "Cleaning vendor-analysis..."
	@cd apps/vendor-analysis && rm -f bootstrap.log
	@cd apps/vendor-analysis && find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@cd apps/vendor-analysis && find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@cd apps/vendor-analysis && find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@cd apps/vendor-analysis && rm -rf dist/ build/ 2>/dev/null || true
	@echo "✓ vendor-analysis cleaned"

# Clean financial-analytics
clean-fin:
	@echo "Cleaning financial-analytics..."
	@cd apps/financial-analytics && find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@cd apps/financial-analytics && find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@cd apps/financial-analytics && find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@cd apps/financial-analytics && rm -rf dist/ build/ 2>/dev/null || true
	@echo "✓ financial-analytics cleaned"

# Bootstrap vendor-analysis
bootstrap-vendor:
	@echo "Running vendor-analysis bootstrap..."
	@cd apps/vendor-analysis && python3 scripts/bootstrap.py

# Run vendor-analysis CLI
# Usage: make vendor-analysis sync --vendors-only
vendor-analysis:
	@cd apps/vendor-analysis && uv run vendor-analysis $(filter-out $@,$(MAKECMDGOALS))

# Catch-all rule to prevent Make from treating arguments as targets
%:
	@:
