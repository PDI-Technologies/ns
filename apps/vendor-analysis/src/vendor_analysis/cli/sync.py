"""Sync command - pull data from NetSuite to local database."""

from rich.console import Console
from rich.progress import Progress

from vendor_analysis.core.config import get_settings
from vendor_analysis.db.models import TransactionRecord, VendorRecord
from vendor_analysis.db.session import get_session
from vendor_analysis.netsuite.client import NetSuiteClient
from vendor_analysis.netsuite.queries import fetch_all_vendors, fetch_vendor_bills

console = Console()


def sync_command(vendors_only: bool = False, transactions_only: bool = False) -> None:
    """
    Sync vendors and transactions from NetSuite.

    Args:
        vendors_only: Only sync vendors
        transactions_only: Only sync transactions
    """
    settings = get_settings()
    session = get_session(settings)

    with NetSuiteClient(settings) as client:
        # Sync vendors
        if not transactions_only:
            console.print("[yellow]Syncing vendors from NetSuite...[/yellow]")
            with Progress() as progress:
                task = progress.add_task("[cyan]Fetching vendors...", total=None)
                vendors = fetch_all_vendors(client, settings)
                progress.update(task, completed=True)

            console.print(f"[blue]Fetched {len(vendors)} vendors[/blue]")

            # Store in database
            with Progress() as progress:
                task = progress.add_task(
                    "[cyan]Storing vendors...", total=len(vendors)
                )
                for vendor in vendors:
                    # Upsert vendor
                    existing = session.query(VendorRecord).filter_by(id=vendor.id).first()
                    if existing:
                        # Update
                        for key, value in vendor.model_dump().items():
                            setattr(existing, key, value)
                    else:
                        # Insert
                        session.add(
                            VendorRecord(**vendor.model_dump())
                        )
                    progress.advance(task)

                session.commit()

            console.print(f"[green]✓ Synced {len(vendors)} vendors[/green]")

        # Sync transactions
        if not vendors_only:
            console.print("[yellow]Syncing vendor bills from NetSuite...[/yellow]")
            with Progress() as progress:
                task = progress.add_task("[cyan]Fetching bills...", total=None)
                bills = fetch_vendor_bills(client, settings)
                progress.update(task, completed=True)

            console.print(f"[blue]Fetched {len(bills)} bills[/blue]")

            # Store in database
            with Progress() as progress:
                task = progress.add_task("[cyan]Storing bills...", total=len(bills))
                for bill in bills:
                    existing = session.query(TransactionRecord).filter_by(id=bill.id).first()
                    if existing:
                        for key, value in bill.model_dump().items():
                            setattr(existing, key, value)
                    else:
                        session.add(TransactionRecord(**bill.model_dump()))
                    progress.advance(task)

                session.commit()

            console.print(f"[green]✓ Synced {len(bills)} bills[/green]")

    session.close()
    console.print("[green]✓ Sync complete[/green]")
