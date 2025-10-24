#!/usr/bin/env python3
"""
Bootstrap script for vendor-analysis application.

100% idempotent - safe to run multiple times.
Fail-fast - stops on first error with clear error messages.
Logs to console (with colors) and bootstrap.log file.
"""

import logging
import subprocess
import sys
from pathlib import Path
from typing import NoReturn

# Rich console output
try:
    from rich.console import Console
    from rich.logging import RichHandler
    from rich.panel import Panel
except ImportError:
    print("ERROR: Rich library not installed")
    print("Install with: pip install rich")
    print("Or: uv pip install rich")
    sys.exit(1)

console = Console()

# Dual logging: console (Rich) + file
log_file = Path.cwd() / "bootstrap.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        RichHandler(console=console, rich_tracebacks=True, markup=True),
        logging.FileHandler(log_file, mode="a", encoding="utf-8"),
    ],
)
logger = logging.getLogger("bootstrap")


class BootstrapError(Exception):
    """Fatal bootstrap error - fail fast."""

    pass


def fail(message: str) -> NoReturn:
    """
    Fail fast with error message.

    Args:
        message: Error message

    Raises:
        SystemExit: Always exits with code 1
    """
    logger.error(message)
    console.print("\n[red bold]✗ BOOTSTRAP FAILED[/red bold]")
    console.print(f"[red]{message}[/red]")
    console.print(f"\n[yellow]Check {log_file} for details[/yellow]")
    sys.exit(1)


