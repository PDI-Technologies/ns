"""Test SuiteQL pagination and total count."""

from rich.console import Console

from vendor_analysis.core.config import get_settings, initialize_logger
from vendor_analysis.netsuite.client import NetSuiteClient

initialize_logger()
console = Console()

def test_pagination():
    """Test if SuiteQL returns total count for progress bars."""
    settings = get_settings()

    with NetSuiteClient(settings) as client:
        console.print("[cyan]Testing SuiteQL pagination metadata...[/cyan]\n")

        # Query with limit 5 to see response structure
        response = client.query_suiteql("SELECT * FROM vendor", limit=5, offset=0)

        console.print("[yellow]Response structure:[/yellow]")
        console.print(f"  items: {len(response.get('items', []))} records")
        console.print(f"  count: {response.get('count')}")
        console.print(f"  hasMore: {response.get('hasMore')}")
        console.print(f"  totalResults: {response.get('totalResults')}")
        console.print(f"  offset: {response.get('offset')}")

        if response.get('totalResults'):
            total = response['totalResults']
            page_size = 250
            total_pages = (total + page_size - 1) // page_size

            console.print(f"\n[green]Total vendors: {total}[/green]")
            console.print(f"[green]With page_size={page_size}: {total_pages} API calls needed[/green]")
            console.print(f"[blue]We CAN show determinate progress bar![/blue]")
        else:
            console.print(f"\n[red]No totalResults in response - cannot show determinate progress[/red]")

if __name__ == "__main__":
    test_pagination()
