# NetSuite Operations Repository
# Build, packaging, and development tasks

.PHONY: help install build typecheck lint format clean test

# Default target
help:
	@echo "NetSuite Operations - Build & Development"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install           Install all app dependencies"
	@echo "  make install-vendor    Install vendor-analysis dependencies"
	@echo ""
	@echo "Build & Package:"
	@echo "  make build             Build all applications"
	@echo "  make build-vendor      Build vendor-analysis package"
	@echo ""
	@echo "Code Quality:"
	@echo "  make typecheck         Run type checking (all apps)"
	@echo "  make lint              Run linting (all apps)"
	@echo "  make format            Format code (all apps)"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean             Remove generated files and build artifacts"
	@echo "  make clean-vendor      Clean vendor-analysis only"
	@echo ""
	@echo "Application Bootstrapping:"
	@echo "  make bootstrap-vendor  Run vendor-analysis bootstrap script"

# Install all dependencies
install: install-vendor

# Install vendor-analysis dependencies
install-vendor:
	@echo "Installing vendor-analysis dependencies..."
	@cd apps/vendor-analysis && uv sync

# Build all applications
build: build-vendor

# Build vendor-analysis package
build-vendor:
	@echo "Building vendor-analysis package..."
	@cd apps/vendor-analysis && uv build

# Run type checking on all apps
typecheck:
	@echo "Type checking vendor-analysis..."
	@cd apps/vendor-analysis && uv run pyright || true

# Run linting on all apps
lint:
	@echo "Linting vendor-analysis..."
	@cd apps/vendor-analysis && uv run ruff check . || true

# Format all apps
format:
	@echo "Formatting vendor-analysis..."
	@cd apps/vendor-analysis && uv run ruff format .

# Clean all generated files
clean: clean-vendor
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

# Bootstrap vendor-analysis
bootstrap-vendor:
	@echo "Running vendor-analysis bootstrap..."
	@cd apps/vendor-analysis && python3 scripts/bootstrap.py
