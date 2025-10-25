"""
Database initialization command.

Following python-cli-engineering idempotent patterns.
"""

import typer
from rich.console import Console
from rich.panel import Panel

from financial_analytics.core.config import Settings, get_logger
from financial_analytics.db.session import init_database

console = Console()


def init_command(
    force: bool = typer.Option(False, "--force", help="Force re-initialization"),
) -> None:
    """
    Initialize database schema.

    Creates all tables if they don't exist. Safe to run multiple times.
    """
    logger = get_logger()
    logger.info(f"Command: init (force={force})")

    console.print(Panel("[cyan]Initializing Database Schema[/cyan]"))

    try:
        settings = Settings()  # type: ignore[call-arg]  # Reads from .env at runtime
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        console.print(f"[red]Configuration error: {e}[/red]")
        raise typer.Exit(code=1) from e

    console.print(f"Database: {settings.yaml_config.database.name}")
    console.print(f"Host: {settings.yaml_config.database.host}")

    try:
        init_database(settings)
        logger.info("Database schema initialized successfully")
        console.print("[green]Database schema initialized successfully[/green]")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        console.print(f"[red]Failed to initialize database: {e}[/red]")
        raise typer.Exit(code=1) from e
