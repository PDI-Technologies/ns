"""Test why one custom field is missing in SuiteQL."""

from rich.console import Console
from rich.pretty import pprint

from vendor_analysis.core.config import get_settings, initialize_logger
from vendor_analysis.netsuite.client import NetSuiteClient

initialize_logger()
console = Console()

def test_missing_field():
    """Check what field is missing and why."""
    settings = get_settings()

    with NetSuiteClient(settings) as client:
        vendor_id = "-3"

        # Get via Record API
        console.print("[cyan]Fetching via Record API...[/cyan]")
        record_api = client.get_record("vendor", vendor_id)

        # Get via SuiteQL
        console.print("[cyan]Fetching via SuiteQL...[/cyan]")
        suiteql_response = client.query_suiteql(f"SELECT * FROM vendor WHERE id = '{vendor_id}'", limit=1)
        suiteql = suiteql_response["items"][0] if suiteql_response.get("items") else {}

        # Find differences
        record_api_fields = set(record_api.keys())
        suiteql_fields = set(suiteql.keys())

        missing_in_suiteql = record_api_fields - suiteql_fields
        missing_in_record = suiteql_fields - record_api_fields

        console.print(f"\n[yellow]Fields in Record API but NOT in SuiteQL ({len(missing_in_suiteql)}):[/yellow]")
        for field in sorted(missing_in_suiteql):
            value = record_api.get(field)
            console.print(f"  - {field}: {type(value).__name__} = {str(value)[:100]}")

        console.print(f"\n[yellow]Fields in SuiteQL but NOT in Record API ({len(missing_in_record)}):[/yellow]")
        for field in sorted(missing_in_record):
            value = suiteql.get(field)
            console.print(f"  - {field}: {type(value).__name__} = {str(value)[:100]}")

if __name__ == "__main__":
    test_missing_field()
