"""Test what fields are available on transaction table via SuiteQL."""

from rich.console import Console
from rich.pretty import pprint

from vendor_analysis.core.config import get_settings, initialize_logger
from vendor_analysis.netsuite.client import NetSuiteClient

initialize_logger()
console = Console()

def test_transaction_fields():
    """Query a single transaction to see available fields."""
    settings = get_settings()

    with NetSuiteClient(settings) as client:
        console.print("[cyan]Fetching single VendBill to see fields...[/cyan]\n")

        # Query without date filter to get one bill
        try:
            response = client.query_suiteql("SELECT * FROM transaction WHERE type = 'VendBill'", limit=1)
            if response.get("items"):
                bill = response["items"][0]
                console.print(f"[green]Fields available ({len(bill)}):[/green]\n")
                
                # Show date-related fields
                date_fields = [k for k in sorted(bill.keys()) if 'date' in k.lower() or 'created' in k.lower() or 'modified' in k.lower()]
                console.print("[yellow]Date/time fields:[/yellow]")
                for field in date_fields:
                    console.print(f"  {field}: {bill[field]}")
                
                console.print("\n[yellow]All fields:[/yellow]")
                for field in sorted(bill.keys())[:30]:
                    console.print(f"  {field}")
                console.print(f"  ... and {len(bill) - 30} more")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    test_transaction_fields()
