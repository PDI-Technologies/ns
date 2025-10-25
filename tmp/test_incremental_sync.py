"""
Test script to validate incremental sync functionality.

Queries the sync_metadata table to verify sync state tracking.
"""

import sys
from datetime import datetime

from rich.console import Console
from rich.table import Table

# Add src to path
sys.path.insert(0, "/opt/ns/apps/vendor-analysis/src")

from vendor_analysis.core.config import get_settings
from vendor_analysis.db.models import SyncMetadata
from vendor_analysis.db.session import get_session

console = Console()


def test_sync_metadata() -> None:
    """Check sync metadata state."""
    console.print("[cyan]Checking sync metadata state...[/cyan]\n")

    settings = get_settings()
    session = get_session(settings)

    # Query all sync metadata
    all_metadata = session.query(SyncMetadata).all()

    if not all_metadata:
        console.print("[yellow]No sync metadata found - database never synced[/yellow]")
        console.print("[cyan]Run your first sync with: vendor-analysis sync --limit 5[/cyan]")
        return

    # Create table
    table = Table(title="Sync Metadata Status")
    table.add_column("Record Type", style="cyan")
    table.add_column("Last Sync", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Records Synced", style="blue")
    table.add_column("Full Sync?", style="magenta")
    table.add_column("Age (mins)", style="white")

    for meta in all_metadata:
        age_minutes = int((datetime.now() - meta.last_sync_timestamp).total_seconds() / 60)
        table.add_row(
            meta.record_type,
            meta.last_sync_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            meta.sync_status,
            str(meta.records_synced),
            "Yes" if meta.is_full_sync else "No (Incremental)",
            str(age_minutes),
        )

    console.print(table)
    console.print()

    # Provide recommendations
    for meta in all_metadata:
        if meta.sync_status == "completed":
            age_minutes = int((datetime.now() - meta.last_sync_timestamp).total_seconds() / 60)
            console.print(
                f"[green]✓[/green] {meta.record_type}: "
                f"Ready for incremental sync (last synced {age_minutes} minutes ago)"
            )
        else:
            console.print(f"[red]✗[/red] {meta.record_type}: Status is {meta.sync_status}")

    session.close()


def test_record_counts() -> None:
    """Check actual record counts in database."""
    console.print("\n[cyan]Checking database record counts...[/cyan]\n")

    from vendor_analysis.db.models import TransactionRecord, VendorRecord

    settings = get_settings()
    session = get_session(settings)

    vendor_count = session.query(VendorRecord).count()
    transaction_count = session.query(TransactionRecord).count()

    console.print(f"  Vendors:      {vendor_count:,}")
    console.print(f"  Transactions: {transaction_count:,}")

    if vendor_count == 0 and transaction_count == 0:
        console.print("\n[yellow]No records found - run initial sync[/yellow]")
    else:
        console.print("\n[green]Database has data - incremental sync available[/green]")

    session.close()


def show_testing_commands() -> None:
    """Show recommended testing commands."""
    console.print("\n[cyan]Recommended Testing Workflow:[/cyan]\n")

    commands = [
        ("1. Dry run (preview only)", "vendor-analysis sync --dry-run --limit 5"),
        ("2. Test sync (limited records)", "vendor-analysis sync --limit 5"),
        ("3. Check metadata", "python tmp/test_incremental_sync.py"),
        ("4. Test incremental sync", "vendor-analysis sync --limit 5"),
        ("5. Full sync (when needed)", "vendor-analysis sync --full"),
    ]

    for desc, cmd in commands:
        console.print(f"  [yellow]{desc}[/yellow]")
        console.print(f"    [dim]$ {cmd}[/dim]\n")


if __name__ == "__main__":
    console.print("\n[bold]Incremental Sync Test Report[/bold]\n")
    test_sync_metadata()
    test_record_counts()
    show_testing_commands()
    console.print()
