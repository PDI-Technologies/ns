#!/usr/bin/env python3
"""
Run database migration to add custom fields support.

This script:
1. Connects to the PostgreSQL database
2. Runs the SQL migration script
3. Verifies the migration succeeded
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import text

from vendor_analysis.core.config import get_settings
from vendor_analysis.db.session import get_session

from rich.console import Console

console = Console()


def run_migration() -> None:
    """Run the database migration."""
    console.print("\n[bold cyan]Database Migration: Add Custom Fields Support[/bold cyan]\n")

    # Load configuration
    console.print("[yellow]Loading configuration...[/yellow]")
    settings = get_settings()
    session = get_session(settings)

    # Read migration SQL
    migration_file = Path(__file__).parent / "migrate_add_custom_fields.sql"
    console.print(f"[yellow]Reading migration file: {migration_file}[/yellow]")

    if not migration_file.exists():
        console.print(f"[red]Error: Migration file not found: {migration_file}[/red]")
        sys.exit(1)

    with open(migration_file) as f:
        migration_sql = f.read()

    # Execute migration
    console.print("[yellow]Executing migration...[/yellow]")

    try:
        # Execute the SQL
        session.execute(text(migration_sql))
        session.commit()

        console.print("[green]✓ Migration completed successfully![/green]")
        console.print("\n[cyan]Database schema updated:[/cyan]")
        console.print("  • vendors.custom_fields (JSONB) - Custom NetSuite fields")
        console.print("  • vendors.raw_data (JSONB) - Complete API responses")
        console.print("  • vendors.schema_version (INTEGER) - Schema tracking")
        console.print("  • transactions.custom_fields (JSONB) - Custom transaction fields")
        console.print("  • transactions.raw_data (JSONB) - Complete API responses")
        console.print("  • transactions.schema_version (INTEGER) - Schema tracking")
        console.print("  • GIN indexes on JSONB columns")
        console.print("  • Helper functions for querying custom fields")

        console.print("\n[green]You can now run sync to populate custom fields![/green]")

    except Exception as e:
        console.print(f"\n[red]✗ Migration failed:[/red]")
        console.print(f"[red]{str(e)}[/red]")
        session.rollback()
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    run_migration()
