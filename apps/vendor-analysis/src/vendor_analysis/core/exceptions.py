"""
Custom exceptions for vendor analysis application.

All exceptions fail fast - no swallowing, no silent failures.
"""


class VendorAnalysisError(Exception):
    """Base exception for all vendor analysis errors."""

    pass


class NetSuiteConnectionError(VendorAnalysisError):
    """NetSuite API connection or authentication failure."""

    pass


class NetSuiteAPIError(VendorAnalysisError):
    """NetSuite API returned an error response."""

    pass


class ReadOnlyViolationError(VendorAnalysisError):
    """CRITICAL: Attempted write operation in read-only application."""

    pass


class DatabaseError(VendorAnalysisError):
    """Database operation failure."""

    pass


class ConfigurationError(VendorAnalysisError):
    """Invalid or missing configuration."""

    pass


class DataValidationError(VendorAnalysisError):
    """Data validation failed."""

    pass
