"""
Financial analysis commands.

Following python-cli-engineering patterns with Rich output.
"""

import typer
from rich.console import Console
from rich.table import Table

from financial_analytics.analytics.revenue_analysis import (
    analyze_revenue_trends,
    calculate_customer_ltv,
)
from financial_analytics.analytics.salesforce_analysis import (
    analyze_by_industry,
    analyze_revenue_pipeline,
)
from financial_analytics.analytics.vendor_analysis import (
    detect_duplicate_vendors,
    get_top_vendors,
)
from financial_analytics.core.config import Settings
from financial_analytics.db.session import get_session

console = Console()


def analyze_command(
    months: int = typer.Option(12, "--months", "-m", help="Analysis period in months"),
) -> None:
    """
    Run comprehensive financial analysis.

    Analyzes vendors, revenue, and displays key metrics.
    """
    console.print(f"[cyan]Running financial analysis ({months} months)[/cyan]\n")

    settings = Settings()  # type: ignore[call-arg]  # Reads from .env at runtime  # type: ignore[call-arg]  # Reads from .env at runtime
    session = get_session(settings)

    # Vendor analysis
    console.print("[yellow]Top Vendors by Spend:[/yellow]")
    vendors = get_top_vendors(session, settings, top_n=10)

    if vendors:
        table = Table(title="Vendor Spend Analysis")
        table.add_column("Rank", style="cyan")
        table.add_column("Vendor", style="magenta")
        table.add_column("Total Spend", justify="right", style="green")
        table.add_column("Transactions", justify="right")

        for idx, vendor in enumerate(vendors, 1):
            table.add_row(
                str(idx),
                vendor.company_name,
                f"${vendor.total_spend:,.2f}",
                str(vendor.transaction_count),
            )

        console.print(table)
    else:
        console.print("[red]No vendor data available[/red]")

    # Revenue analysis
    console.print("\n[yellow]Revenue Trends:[/yellow]")
    trends = analyze_revenue_trends(session, settings, months=months)

    if trends:
        table = Table(title="Monthly Revenue")
        table.add_column("Period", style="cyan")
        table.add_column("Revenue", justify="right", style="green")
        table.add_column("Invoices", justify="right")
        table.add_column("Growth", justify="right")

        for trend in trends[-12:]:  # Last 12 months
            growth_str = (
                f"{trend.revenue_growth_pct:+.1f}%"
                if trend.revenue_growth_pct is not None
                else "N/A"
            )
            table.add_row(
                trend.period,
                f"${trend.total_revenue:,.2f}",
                str(trend.invoice_count),
                growth_str,
            )

        console.print(table)
    else:
        console.print("[red]No revenue data available[/red]")

    session.close()


def vendors_command(
    top: int = typer.Option(25, "--top", "-n", help="Number of top vendors to display"),
    duplicates: bool = typer.Option(False, "--duplicates", help="Show duplicate vendors"),
) -> None:
    """
    Analyze vendor spend and detect duplicates.
    """
    settings = Settings()  # type: ignore[call-arg]  # Reads from .env at runtime
    session = get_session(settings)

    if duplicates:
        console.print("[yellow]Detecting duplicate vendors...[/yellow]\n")
        pairs = detect_duplicate_vendors(session, settings)

        if pairs:
            table = Table(title="Potential Duplicate Vendors")
            table.add_column("Vendor 1", style="magenta")
            table.add_column("Vendor 2", style="magenta")
            table.add_column("Similarity", justify="right", style="yellow")

            for pair in pairs[:20]:  # Top 20 duplicates
                table.add_row(
                    pair.vendor1_name,
                    pair.vendor2_name,
                    f"{pair.similarity * 100:.1f}%",
                )

            console.print(table)
        else:
            console.print("[green]No duplicate vendors found[/green]")
    else:
        console.print(f"[yellow]Top {top} Vendors by Spend:[/yellow]\n")
        vendors = get_top_vendors(session, settings, top_n=top)

        if vendors:
            table = Table(title=f"Top {top} Vendors")
            table.add_column("Rank", style="cyan")
            table.add_column("Vendor", style="magenta")
            table.add_column("Total Spend", justify="right", style="green")
            table.add_column("Transactions", justify="right")
            table.add_column("Avg Transaction", justify="right")

            for idx, vendor in enumerate(vendors, 1):
                table.add_row(
                    str(idx),
                    vendor.company_name,
                    f"${vendor.total_spend:,.2f}",
                    str(vendor.transaction_count),
                    f"${vendor.avg_transaction:,.2f}",
                )

            console.print(table)
        else:
            console.print("[red]No vendor data available[/red]")

    session.close()


