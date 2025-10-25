.PHONY: help install sync init typecheck lint format clean

help:
	@echo "Available commands:"
	@echo "  make install     Install dependencies with UV"
	@echo "  make init        Initialize database schema"
	@echo "  make sync        Sync data from NetSuite"
	@echo "  make typecheck   Run Pyright type checking"
	@echo "  make lint        Run Ruff linter"
	@echo "  make format      Format code with Ruff"
	@echo "  make clean       Remove build artifacts"

install:
	uv sync

init:
	uv run fin-analytics init

sync:
	uv run fin-analytics sync

typecheck:
	uv run pyright

lint:
	uv run ruff check .

format:
	uv run ruff format .

clean:
	rm -rf dist/ build/ *.egg-info .venv
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
