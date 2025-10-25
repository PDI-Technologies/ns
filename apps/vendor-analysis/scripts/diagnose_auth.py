#!/usr/bin/env python3
"""
Diagnostic script to test NetSuite authentication.

Attempts authentication and provides detailed error information.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import httpx
from rich.console import Console
from rich.table import Table

from vendor_analysis.core.config import get_settings
from vendor_analysis.netsuite.auth_factory import create_auth_provider

console = Console()


def test_authentication() -> None:
    """Test NetSuite authentication and report detailed diagnostics."""
    console.print("\n[bold cyan]NetSuite Authentication Diagnostics[/bold cyan]\n")

    try:
        # Load configuration
        console.print("[yellow]Loading configuration...[/yellow]")
        settings = get_settings()
        console.print("[green]✓ Configuration loaded successfully[/green]\n")

        # Display credentials (partially masked)
        table = Table(title="Credentials Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Account ID", settings.ns_account_id)
        table.add_row("Auth Method", settings.yaml_config.application.auth_method.upper())
        table.add_row(
            "Consumer Key", f"{settings.ns_client_id[:20]}...{settings.ns_client_id[-10:]}"
        )
        table.add_row(
            "Consumer Secret",
            f"{settings.ns_client_secret[:10]}...{settings.ns_client_secret[-5:]}",
        )
        table.add_row(
            "Token ID", f"{settings.ns_token_id[:20]}...{settings.ns_token_id[-10:]}"
        )
        table.add_row(
            "Token Secret", f"{settings.ns_token_secret[:10]}...{settings.ns_token_secret[-5:]}"
        )

        console.print(table)
        console.print()

        # Create auth provider
        console.print("[yellow]Creating authentication provider...[/yellow]")
        auth = create_auth_provider(settings)
        console.print(f"[green]✓ Using {type(auth).__name__}[/green]\n")

        # Test authentication with a simple API call
        console.print("[yellow]Testing authentication with NetSuite API...[/yellow]")

        base_url = (
            f"https://{settings.ns_account_id}.suitetalk.api.netsuite.com"
            f"/services/rest/record/v1/vendor"
        )
        test_url = f"{base_url}?limit=1"

        # Get auth headers
        headers = auth.get_auth_headers(url=test_url, method="GET")
        headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

        # Display Authorization header (partially)
        auth_header = headers["Authorization"]
        console.print("[cyan]Authorization Header:[/cyan]")
        console.print(f"  {auth_header[:100]}...")
        console.print()

        # Make request
        console.print("[yellow]Making test request to NetSuite...[/yellow]")
        console.print(f"[dim]URL: {test_url}[/dim]\n")

        client = httpx.Client(timeout=30.0)
        response = client.get(test_url, headers=headers)

        # Display response details
        console.print(f"[cyan]Response Status:[/cyan] {response.status_code}")

        if response.status_code == 200:
            console.print("[bold green]✓ Authentication successful![/bold green]")
            data = response.json()
            if "items" in data:
                console.print(f"[green]✓ Retrieved {len(data['items'])} vendor(s)[/green]")
        else:
            console.print("[bold red]✗ Authentication failed[/bold red]\n")
            console.print(f"[red]Status Code:[/red] {response.status_code}")
            console.print(f"[red]Response:[/red] {response.text}\n")

            # Provide specific guidance based on error
            if response.status_code == 401:
                console.print("[yellow]Possible causes for 401 Unauthorized:[/yellow]")
                console.print("  1. Integration record is disabled in NetSuite")
                console.print("  2. Access token has been revoked or expired")
                console.print("  3. Credentials don't match (consumer key/secret vs token ID/secret)")
                console.print("  4. Wrong environment (Production vs Sandbox credentials)")
                console.print("\n[cyan]Required actions:[/cyan]")
                console.print(
                    "  • Have NetSuite admin check Setup > Integration > Manage Integrations"
                )
                console.print("  • Verify integration is Enabled")
                console.print(
                    "  • Have admin check Setup > Users/Roles > Access Tokens"
                )
                console.print("  • Verify token status is Active (not Revoked)")
                console.print(
                    "  • Check Setup > Users/Roles > View Login Audit Trail for details"
                )
            elif response.status_code == 403:
                console.print("[yellow]403 Forbidden - Permission issue:[/yellow]")
                console.print("  • Token's role lacks permissions to access Vendor records")
                console.print("  • Have admin verify role has 'Vendor (View)' permission")

    except Exception as e:
        console.print(f"[bold red]✗ Error: {e}[/bold red]")
        import traceback

        console.print("\n[dim]" + traceback.format_exc() + "[/dim]")


if __name__ == "__main__":
    test_authentication()