def revenue_command(
    months: int = typer.Option(12, "--months", "-m", help="Analysis period in months"),
    ltv: bool = typer.Option(False, "--ltv", help="Show customer lifetime value"),
) -> None:
    """
    Analyze revenue trends and customer value.
    """
    settings = Settings()  # type: ignore[call-arg]  # Reads from .env at runtime
    session = get_session(settings)

    if ltv:
        console.print("[yellow]Customer Lifetime Value:[/yellow]\n")
        customers = calculate_customer_ltv(session)

        if customers:
            table = Table(title="Top Customers by Revenue")
            table.add_column("Rank", style="cyan")
            table.add_column("Customer", style="magenta")
            table.add_column("Total Revenue", justify="right", style="green")
            table.add_column("Orders", justify="right")
            table.add_column("Avg Order", justify="right")

            for idx, customer in enumerate(customers[:25], 1):
                table.add_row(
                    str(idx),
                    customer.company_name,
                    f"${customer.total_revenue:,.2f}",
                    str(customer.invoice_count),
                    f"${customer.avg_order_value:,.2f}",
                )

            console.print(table)
        else:
            console.print("[red]No customer data available[/red]")
    else:
        console.print(f"[yellow]Revenue Trends ({months} months):[/yellow]\n")
        trends = analyze_revenue_trends(session, settings, months=months)

        if trends:
            table = Table(title="Monthly Revenue Trends")
            table.add_column("Period", style="cyan")
            table.add_column("Revenue", justify="right", style="green")
            table.add_column("Invoices", justify="right")
            table.add_column("Avg Invoice", justify="right")
            table.add_column("Growth", justify="right")

            for trend in trends:
                growth_str = (
                    f"{trend.revenue_growth_pct:+.1f}%"
                    if trend.revenue_growth_pct is not None
                    else "N/A"
                )
                table.add_row(
                    trend.period,
                    f"${trend.total_revenue:,.2f}",
                    str(trend.invoice_count),
                    f"${trend.avg_invoice_size:,.2f}",
                    growth_str,
                )

            console.print(table)
        else:
            console.print("[red]No revenue data available[/red]")

    session.close()


def pipeline_command(
    by_industry: bool = typer.Option(False, "--by-industry", help="Show revenue by industry"),
) -> None:
    """
    Analyze Salesforce revenue pipeline and forecasts.

    Requires Salesforce sync to be enabled and data synced.
    """
    settings = Settings()  # type: ignore[call-arg]  # Reads from .env at runtime

    if not settings.sf_enabled:
        console.print("[red]Salesforce integration is not enabled[/red]")
        console.print("Set SF_ENABLED=true in .env to enable Salesforce integration")
        raise typer.Exit(code=1)

    session = get_session(settings)

    if by_industry:
        console.print("[yellow]Revenue by Industry:[/yellow]\n")
        industries = analyze_by_industry(session)

        if industries:
            table = Table(title="Revenue by Industry")
            table.add_column("Rank", style="cyan")
            table.add_column("Industry", style="magenta")
            table.add_column("Total Revenue", justify="right", style="green")
            table.add_column("Deals", justify="right")
            table.add_column("Avg Deal Size", justify="right")

            for idx, industry in enumerate(industries, 1):
                table.add_row(
                    str(idx),
                    industry.industry,
                    f"${industry.total_revenue:,.2f}",
                    str(industry.opportunity_count),
                    f"${industry.avg_deal_size:,.2f}",
                )

            console.print(table)
        else:
            console.print("[red]No industry data available[/red]")
    else:
        console.print("[yellow]Revenue Pipeline Analysis:[/yellow]\n")
        pipeline = analyze_revenue_pipeline(session)

        if pipeline:
            table = Table(title="Opportunity Pipeline by Stage")
            table.add_column("Stage", style="magenta")
            table.add_column("Count", justify="right")
            table.add_column("Total Amount", justify="right", style="green")
            table.add_column("Weighted Amount", justify="right", style="cyan")
            table.add_column("Avg Deal", justify="right")
            table.add_column("Win Prob", justify="right")

            for stage in pipeline:
                table.add_row(
                    stage.stage_name,
                    str(stage.opportunity_count),
                    f"${stage.total_amount:,.2f}",
                    f"${stage.weighted_amount:,.2f}",
                    f"${stage.avg_deal_size:,.2f}",
                    f"{stage.win_probability:.1f}%",
                )

            console.print(table)

            # Summary
            total_pipeline = sum(s.total_amount for s in pipeline)
            total_weighted = sum(s.weighted_amount for s in pipeline)
            console.print(f"\n[cyan]Total Pipeline:[/cyan] ${total_pipeline:,.2f}")
            console.print(f"[cyan]Weighted Pipeline:[/cyan] ${total_weighted:,.2f}")
        else:
            console.print("[red]No pipeline data available[/red]")
            console.print("Run 'fin-analytics sync --salesforce-only' to fetch Salesforce data")

    session.close()
