"""
Custom exceptions for financial analytics application.

All exceptions inherit from FinancialAnalyticsError for easy catching.
Follows fail-fast discipline - no exception swallowing.
"""


class FinancialAnalyticsError(Exception):
    """Base exception for all application errors."""

    pass


class ConfigurationError(FinancialAnalyticsError):
    """Configuration file missing, invalid, or incomplete."""

    pass


class NetSuiteConnectionError(FinancialAnalyticsError):
    """Failed to connect to NetSuite API."""

    pass


class NetSuiteAPIError(FinancialAnalyticsError):
    """NetSuite API returned an error response."""

    pass


class ReadOnlyViolationError(FinancialAnalyticsError):
    """Attempted write operation on read-only client."""

    pass


class DatabaseError(FinancialAnalyticsError):
    """Database operation failed."""

    pass


class SalesforceConnectionError(FinancialAnalyticsError):
    """Failed to connect to Salesforce."""

    pass


class DataValidationError(FinancialAnalyticsError):
    """Data validation failed."""

    pass