def run_command(
    cmd: list[str],
    description: str,
    cwd: Path | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess:
    """
    Run command with live output streaming to console and log.

    Args:
        cmd: Command and arguments
        description: Human-readable description
        cwd: Working directory
        check: Raise on non-zero exit

    Returns:
        CompletedProcess result

    Raises:
        BootstrapError: If command fails and check=True
    """
    logger.info(f"{description}")
    logger.debug(f"Running: {' '.join(cmd)}")

    try:
        # Use Popen for live output streaming
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        output_lines: list[str] = []
        if process.stdout:
            for line in process.stdout:
                line = line.rstrip()
                output_lines.append(line)
                # Print to console
                console.print(f"  [dim]{line}[/dim]")
                # Write to log file
                logger.debug(line)

        returncode = process.wait()

        if check and returncode != 0:
            raise BootstrapError(
                f"{description} failed with exit code {returncode}\n"
                f"Command: {' '.join(cmd)}\n"
                f"Output (last 10 lines):\n" + "\n".join(output_lines[-10:])
            )

        return subprocess.CompletedProcess(
            cmd, returncode, stdout="\n".join(output_lines), stderr=""
        )

    except FileNotFoundError as e:
        raise BootstrapError(f"Command not found: {cmd[0]}") from e
    except Exception as e:
        raise BootstrapError(f"{description} failed: {e}") from e


def check_python_version() -> None:
    """Check Python version >= 3.12."""
    logger.info("Checking Python version...")
    version = sys.version_info

    if version < (3, 12):
        fail(
            f"Python 3.12+ required, found {version.major}.{version.minor}.{version.micro}\n"
            f"Install Python 3.12+: https://www.python.org/downloads/"
        )

    console.print(
        f"[green]✓[/green] Python {version.major}.{version.minor}.{version.micro}"
    )


def check_uv_installed() -> bool:
    """Check if UV package manager is installed."""
    logger.info("Checking for UV package manager...")
    try:
        result = subprocess.run(
            ["uv", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            console.print(f"[green]✓[/green] UV installed: {version}")
            return True
        return False
    except FileNotFoundError:
        return False


def install_uv() -> None:
    """Install UV package manager."""
    console.print("[yellow]UV not found, installing...[/yellow]")
    logger.info("Installing UV package manager...")

    install_cmd = [
        "sh",
        "-c",
        "curl -LsSf https://astral.sh/uv/install.sh | sh",
    ]

    try:
        run_command(install_cmd, "Installing UV package manager")
        console.print("[green]✓[/green] UV installed successfully")
    except BootstrapError:
        fail(
            "Failed to install UV package manager\n"
            "Manually install: curl -LsSf https://astral.sh/uv/install.sh | sh"
        )


def check_directory() -> Path:
    """Verify we're in vendor-analysis directory."""
    logger.info("Checking directory...")
    cwd = Path.cwd()

    # Check for pyproject.toml with correct name
    pyproject = cwd / "pyproject.toml"
    if not pyproject.exists():
        fail(
            f"pyproject.toml not found in {cwd}\n"
            f"Run this script from apps/vendor-analysis directory"
        )

    # Verify it's the vendor-analysis project
    content = pyproject.read_text()
    if 'name = "vendor-analysis"' not in content:
        fail(
            f"Not in vendor-analysis directory\n"
            f"Current: {cwd}\n"
            f"Expected: .../apps/vendor-analysis"
        )

    console.print(f"[green]✓[/green] Directory: {cwd}")
    return cwd


def sync_dependencies(project_dir: Path) -> None:
    """Install dependencies with UV (idempotent)."""
    logger.info("Installing dependencies with UV...")

    # Check if already synced
    venv_dir = project_dir / ".venv"
    if venv_dir.exists():
        logger.info("Virtual environment exists, updating dependencies...")
        console.print("[dim]Virtual environment found, updating...[/dim]")
    else:
        logger.info("Creating virtual environment and installing dependencies...")
        console.print("[yellow]Creating virtual environment...[/yellow]")

    run_command(
        ["uv", "sync"],
        "Installing dependencies",
        cwd=project_dir,
    )

    console.print("[green]✓[/green] Dependencies installed")


def check_config_files(project_dir: Path) -> None:
    """Verify configuration files exist."""
    logger.info("Checking configuration files...")

    # Check config.yaml
    config_yaml = project_dir / "config.yaml"
    if not config_yaml.exists():
        fail(
            f"config.yaml not found in {project_dir}\n"
            f"This file should exist in the repository"
        )
    console.print("[green]✓[/green] config.yaml found")

    # Check .env (or symlink)
    env_file = project_dir / ".env"
    if not env_file.exists():
        console.print("[yellow]⚠[/yellow] .env file not found")
        console.print(
            "[yellow]Create .env file with NetSuite and database credentials[/yellow]"
        )
        console.print("[yellow]See .env.example for template[/yellow]")
        fail(
            ".env file required\n"
            "Create from template: cp .env.example .env\n"
            "Or symlink from parent: ln -s ../../.env .env"
        )

    console.print("[green]✓[/green] .env found")


def check_database_connection(project_dir: Path) -> bool:
    """Check if PostgreSQL database is accessible."""
    logger.info("Checking database connection...")

    # Try to import psycopg2 and test connection
    test_script = """
import sys
import os
sys.path.insert(0, 'src')

try:
    from vendor_analysis.core.config import get_settings
    from sqlalchemy import create_engine, text

    settings = get_settings()
    engine = create_engine(settings.database_url)

    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.scalar()
        print(f"PostgreSQL: {version.split(',')[0]}")
        sys.exit(0)
except Exception as e:
    print(f"Database connection failed: {e}", file=sys.stderr)
    sys.exit(1)
"""

    test_file = project_dir / "test_db_connection.py"
    test_file.write_text(test_script)

    try:
        result = subprocess.run(
            ["uv", "run", "python", "test_db_connection.py"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            check=False,
        )

        test_file.unlink()  # Clean up

        if result.returncode == 0:
            console.print(f"[green]✓[/green] Database connected: {result.stdout.strip()}")
            return True
        else:
            console.print("[yellow]⚠[/yellow] Database not accessible")
            logger.warning(f"Database check failed: {result.stderr}")
            return False

    except Exception as e:
        logger.warning(f"Database check error: {e}")
        if test_file.exists():
            test_file.unlink()
        return False


def create_database_if_needed() -> None:
    """Prompt to create database if not accessible."""
    console.print("\n[yellow]Database Setup Required[/yellow]")
    console.print("\nOptions:")
    console.print("1. Use Supabase PostgreSQL (recommended if already running)")
    console.print("   docker exec -e PGPASSWORD=postgres supabase_db_supabase \\")
    console.print("     psql -U supabase_admin -d postgres \\")
    console.print("     -c 'CREATE DATABASE vendor_analysis OWNER supabase_admin;'")
    console.print("\n2. Use standalone PostgreSQL")
    console.print("   docker run -d --name vendor-analysis-db \\")
    console.print("     -p 5432:5432 -e POSTGRES_PASSWORD=postgres \\")
    console.print("     -e POSTGRES_DB=vendor_analysis postgres:17")
    console.print("\n3. Use existing PostgreSQL instance")
    console.print("   Update config.yaml with your database host/port/name")

    console.print("\n[yellow]After database setup, re-run this script[/yellow]")
    sys.exit(0)


def initialize_database(project_dir: Path) -> None:
    """Initialize database schema (idempotent)."""
    logger.info("Initializing database schema...")

    run_command(
        ["uv", "run", "vendor-analysis", "init-db"],
        "Initializing database schema",
        cwd=project_dir,
    )

    console.print("[green]✓[/green] Database schema initialized")


def verify_cli(project_dir: Path) -> None:
    """Verify CLI is working."""
    logger.info("Verifying CLI...")

    result = subprocess.run(
        ["uv", "run", "vendor-analysis", "--help"],
        cwd=project_dir,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        fail(f"CLI verification failed:\n{result.stderr}")

    console.print("[green]✓[/green] CLI working")


def main() -> None:
    """Main bootstrap process."""
    console.print(
        Panel.fit(
            "[bold cyan]Vendor Analysis Bootstrap[/bold cyan]\n"
            "[dim]Idempotent setup for NetSuite vendor cost analysis[/dim]",
            border_style="cyan",
        )
    )

    logger.info(f"Bootstrap started, logging to: {log_file}")
    console.print(f"[dim]Logging to: {log_file}[/dim]\n")

    try:
        # 1. Check Python version
        check_python_version()

        # 2. Check/install UV
        if not check_uv_installed():
            install_uv()

        # 3. Verify directory
        project_dir = check_directory()

        # 4. Install dependencies
        sync_dependencies(project_dir)

        # 5. Check configuration files
        check_config_files(project_dir)

        # 6. Check database
        db_accessible = check_database_connection(project_dir)
        if not db_accessible:
            create_database_if_needed()

        # 7. Initialize database schema
        initialize_database(project_dir)

        # 8. Verify CLI
        verify_cli(project_dir)

        # Success
        console.print("\n" + "=" * 60)
        console.print(
            Panel.fit(
                "[bold green]✓ Bootstrap Complete![/bold green]\n\n"
                "Next steps:\n"
                "1. Verify NetSuite credentials in .env\n"
                "2. Run: uv run vendor-analysis sync\n"
                "3. Run: uv run vendor-analysis analyze",
                border_style="green",
            )
        )
        logger.info("Bootstrap completed successfully")

    except BootstrapError as e:
        fail(str(e))
    except KeyboardInterrupt:
        console.print("\n[yellow]Bootstrap interrupted by user[/yellow]")
        logger.warning("Bootstrap interrupted")
        sys.exit(130)
    except Exception as e:
        logger.exception("Unexpected error during bootstrap")
        fail(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
