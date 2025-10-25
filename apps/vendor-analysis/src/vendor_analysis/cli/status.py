"""
Status command - show database state and sync metadata.

Displays record counts, last sync times, and recent records.
"""

from datetime import datetime

from rich.console import Console
from rich.table import Table

from vendor_analysis.core.config import get_logger, get_settings
from vendor_analysis.db.models import SyncMetadata, TransactionRecord, VendorRecord
from vendor_analysis.db.session import get_session

console = Console()


def status_command() -> None:
    """
    Show database status, sync metadata, and recent records.

    Displays:
    - Record counts for vendors and transactions
    - Last sync timestamps and status
    - Most recently modified records
    - Database health indicators
    """
    logger = get_logger()
    logger.info("Command: status")

    settings = get_settings()
    session = get_session(settings)

    console.print()
    console.print("[bold cyan]Database Status[/bold cyan]")
    console.print()

    # Record counts
    vendor_count = session.query(VendorRecord).count()
    transaction_count = session.query(TransactionRecord).count()
    vendor_active = session.query(VendorRecord).filter_by(is_inactive=False, is_deleted=False).count()
    transaction_total_amount = (
        session.query(TransactionRecord).filter_by(is_deleted=False).count()
    )

    counts_table = Table(title="Record Counts", show_header=True)
    counts_table.add_column("Type", style="cyan")
    counts_table.add_column("Total", style="green", justify="right")
    counts_table.add_column("Active/Valid", style="blue", justify="right")

    counts_table.add_row(
        "Vendors",
        f"{vendor_count:,}",
        f"{vendor_active:,}",
    )
    counts_table.add_row(
        "Transactions",
        f"{transaction_count:,}",
        f"{transaction_total_amount:,}",
    )

    console.print(counts_table)
    console.print()

    # Sync metadata
    sync_metadata = session.query(SyncMetadata).all()

    if sync_metadata:
        sync_table = Table(title="Sync Status", show_header=True)
        sync_table.add_column("Record Type", style="cyan")
        sync_table.add_column("Last Sync", style="green")
        sync_table.add_column("Status", style="yellow")
        sync_table.add_column("Records", style="blue", justify="right")
        sync_table.add_column("Type", style="magenta")
        sync_table.add_column("Age", style="white")

        for meta in sync_metadata:
            age = datetime.now() - meta.last_sync_timestamp
            age_str = f"{int(age.total_seconds() / 60)}m ago" if age.total_seconds() < 3600 else f"{int(age.total_seconds() / 3600)}h ago"

            sync_table.add_row(
                meta.record_type,
                meta.last_sync_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                meta.sync_status,
                f"{meta.records_synced:,}",
                "Full" if meta.is_full_sync else "Incremental",
                age_str,
            )

        console.print(sync_table)
        console.print()
    else:
        console.print("[yellow]No sync metadata found - database never synced[/yellow]")
        console.print()

    # Most recent vendors
    recent_vendors = (
        session.query(VendorRecord)
        .filter_by(is_deleted=False)
        .order_by(VendorRecord.last_modified_date.desc())
        .limit(5)
        .all()
    )

    if recent_vendors:
        vendors_table = Table(title="Most Recently Modified Vendors (Top 5)", show_header=True)
        vendors_table.add_column("ID", style="cyan")
        vendors_table.add_column("Name", style="green")
        vendors_table.add_column("Balance", style="yellow", justify="right")
        vendors_table.add_column("Modified", style="blue")

        for vendor in recent_vendors:
            vendors_table.add_row(
                vendor.entity_id,
                vendor.company_name or vendor.entity_id,
                f"${vendor.balance:,.2f}" if vendor.balance else "$0.00",
                vendor.last_modified_date.strftime("%Y-%m-%d %H:%M") if vendor.last_modified_date else "Unknown",
            )

        console.print(vendors_table)
        console.print()

    # Most recent transactions
    recent_transactions = (
        session.query(TransactionRecord)
        .filter_by(is_deleted=False)
        .order_by(TransactionRecord.last_modified_date.desc())
        .limit(5)
        .all()
    )

    if recent_transactions:
        transactions_table = Table(title="Most Recently Modified Transactions (Top 5)", show_header=True)
        transactions_table.add_column("Tran ID", style="cyan")
        transactions_table.add_column("Date", style="green")
        transactions_table.add_column("Amount", style="yellow", justify="right")
        transactions_table.add_column("Status", style="blue")
        transactions_table.add_column("Modified", style="magenta")

        for txn in recent_transactions:
            transactions_table.add_row(
                txn.tran_id or txn.id,
                txn.tran_date.strftime("%Y-%m-%d") if txn.tran_date else "Unknown",
                f"${txn.amount:,.2f}" if txn.amount else "$0.00",
                txn.status or "Unknown",
                txn.last_modified_date.strftime("%Y-%m-%d %H:%M") if txn.last_modified_date else "Unknown",
            )

        console.print(transactions_table)
        console.print()

    # Health check
    if vendor_count == 0 and transaction_count == 0:
        console.print("[red]Database is empty - run 'vendor-analysis sync' to download data[/red]")
    elif vendor_count > 0 and transaction_count == 0:
        console.print("[yellow]Vendors synced but no transactions - run 'vendor-analysis sync --transactions-only'[/yellow]")
    else:
        console.print("[green]Database populated and ready for analysis[/green]")

    console.print()
    session.close()
    logger.info("Status command completed")
