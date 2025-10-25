"""
Financial Analytics CLI application.

Following python-cli-engineering patterns with Typer and Rich.
Fail-fast discipline: Only catch exceptions at top level.
"""

import typer
from rich.console import Console

from financial_analytics.cli.analyze import (
    analyze_command,
    pipeline_command,
    revenue_command,
    vendors_command,
)
from financial_analytics.cli.init import init_command
from financial_analytics.cli.sync import sync_command
from financial_analytics.core.config import initialize_logger
from financial_analytics.core.exceptions import FinancialAnalyticsError

app = typer.Typer(
    name="fin-analytics",
    help="Comprehensive financial analytics and reporting from NetSuite and Salesforce",
    add_completion=False,
)
console = Console()


# Register commands
app.command(name="init")(init_command)
app.command(name="sync")(sync_command)
app.command(name="analyze")(analyze_command)
app.command(name="vendors")(vendors_command)
app.command(name="revenue")(revenue_command)
app.command(name="pipeline")(pipeline_command)


def main() -> None:
    """
    Main entry point with top-level error handling.

    Only exceptions are caught here for user-friendly messages.
    All other code follows fail-fast discipline.
    """
    logger = None
    try:
        # Initialize logger first
        logger = initialize_logger()
        logger.info("Application started")

        app()

        logger.info("Application completed successfully")
    except FinancialAnalyticsError as e:
        if logger:
            logger.error(f"Application error: {e}")
        console.print(f"[red]ERROR: {e}[/red]")
        raise typer.Exit(code=1) from e
    except KeyboardInterrupt as e:
        if logger:
            logger.warning("Application interrupted by user")
        console.print("\n[yellow]Interrupted[/yellow]")
        raise typer.Exit(code=130) from e
    except Exception as e:
        if logger:
            logger.error(f"Unexpected error: {e}", exc_info=True)
        console.print(f"[red]UNEXPECTED ERROR: {e}[/red]")
        raise


if __name__ == "__main__":
    main()
