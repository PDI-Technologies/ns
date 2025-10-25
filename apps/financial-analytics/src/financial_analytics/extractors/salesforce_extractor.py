"""
Salesforce data extraction using MCP tools.

Uses pdi-salesforce-sse3 MCP server for data access.
Based on salesforce-mcp skill and financial-analytics integration patterns.
"""

from datetime import date, datetime, timedelta
from typing import Any

from pydantic import BaseModel

from financial_analytics.core.exceptions import SalesforceConnectionError

# MCP tools are injected at runtime by the environment
# They are not imported but available as global functions


class SalesforceOpportunity(BaseModel):
    """Salesforce Opportunity record for revenue analysis."""

    Id: str
    Name: str
    Amount: float | None = None
    CloseDate: date
    StageName: str
    Probability: float | None = None
    Type: str | None = None
    AccountId: str | None = None
    AccountName: str | None = None
    Industry: str | None = None
    OwnerName: str | None = None
    IsClosed: bool = False
    IsWon: bool = False


class SalesforceAccount(BaseModel):
    """Salesforce Account record."""

    Id: str
    Name: str
    Type: str | None = None
    Industry: str | None = None
    AnnualRevenue: float | None = None
    NumberOfEmployees: int | None = None


def fetch_opportunities(
    months_back: int = 12,
    page_size: int = 200,
) -> list[SalesforceOpportunity]:
    """
    Fetch opportunities from Salesforce for revenue analysis.

    Args:
        months_back: Number of months of historical data
        page_size: Records per page

    Returns:
        List of opportunity records

    Raises:
        SalesforceConnectionError: If query fails
    """
    # Calculate cutoff date
    cutoff = datetime.now().replace(day=1)
    for _ in range(months_back):
        cutoff = (cutoff.replace(day=1) - timedelta(days=1)).replace(day=1)

    cutoff_str = cutoff.strftime("%Y-%m-%d")

    soql = f"""
        SELECT
            Id,
            Name,
            Amount,
            CloseDate,
            StageName,
            Probability,
            Type,
            Account.Name,
            Account.Industry,
            Owner.Name,
            IsClosed,
            IsWon
        FROM Opportunity
        WHERE CloseDate >= {cutoff_str}
        ORDER BY CloseDate DESC
    """

    opportunities: list[SalesforceOpportunity] = []
    page = 1

    try:
        while True:
            # Use MCP tool to query Salesforce
            result: dict[str, Any] = mcp__pdi_salesforce_sse3__query(  # type: ignore[name-defined]
                soql=soql,
                pageNumber=page,
                pageSize=page_size,
            )

            records = result.get("records", [])
            if not records:
                break

            # Parse records
            for record in records:
                # Flatten nested Account and Owner data
                account_name = None
                industry = None
                if "Account" in record and record["Account"]:
                    account_name = record["Account"].get("Name")
                    industry = record["Account"].get("Industry")

                owner_name = None
                if "Owner" in record and record["Owner"]:
                    owner_name = record["Owner"].get("Name")

                opportunities.append(
                    SalesforceOpportunity(
                        Id=record["Id"],
                        Name=record["Name"],
                        Amount=record.get("Amount"),
                        CloseDate=record["CloseDate"],
                        StageName=record["StageName"],
                        Probability=record.get("Probability"),
                        Type=record.get("Type"),
                        AccountId=record.get("AccountId"),
                        AccountName=account_name,
                        Industry=industry,
                        OwnerName=owner_name,
                        IsClosed=record.get("IsClosed", False),
                        IsWon=record.get("IsWon", False),
                    )
                )

            if not result.get("hasMore", False):
                break

            page += 1

    except Exception as e:
        raise SalesforceConnectionError(f"Failed to fetch opportunities: {e}") from e

    return opportunities


def fetch_closed_won_opportunities(months_back: int = 12) -> list[SalesforceOpportunity]:
    """
    Fetch closed-won opportunities for revenue analysis.

    Args:
        months_back: Number of months of historical data

    Returns:
        List of closed-won opportunities
    """
    cutoff = datetime.now().replace(day=1)
    for _ in range(months_back):
        cutoff = (cutoff.replace(day=1) - timedelta(days=1)).replace(day=1)

    cutoff_str = cutoff.strftime("%Y-%m-%d")

    soql = f"""
        SELECT
            Id,
            Name,
            Amount,
            CloseDate,
            StageName,
            Account.Name,
            Account.Industry,
            Owner.Name
        FROM Opportunity
        WHERE IsWon = true
        AND CloseDate >= {cutoff_str}
        ORDER BY CloseDate DESC
    """

    opportunities: list[SalesforceOpportunity] = []
    page = 1

    try:
        while True:
            result: dict[str, Any] = mcp__pdi_salesforce_sse3__query(  # type: ignore[name-defined]
                soql=soql,
                pageNumber=page,
                pageSize=200,
            )

            records = result.get("records", [])
            if not records:
                break

            for record in records:
                account_name = None
                industry = None
                if "Account" in record and record["Account"]:
                    account_name = record["Account"].get("Name")
                    industry = record["Account"].get("Industry")

                owner_name = None
                if "Owner" in record and record["Owner"]:
                    owner_name = record["Owner"].get("Name")

                opportunities.append(
                    SalesforceOpportunity(
                        Id=record["Id"],
                        Name=record["Name"],
                        Amount=record.get("Amount", 0.0),
                        CloseDate=record["CloseDate"],
                        StageName=record["StageName"],
                        AccountName=account_name,
                        Industry=industry,
                        OwnerName=owner_name,
                        IsWon=True,
                    )
                )

            if not result.get("hasMore", False):
                break

            page += 1

    except Exception as e:
        raise SalesforceConnectionError(f"Failed to fetch closed-won opportunities: {e}") from e

    return opportunities


def fetch_accounts(page_size: int = 200) -> list[SalesforceAccount]:
    """
    Fetch Salesforce accounts.

    Args:
        page_size: Records per page

    Returns:
        List of account records
    """
    soql = """
        SELECT
            Id,
            Name,
            Type,
            Industry,
            AnnualRevenue,
            NumberOfEmployees
        FROM Account
        WHERE Type = 'Customer'
        ORDER BY Name ASC
    """

    accounts: list[SalesforceAccount] = []
    page = 1

    try:
        while True:
            result: dict[str, Any] = mcp__pdi_salesforce_sse3__query(  # type: ignore[name-defined]
                soql=soql,
                pageNumber=page,
                pageSize=page_size,
            )

            records = result.get("records", [])
            if not records:
                break

            for record in records:
                accounts.append(SalesforceAccount(**record))

            if not result.get("hasMore", False):
                break

            page += 1

    except Exception as e:
        raise SalesforceConnectionError(f"Failed to fetch accounts: {e}") from e

    return accounts
