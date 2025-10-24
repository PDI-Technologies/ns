"""
Main CLI entry point for vendor-analysis application.

All commands are read-only operations. Fail-fast on errors.
"""

import typer
from rich.console import Console

from vendor_analysis.core.config import get_settings
from vendor_analysis.core.exceptions import VendorAnalysisError

app = typer.Typer(
    name="vendor-analysis",
    help="Read-only NetSuite vendor cost analysis and management CLI",
    add_completion=False,
)

console = Console()


@app.command()
def init_db() -> None:
    """Initialize database schema (creates tables)."""
    from vendor_analysis.db.session import init_database

    console.print("[yellow]Initializing database...[/yellow]")
    settings = get_settings()
    init_database(settings)
    console.print("[green]✓ Database initialized successfully[/green]")


@app.command()
def sync(
    vendors_only: bool = typer.Option(False, "--vendors-only", help="Sync only vendors"),
    transactions_only: bool = typer.Option(
        False, "--transactions-only", help="Sync only transactions"
    ),
) -> None:
    """Sync vendors and transactions from NetSuite to local database."""
    from vendor_analysis.cli.sync import sync_command

    sync_command(vendors_only=vendors_only, transactions_only=transactions_only)


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


@app.callback()
def callback() -> None:
    """Vendor analysis CLI - read-only NetSuite operations."""
    pass


def main() -> None:
    """Main entry point with top-level error handling."""
    try:
        app()
    except VendorAnalysisError as e:
        console.print(f"[red]ERROR: {e}[/red]")
        raise typer.Exit(code=1) from e
    except KeyboardInterrupt as e:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        raise typer.Exit(code=130) from e
    except Exception as e:
        console.print(f"[red]UNEXPECTED ERROR: {e}[/red]")
        raise  # Re-raise for full traceback


if __name__ == "__main__":
    main()
