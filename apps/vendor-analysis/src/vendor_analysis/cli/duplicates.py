"""Duplicates command - find potential duplicate vendors."""

from rich.console import Console
from rich.table import Table

from vendor_analysis.analysis.duplicates import detect_duplicate_vendors
from vendor_analysis.core.config import get_logger, get_settings
from vendor_analysis.db.session import get_session

console = Console()


def duplicates_command(threshold: float = 0.85) -> None:
    """
    Find potential duplicate vendors.

    Args:
        threshold: Similarity threshold (0.0-1.0)
    """
    logger = get_logger()
    logger.info(f"Command: duplicates (threshold={threshold})")

    settings = get_settings()
    session = get_session(settings)

    console.print(f"[yellow]Detecting duplicate vendors (threshold: {threshold})...[/yellow]")

    duplicates = detect_duplicate_vendors(session, settings, threshold=threshold)

    if not duplicates:
        logger.info("No potential duplicates found")
        console.print("[green]No potential duplicates found![/green]")
        session.close()
        return

    # Create table
    table = Table(title=f"Potential Duplicate Vendors (threshold: {threshold})")
    table.add_column("Similarity", justify="right", style="cyan")
    table.add_column("Vendor 1", style="magenta")
    table.add_column("Vendor 2", style="yellow")

    for dup in duplicates:
        table.add_row(
            f"{dup.similarity_score:.2%}",
            f"{dup.vendor_1_name} (ID: {dup.vendor_1_id})",
            f"{dup.vendor_2_name} (ID: {dup.vendor_2_id})",
        )

    console.print(table)
    console.print(f"\n[blue]Found {len(duplicates)} potential duplicate pairs[/blue]")

    logger.info(f"Duplicates detection complete: found {len(duplicates)} potential duplicate pairs")
    session.close()
