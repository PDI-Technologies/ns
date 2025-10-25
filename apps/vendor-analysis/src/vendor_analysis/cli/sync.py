"""
Sync command - pull data from NetSuite to local database.

Implements resilient schema handling:
- Fetches complete vendor/bill data from NetSuite
- Splits known fields (typed columns) from custom fields (JSONB)
- Merges custom fields to preserve historical data
- Stores complete raw data for auditing
"""

from datetime import datetime

from rich.console import Console
from rich.progress import Progress

from vendor_analysis.core.config import get_logger, get_settings
from vendor_analysis.db.models import SyncMetadata, TransactionRecord, VendorRecord
from vendor_analysis.db.session import get_session
from vendor_analysis.netsuite.client import NetSuiteClient
from vendor_analysis.netsuite.field_processor import (
    merge_custom_fields,
    process_vendor_bill_fields,
    process_vendor_fields,
)
from vendor_analysis.netsuite.queries import (
    fetch_all_vendors_suiteql,
    fetch_vendor_bills_suiteql,
)

console = Console()


def sync_command(
    vendors_only: bool = False,
    transactions_only: bool = False,
    full: bool = False,
    limit: int | None = None,
    dry_run: bool = False,
) -> None:
    """
    Sync vendors and transactions from NetSuite with schema-resilient processing.

    By default, performs incremental sync (only changed/new records).
    Use --full flag to force complete re-sync of all records.

    Fetches complete data from NetSuite, splits into known/custom fields,
    preserves historical custom fields, and stores everything.

    Args:
        vendors_only: Only sync vendors
        transactions_only: Only sync transactions
        full: Force full sync instead of incremental (default: False)
        limit: Limit number of records to sync (for testing)
        dry_run: Preview what would be synced without storing to database
    """
    logger = get_logger()
    logger.info(
        f"Command: sync (vendors_only={vendors_only}, transactions_only={transactions_only}, "
        f"full={full}, limit={limit}, dry_run={dry_run})"
    )

    settings = get_settings()
    session = get_session(settings)
    sync_timestamp = datetime.now()
    schema_version = int(sync_timestamp.timestamp())  # Use timestamp as version

    # Determine high-water marks from database (not sync metadata)
    vendor_max_created = None
    bill_max_created = None

    if not full:
        # Query database for highest created_date (high-water mark)
        if not transactions_only:
            from sqlalchemy import func
            max_date = session.query(func.max(VendorRecord.created_date)).scalar()
            if max_date:
                vendor_max_created = max_date.strftime("%Y-%m-%d")
                logger.info(f"Resuming vendor sync from created_date >= {vendor_max_created}")
                console.print(f"[cyan]Resuming from created_date >= {vendor_max_created}[/cyan]")
            else:
                logger.info("No vendors in database - full sync")
                console.print("[yellow]No vendors in database - full sync[/yellow]")

        if not vendors_only:
            from sqlalchemy import func
            max_date = session.query(func.max(TransactionRecord.created_date)).scalar()
            if max_date:
                bill_max_created = max_date.strftime("%Y-%m-%d")
                logger.info(f"Resuming bill sync from created_date >= {bill_max_created}")
                console.print(f"[cyan]Resuming from created_date >= {bill_max_created}[/cyan]")
            else:
                logger.info("No bills in database - full sync")
                console.print("[yellow]No bills in database - full sync[/yellow]")
    else:
        logger.info("Full sync requested - fetching all records")
        console.print("[yellow]Full sync requested - fetching all records[/yellow]")

    if limit:
        console.print(f"[cyan]Testing mode: limiting to {limit} records[/cyan]")

    if dry_run:
        console.print("[yellow]DRY RUN - No data will be stored to database[/yellow]")

    with NetSuiteClient(settings) as client:
        # Sync vendors
        if not transactions_only:
            console.print("[yellow]Syncing vendors from NetSuite...[/yellow]")

            # Create progress tracking with page-level visibility
            vendor_data_list = []
            with Progress() as progress:
                fetch_task = progress.add_task("[cyan]Fetching vendors...", total=None)

                def vendor_progress(phase: str, current: int, total: int, pages: int) -> None:
                    if phase == "fetch_records":
                        # Show determinate progress with page info
                        current_page = (current // settings.batch_size) if current > 0 else 1
                        progress.update(
                            fetch_task,
                            total=total,
                            completed=current,
                            description=f"[cyan]Fetching vendors... Page {current_page}/{pages} ({current}/{total} records)"
                        )

                # Use SuiteQL for efficient batch fetching (250x faster than N+1)
                vendor_data_list = fetch_all_vendors_suiteql(
                    client, settings, vendor_max_created, limit, vendor_progress
                )

            logger.info(f"Fetched {len(vendor_data_list)} vendors from NetSuite")
            console.print(f"[blue]Fetched {len(vendor_data_list)} vendors[/blue]")

            if dry_run:
                # Show sample data without storing
                console.print("[yellow]DRY RUN - Vendor data preview:[/yellow]")
                for i, vendor_data in enumerate(vendor_data_list[:5], 1):
                    console.print(
                        f"  {i}. ID: {vendor_data.get('id')}, "
                        f"Name: {vendor_data.get('companyName') or vendor_data.get('entityId')}, "
                        f"Modified: {vendor_data.get('lastModifiedDate')}"
                    )
                if len(vendor_data_list) > 5:
                    console.print(f"  ... and {len(vendor_data_list) - 5} more")
                console.print("[yellow]DRY RUN - Skipping database storage[/yellow]")
            else:
                # Process and store in database
                with Progress() as progress:
                    task = progress.add_task(
                        "[cyan]Processing and storing vendors...", total=len(vendor_data_list)
                    )
                    for raw_vendor in vendor_data_list:
                        # Split known vs custom fields
                        known_fields, custom_fields = process_vendor_fields(raw_vendor)

                        # Check if vendor exists
                        existing = session.query(VendorRecord).filter_by(id=known_fields["id"]).first()

                        if existing:
                            # Update known fields
                            for key, value in known_fields.items():
                                if key != "id":  # Don't update primary key
                                    setattr(existing, key, value)

                            # Merge custom fields (preserves historical data)
                            existing.custom_fields = merge_custom_fields(
                                existing.custom_fields, custom_fields, sync_timestamp
                            )

                            # Update raw data and metadata
                            existing.raw_data = raw_vendor
                            existing.synced_at = sync_timestamp
                            existing.schema_version = schema_version
                        else:
                            # New vendor - create with metadata-enhanced custom fields
                            enhanced_custom = merge_custom_fields(None, custom_fields, sync_timestamp)

                            new_vendor = VendorRecord(
                                **known_fields,
                                custom_fields=enhanced_custom,
                                raw_data=raw_vendor,
                                synced_at=sync_timestamp,
                                schema_version=schema_version,
                            )
                            session.add(new_vendor)

                        progress.advance(task)

                    session.commit()

                logger.info(f"Successfully synced {len(vendor_data_list)} vendors to database")
                console.print(f"[green]OK - Synced {len(vendor_data_list)} vendors[/green]")

                # Update sync metadata ONLY if we actually synced records
                # Don't save metadata when 0 records fetched (prevents locking out historical data)
                if len(vendor_data_list) > 0:
                    vendor_meta = session.query(SyncMetadata).filter_by(record_type="vendor").first()
                    if vendor_meta:
                        vendor_meta.last_sync_timestamp = sync_timestamp
                        vendor_meta.sync_status = "completed"
                        vendor_meta.records_synced = len(vendor_data_list)
                        vendor_meta.is_full_sync = full or vendor_max_created is None
                        vendor_meta.updated_at = sync_timestamp
                    else:
                        vendor_meta = SyncMetadata(
                            record_type="vendor",
                            last_sync_timestamp=sync_timestamp,
                            sync_status="completed",
                            records_synced=len(vendor_data_list),
                            is_full_sync=full or vendor_max_created is None,
                        )
                        session.add(vendor_meta)
                    session.commit()
                    logger.info(f"Sync metadata updated for vendors")
                else:
                    logger.info("No vendors synced - metadata not updated (will retry full sync next time)")

        # Sync transactions
        if not vendors_only:
            console.print("[yellow]Syncing vendor bills from NetSuite...[/yellow]")

            # Create progress tracking with page-level visibility
            bill_data_list = []
            with Progress() as progress:
                fetch_task = progress.add_task("[cyan]Fetching bills...", total=None)

                def bill_progress(phase: str, current: int, total: int, pages: int) -> None:
                    if phase == "fetch_records":
                        # Show determinate progress with page info
                        current_page = (current // settings.batch_size) if current > 0 else 1
                        progress.update(
                            fetch_task,
                            total=total,
                            completed=current,
                            description=f"[cyan]Fetching bills... Page {current_page}/{pages} ({current}/{total} records)"
                        )

                # Use SuiteQL for efficient batch fetching
                bill_data_list = fetch_vendor_bills_suiteql(
                    client, settings, None, bill_max_created, limit, bill_progress
                )

            logger.info(f"Fetched {len(bill_data_list)} vendor bills from NetSuite")
            console.print(f"[blue]Fetched {len(bill_data_list)} bills[/blue]")

            if dry_run:
                # Show sample data without storing
                console.print("[yellow]DRY RUN - Bill data preview:[/yellow]")
                for i, bill_data in enumerate(bill_data_list[:5], 1):
                    console.print(
                        f"  {i}. ID: {bill_data.get('id')}, "
                        f"TranID: {bill_data.get('tranId')}, "
                        f"Amount: {bill_data.get('userTotal')}, "
                        f"Modified: {bill_data.get('lastModifiedDate')}"
                    )
                if len(bill_data_list) > 5:
                    console.print(f"  ... and {len(bill_data_list) - 5} more")
                console.print("[yellow]DRY RUN - Skipping database storage[/yellow]")
            else:
                # Process and store in database
                with Progress() as progress:
                    task = progress.add_task(
                        "[cyan]Processing and storing bills...", total=len(bill_data_list)
                    )
                    for raw_bill in bill_data_list:
                        # Split known vs custom fields
                        known_fields, custom_fields = process_vendor_bill_fields(raw_bill)

                        # Check if bill exists
                        existing = session.query(TransactionRecord).filter_by(id=known_fields["id"]).first()

                        if existing:
                            # Update known fields
                            for key, value in known_fields.items():
                                if key != "id":
                                    setattr(existing, key, value)

                            # Merge custom fields
                            existing.custom_fields = merge_custom_fields(
                                existing.custom_fields, custom_fields, sync_timestamp
                            )

                            # Update raw data and metadata
                            existing.raw_data = raw_bill
                            existing.synced_at = sync_timestamp
                            existing.schema_version = schema_version
                        else:
                            # New bill
                            enhanced_custom = merge_custom_fields(None, custom_fields, sync_timestamp)

                            new_bill = TransactionRecord(
                                **known_fields,
                                custom_fields=enhanced_custom,
                                raw_data=raw_bill,
                                synced_at=sync_timestamp,
                                schema_version=schema_version,
                            )
                            session.add(new_bill)

                        progress.advance(task)

                    session.commit()

                logger.info(f"Successfully synced {len(bill_data_list)} vendor bills to database")
                console.print(f"[green]OK - Synced {len(bill_data_list)} bills[/green]")

                # Update sync metadata ONLY if we actually synced records
                # Don't save metadata when 0 records fetched (prevents locking out historical data)
                if len(bill_data_list) > 0:
                    bill_meta = session.query(SyncMetadata).filter_by(record_type="vendorbill").first()
                    if bill_meta:
                        bill_meta.last_sync_timestamp = sync_timestamp
                        bill_meta.sync_status = "completed"
                        bill_meta.records_synced = len(bill_data_list)
                        bill_meta.is_full_sync = full or bill_max_created is None
                        bill_meta.updated_at = sync_timestamp
                    else:
                        bill_meta = SyncMetadata(
                            record_type="vendorbill",
                            last_sync_timestamp=sync_timestamp,
                            sync_status="completed",
                            records_synced=len(bill_data_list),
                            is_full_sync=full or bill_max_created is None,
                        )
                        session.add(bill_meta)
                    session.commit()
                    logger.info(f"Sync metadata updated for bills")
                else:
                    logger.info("No bills synced - metadata not updated (will retry full sync next time)")

    session.close()
    logger.info("Sync operation completed successfully")
    console.print("[green]OK - Sync complete[/green]")
