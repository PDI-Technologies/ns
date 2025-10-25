"""
Test script to validate SuiteQL returns same data as Record API.

Compares:
1. Record API: get_record() - returns all fields including custom
2. SuiteQL: SELECT * FROM vendor - does it return all fields?
"""

from rich.console import Console
from rich.table import Table

from vendor_analysis.core.config import get_settings, initialize_logger
from vendor_analysis.netsuite.client import NetSuiteClient

# Initialize logger
initialize_logger()

console = Console()


def test_suiteql_vs_record_api() -> None:
    """Compare SuiteQL vs Record API for same vendor."""
    console.print("[cyan]Testing SuiteQL vs Record API...[/cyan]\n")

    settings = get_settings()

    with NetSuiteClient(settings) as client:
        # Step 1: Get a vendor ID using current method
        console.print("[yellow]Step 1: Getting vendor ID via Record API query...[/yellow]")
        query_response = client.query_records("vendor", limit=1)
        if not query_response.get("items"):
            console.print("[red]No vendors found[/red]")
            return

        vendor_id = query_response["items"][0]["id"]
        console.print(f"[green]Found vendor ID: {vendor_id}[/green]\n")

        # Step 2: Fetch via Record API get_record (current method)
        console.print("[yellow]Step 2: Fetching via Record API get_record...[/yellow]")
        record_api_data = client.get_record("vendor", vendor_id)
        console.print(f"[green]Record API returned {len(record_api_data)} fields[/green]")

        # Count custom fields
        custom_fields_record_api = [k for k in record_api_data.keys() if k.startswith("custentity")]
        console.print(f"[blue]Custom fields (custentity_*): {len(custom_fields_record_api)}[/blue]\n")

        # Step 3: Fetch via SuiteQL
        console.print("[yellow]Step 3: Fetching via SuiteQL...[/yellow]")
        try:
            suiteql_query = f"SELECT * FROM vendor WHERE id = '{vendor_id}'"
            suiteql_response = client.query_suiteql(suiteql_query, limit=1)

            if suiteql_response.get("items"):
                suiteql_data = suiteql_response["items"][0]
                console.print(f"[green]SuiteQL returned {len(suiteql_data)} fields[/green]")

                # Count custom fields
                custom_fields_suiteql = [k for k in suiteql_data.keys() if k.startswith("custentity")]
                console.print(f"[blue]Custom fields (custentity_*): {len(custom_fields_suiteql)}[/blue]\n")

                # Step 4: Compare
                console.print("[yellow]Step 4: Comparison...[/yellow]\n")

                table = Table(title="Field Count Comparison")
                table.add_column("Metric", style="cyan")
                table.add_column("Record API", style="green")
                table.add_column("SuiteQL", style="blue")

                table.add_row("Total Fields", str(len(record_api_data)), str(len(suiteql_data)))
                table.add_row("Custom Fields", str(len(custom_fields_record_api)), str(len(custom_fields_suiteql)))

                console.print(table)
                console.print()

                # Show sample of fields in each
                console.print("[cyan]Sample Record API fields:[/cyan]")
                for k in list(record_api_data.keys())[:10]:
                    console.print(f"  - {k}")

                console.print("\n[cyan]Sample SuiteQL fields:[/cyan]")
                for k in list(suiteql_data.keys())[:10]:
                    console.print(f"  - {k}")

                # Check for missing custom fields
                missing_in_suiteql = set(custom_fields_record_api) - set(custom_fields_suiteql)
                missing_in_record_api = set(custom_fields_suiteql) - set(custom_fields_record_api)

                if missing_in_suiteql:
                    console.print(f"\n[red]WARNING: {len(missing_in_suiteql)} custom fields missing in SuiteQL:[/red]")
                    for field in list(missing_in_suiteql)[:5]:
                        console.print(f"  - {field}")
                else:
                    console.print("\n[green]All custom fields present in SuiteQL[/green]")

                if missing_in_record_api:
                    console.print(f"\n[yellow]Note: {len(missing_in_record_api)} fields only in SuiteQL[/yellow]")

            else:
                console.print("[red]SuiteQL returned no items[/red]")

        except Exception as e:
            console.print(f"[red]SuiteQL query failed: {e}[/red]")
            console.print("\n[yellow]This means we CANNOT use SuiteQL - must stick with Record API[/yellow]")


if __name__ == "__main__":
    test_suiteql_vs_record_api()
