"""
Data synchronization command.

Syncs data from NetSuite to local database.
"""

from datetime import UTC, datetime

import typer
from rich.console import Console
from rich.progress import Progress

from financial_analytics.core.config import Settings
from financial_analytics.db.models import (
    DimCustomer,
    DimVendor,
    FactInvoice,
    FactVendorBill,
    SalesforceAccount,
    SalesforceOpportunity,
)
from financial_analytics.db.session import get_session
from financial_analytics.extractors.netsuite_client import NetSuiteClient
from financial_analytics.extractors.netsuite_queries import (
    fetch_all_customers,
    fetch_all_vendors,
    fetch_invoices,
    fetch_vendor_bills,
)
from financial_analytics.extractors.salesforce_extractor import (
    fetch_accounts,
    fetch_opportunities,
)

console = Console()


def sync_command(
    vendors_only: bool = typer.Option(False, "--vendors-only", help="Sync vendors only"),
    customers_only: bool = typer.Option(False, "--customers-only", help="Sync customers only"),
    salesforce_only: bool = typer.Option(False, "--salesforce-only", help="Sync Salesforce only"),
    full: bool = typer.Option(False, "--full", help="Full sync of all data"),
) -> None:
    """
    Sync data from NetSuite and Salesforce to local database.

    By default syncs all data. Use flags to sync specific datasets.
    """
    console.print("[cyan]Starting data synchronization[/cyan]")

    settings = Settings()  # type: ignore[call-arg]  # Reads from .env at runtime
    session = get_session(settings)

    sync_all = not (vendors_only or customers_only or salesforce_only) or full
    sync_netsuite = sync_all or vendors_only or customers_only
    sync_salesforce = (sync_all or salesforce_only) and settings.sf_enabled

    # Sync NetSuite data
    if sync_netsuite:
        console.print("\n[cyan]NetSuite Synchronization[/cyan]")

    with NetSuiteClient(settings) as client:
        # Sync vendors
        if sync_netsuite and (sync_all or vendors_only):
            console.print("\n[yellow]Syncing vendors...[/yellow]")
            with Progress() as progress:
                task = progress.add_task("Fetching vendors", total=None)
                vendors = fetch_all_vendors(client, settings)
                progress.update(task, completed=True)

            console.print(f"Fetched {len(vendors)} vendors")

            # Upsert to database
            for vendor in vendors:
                db_vendor = DimVendor(
                    id=vendor.id,
                    company_name=vendor.companyName,
                    email=vendor.email,
                    balance=vendor.balance,
                    terms=vendor.terms,
                    category=vendor.category,
                    currency=vendor.currency,
                    synced_at=datetime.now(UTC),
                )
                session.merge(db_vendor)

            session.commit()
            console.print("[green]Vendors synced successfully[/green]")

            # Sync vendor bills
            console.print("\n[yellow]Syncing vendor bills...[/yellow]")
            with Progress() as progress:
                task = progress.add_task("Fetching vendor bills", total=None)
                bills = fetch_vendor_bills(client, settings)
                progress.update(task, completed=True)

            console.print(f"Fetched {len(bills)} vendor bills")

            for bill in bills:
                db_bill = FactVendorBill(
                    id=bill.id,
                    tran_id=bill.tranId,
                    vendor_id=bill.entity,
                    amount=bill.amount,
                    tran_date=bill.tranDate,
                    due_date=bill.dueDate,
                    status=bill.status,
                    memo=bill.memo,
                    synced_at=datetime.now(UTC),
                )
                session.merge(db_bill)

            session.commit()
            console.print("[green]Vendor bills synced successfully[/green]")

        # Sync customers
        if sync_netsuite and (sync_all or customers_only):
            console.print("\n[yellow]Syncing customers...[/yellow]")
            with Progress() as progress:
                task = progress.add_task("Fetching customers", total=None)
                customers = fetch_all_customers(client, settings)
                progress.update(task, completed=True)

            console.print(f"Fetched {len(customers)} customers")

            for customer in customers:
                db_customer = DimCustomer(
                    id=customer.id,
                    company_name=customer.companyName,
                    email=customer.email,
                    balance=customer.balance,
                    sales_rep=customer.salesRep,
                    category=customer.category,
                    synced_at=datetime.now(UTC),
                )
                session.merge(db_customer)

            session.commit()
            console.print("[green]Customers synced successfully[/green]")

            # Sync invoices
            console.print("\n[yellow]Syncing invoices...[/yellow]")
            with Progress() as progress:
                task = progress.add_task("Fetching invoices", total=None)
                invoices = fetch_invoices(client, settings)
                progress.update(task, completed=True)

            console.print(f"Fetched {len(invoices)} invoices")

            for invoice in invoices:
                db_invoice = FactInvoice(
                    id=invoice.id,
                    tran_id=invoice.tranId,
                    customer_id=invoice.entity,
                    amount=invoice.amount,
                    tran_date=invoice.tranDate,
                    due_date=invoice.dueDate,
                    status=invoice.status,
                    synced_at=datetime.now(UTC),
                )
                session.merge(db_invoice)

            session.commit()
            console.print("[green]Invoices synced successfully[/green]")

    # Sync Salesforce data
    if sync_salesforce:
        console.print("\n[cyan]Salesforce Synchronization[/cyan]")

        console.print("\n[yellow]Syncing opportunities...[/yellow]")
        with Progress() as progress:
            task = progress.add_task("Fetching opportunities", total=None)
            opportunities = fetch_opportunities(months_back=settings.analysis_months)
            progress.update(task, completed=True)

        console.print(f"Fetched {len(opportunities)} opportunities")

        for opp in opportunities:
            db_opp = SalesforceOpportunity(
                id=opp.Id,
                name=opp.Name,
                amount=opp.Amount,
                close_date=opp.CloseDate,
                stage_name=opp.StageName,
                probability=opp.Probability,
                opp_type=opp.Type,
                account_id=opp.AccountId,
                account_name=opp.AccountName,
                industry=opp.Industry,
                owner_name=opp.OwnerName,
                is_closed=opp.IsClosed,
                is_won=opp.IsWon,
                synced_at=datetime.now(UTC),
            )
            session.merge(db_opp)

        session.commit()
        console.print("[green]Opportunities synced successfully[/green]")

        console.print("\n[yellow]Syncing accounts...[/yellow]")
        with Progress() as progress:
            task = progress.add_task("Fetching accounts", total=None)
            accounts = fetch_accounts()
            progress.update(task, completed=True)

        console.print(f"Fetched {len(accounts)} accounts")

        for account in accounts:
            db_account = SalesforceAccount(
                id=account.Id,
                name=account.Name,
                account_type=account.Type,
                industry=account.Industry,
                annual_revenue=account.AnnualRevenue,
                employee_count=account.NumberOfEmployees,
                synced_at=datetime.now(UTC),
            )
            session.merge(db_account)

        session.commit()
        console.print("[green]Accounts synced successfully[/green]")

    session.close()
    console.print("\n[green]Synchronization complete[/green]")
