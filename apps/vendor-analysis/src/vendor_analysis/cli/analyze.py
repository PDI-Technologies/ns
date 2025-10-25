"""Analyze command - vendor spend analysis and reporting."""

from rich.console import Console
from rich.table import Table

from vendor_analysis.analysis.vendors import get_top_vendors
from vendor_analysis.core.config import get_logger, get_settings
from vendor_analysis.db.session import get_session

console = Console()


def analyze_command(top: int = 10) -> None:
    """
    Analyze vendor spend and display top vendors.

    Args:
        top: Number of top vendors to display
    """
    logger = get_logger()
    logger.info(f"Command: analyze (top={top})")

    settings = get_settings()
    session = get_session(settings)

    console.print(f"[yellow]Analyzing top {top} vendors by spend...[/yellow]")

    summaries = get_top_vendors(session, settings, top_n=top)

    if not summaries:
        logger.warning("No vendor data found in database")
        console.print("[red]No vendor data found. Run 'sync' first.[/red]")
        return

    # Create table
    table = Table(title=f"Top {top} Vendors by Spend")
    table.add_column("Rank", justify="right", style="cyan")
    table.add_column("Vendor", style="magenta")
    table.add_column("Total Spend", justify="right", style="green")
    table.add_column("Transactions", justify="right", style="blue")
    table.add_column("Avg Transaction", justify="right", style="yellow")
    table.add_column("Currency", justify="center")

    for rank, summary in enumerate(summaries, start=1):
        table.add_row(
            str(rank),
            summary.vendor_name,
            f"${summary.total_spend:,.2f}",
            str(summary.transaction_count),
            f"${summary.average_transaction:,.2f}",
            summary.currency or "N/A",
        )

    console.print(table)

    # Summary stats
    total_spend = sum(s.total_spend for s in summaries)
    total_transactions = sum(s.transaction_count for s in summaries)

    console.print(f"\n[green]Total Spend (Top {top}): ${total_spend:,.2f}[/green]")
    console.print(f"[blue]Total Transactions: {total_transactions}[/blue]")

    logger.info(
        f"Analysis complete: {len(summaries)} vendors, "
        f"${total_spend:,.2f} total spend, {total_transactions} transactions"
    )
    session.close()
