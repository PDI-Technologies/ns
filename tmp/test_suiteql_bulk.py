"""Test SuiteQL bulk query performance vs Record API N+1 pattern."""

from time import time
from rich.console import Console

from vendor_analysis.core.config import get_settings, initialize_logger
from vendor_analysis.netsuite.client import NetSuiteClient

initialize_logger()
console = Console()

def test_bulk_query():
    """Compare SuiteQL bulk vs Record API N+1."""
    settings = get_settings()

    with NetSuiteClient(settings) as client:
        console.print("[cyan]Testing bulk query performance...[/cyan]\n")

        # Test 1: SuiteQL - fetch 10 vendors in ONE query
        console.print("[yellow]Test 1: SuiteQL (1 API call for 10 vendors)[/yellow]")
        start = time()
        try:
            suiteql_response = client.query_suiteql("SELECT * FROM vendor", limit=10)
            elapsed_suiteql = time() - start

            vendors_suiteql = suiteql_response.get("items", [])
            console.print(f"[green]SuiteQL: Fetched {len(vendors_suiteql)} vendors in {elapsed_suiteql:.2f}s[/green]")
            console.print(f"[blue]API calls: 1[/blue]")
            console.print(f"[blue]Fields per vendor: {len(vendors_suiteql[0]) if vendors_suiteql else 0}[/blue]\n")

        except Exception as e:
            console.print(f"[red]SuiteQL failed: {e}[/red]\n")
            return

        # Test 2: Record API N+1 - fetch same 10 vendors
        console.print("[yellow]Test 2: Record API N+1 (11 API calls for 10 vendors)[/yellow]")
        start = time()

        # Step 1: Query for IDs
        query_response = client.query_records("vendor", limit=10)
        vendor_ids = [item["id"] for item in query_response.get("items", [])]

        # Step 2: Fetch each vendor individually
        vendors_record_api = []
        for vendor_id in vendor_ids:
            vendor = client.get_record("vendor", vendor_id)
            vendors_record_api.append(vendor)

        elapsed_record_api = time() - start
        console.print(f"[green]Record API: Fetched {len(vendors_record_api)} vendors in {elapsed_record_api:.2f}s[/green]")
        console.print(f"[blue]API calls: {len(vendor_ids) + 1}[/blue]")
        console.print(f"[blue]Fields per vendor: {len(vendors_record_api[0]) if vendors_record_api else 0}[/blue]\n")

        # Comparison
        speedup = elapsed_record_api / elapsed_suiteql if elapsed_suiteql > 0 else 0
        console.print(f"[cyan]Performance:[/cyan]")
        console.print(f"  SuiteQL: {elapsed_suiteql:.2f}s (1 API call)")
        console.print(f"  Record API: {elapsed_record_api:.2f}s ({len(vendor_ids) + 1} API calls)")
        console.print(f"  Speedup: {speedup:.1f}x faster with SuiteQL\n")

        # Extrapolate for large datasets
        console.print(f"[cyan]Projected time for 9000 vendors:[/cyan]")
        console.print(f"  SuiteQL: ~{(elapsed_suiteql / 10 * 9000) / 60:.1f} minutes (assuming pagination)")
        console.print(f"  Record API: ~{(elapsed_record_api / 10 * 9000) / 60:.1f} minutes")

if __name__ == "__main__":
    test_bulk_query()
