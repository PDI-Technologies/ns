"""
Main CLI entry point for vendor-analysis application.

All commands are read-only operations. Fail-fast on errors.
"""

import typer
from rich.console import Console

from vendor_analysis.core.config import get_logger, get_settings, initialize_logger
from vendor_analysis.core.exceptions import VendorAnalysisError

# Initialize logger at module level
initialize_logger()

app = typer.Typer(
    name="vendor-analysis",
    help="Read-only NetSuite vendor cost analysis and management CLI",
    add_completion=False,
)

console = Console()


@app.command()
def init_db(
    recreate: bool = typer.Option(
        False,
        "--recreate",
        help="Drop and recreate all tables (WARNING: deletes all data)",
    ),
) -> None:
    """
    Initialize database schema (creates tables).

    Use --recreate to drop existing tables and start fresh.
    WARNING: --recreate will delete all existing data.
    """
    from vendor_analysis.db.session import init_database

    logger = get_logger()
    logger.info(f"Command: init-db (recreate={recreate})")

    if recreate:
        console.print("[red]WARNING: Dropping all existing tables (data will be lost)[/red]")
        response = typer.confirm("Are you sure you want to continue?")
        if not response:
            console.print("[yellow]Cancelled[/yellow]")
            logger.info("User cancelled recreate operation")
            raise typer.Exit(0)

    console.print("[yellow]Initializing database...[/yellow]")
    settings = get_settings()
    init_database(settings, drop_existing=recreate)

    if recreate:
        console.print("[green]OK - Database recreated successfully[/green]")
        logger.info("Database recreated successfully")
    else:
        console.print("[green]OK - Database initialized successfully[/green]")
        logger.info("Database initialized successfully")


@app.command()
def sync(
    vendors_only: bool = typer.Option(False, "--vendors-only", help="Sync only vendors"),
    transactions_only: bool = typer.Option(
        False, "--transactions-only", help="Sync only transactions"
    ),
    full: bool = typer.Option(
        False, "--full", help="Force full sync (default: incremental sync)"
    ),
    limit: int | None = typer.Option(
        None, "--limit", help="Limit number of records to sync (for testing)"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be synced without storing to database"
    ),
) -> None:
    """
    Sync vendors and transactions from NetSuite to local database.

    By default, performs incremental sync (only changed/new records).
    Use --full to force complete re-sync of all records.
    Use --limit for quick testing with limited records.
    Use --dry-run to preview what would be synced.
    """
    from vendor_analysis.cli.sync import sync_command

    sync_command(
        vendors_only=vendors_only,
        transactions_only=transactions_only,
        full=full,
        limit=limit,
        dry_run=dry_run,
    )


@app.command()
def analyze(
    top: int = typer.Option(10, "--top", "-n", help="Number of top vendors to show"),
) -> None:
    """Analyze vendor spend and show top vendors."""
    from vendor_analysis.cli.analyze import analyze_command

    analyze_command(top=top)


@app.command()
def duplicates(
    threshold: float = typer.Option(
        0.85, "--threshold", "-t", help="Similarity threshold (0.0-1.0)"
    ),
) -> None:
    """Find potential duplicate vendors."""
    from vendor_analysis.cli.duplicates import duplicates_command

    duplicates_command(threshold=threshold)


@app.command()
def status() -> None:
    """Show database status, sync metadata, and recent records."""
    from vendor_analysis.cli.status import status_command

    status_command()


@app.callback()
def callback() -> None:
    """Vendor analysis CLI - read-only NetSuite operations."""
    pass


def main() -> None:
    """Main entry point with top-level error handling."""
    logger = get_logger()
    try:
        logger.info("Application started")
        app()
        logger.info("Application completed successfully")
    except VendorAnalysisError as e:
        logger.error(f"Application error: {e}")
        console.print(f"[red]ERROR: {e}[/red]")
        raise typer.Exit(code=1) from e
    except KeyboardInterrupt as e:
        logger.warning("Application interrupted by user")
        console.print("\n[yellow]Interrupted by user[/yellow]")
        raise typer.Exit(code=130) from e
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        console.print(f"[red]UNEXPECTED ERROR: {e}[/red]")
        raise  # Re-raise for full traceback


if __name__ == "__main__":
    main()
