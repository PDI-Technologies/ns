"""
Read-only NetSuite SuiteTalk REST API client.

CRITICAL: Enforces read-only operations following CLAUDE.md guidelines.
Based on vendor-analysis implementation and netsuite-integrations skill.
"""

import time
from typing import Any

import httpx

from financial_analytics.core.config import Settings, get_logger
from financial_analytics.core.constants import (
    ALLOWED_HTTP_METHODS,
    NETSUITE_API_VERSION,
    NETSUITE_BASE_URL_TEMPLATE,
)
from financial_analytics.core.exceptions import (
    NetSuiteAPIError,
    NetSuiteConnectionError,
    ReadOnlyViolationError,
)
from financial_analytics.extractors.netsuite_auth import NetSuiteAuth


class NetSuiteClient:
    """
    Read-only NetSuite SuiteTalk REST API client.

    Enforces read-only access per CLAUDE.md - only GET requests allowed.
    Fail-fast discipline: All errors propagate immediately.
    """

    def __init__(self, settings: Settings) -> None:
        """
        Initialize NetSuite client.

        Args:
            settings: Application settings with NetSuite credentials

        Raises:
            ConfigurationError: If credentials missing
        """
        self.settings = settings
        self.logger = get_logger()
        self.auth = NetSuiteAuth(settings)
        self.base_url = NETSUITE_BASE_URL_TEMPLATE.format(
            account_id=settings.ns_account_id,
            version=NETSUITE_API_VERSION,
        )
        self.client = httpx.Client(timeout=30.0)
        self.logger.debug(f"NetSuite client initialized for account {settings.ns_account_id}")

    def __enter__(self) -> "NetSuiteClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit - cleanup resources."""
        self.client.close()

    def _enforce_read_only(self, method: str) -> None:
        """
        Enforce read-only constraint.

        Args:
            method: HTTP method

        Raises:
            ReadOnlyViolationError: If method is not GET
        """
        if method.upper() not in ALLOWED_HTTP_METHODS:
            self.logger.error(f"Attempted {method} operation on read-only client")
            raise ReadOnlyViolationError(
                f"CRITICAL: Attempted {method} operation. "
                f"This application is READ-ONLY. Only {ALLOWED_HTTP_METHODS} allowed."
            )

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Make HTTP request to NetSuite API with retries.

        Args:
            method: HTTP method (must be GET)
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            JSON response data

        Raises:
            ReadOnlyViolationError: If method is not GET
            NetSuiteConnectionError: If connection fails
            NetSuiteAPIError: If API returns error
        """
        self._enforce_read_only(method)

        url = f"{self.base_url}/{endpoint}"
        headers = {
            **self.auth.get_auth_headers(),
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        last_error: Exception | None = None
        max_retries = self.settings.max_retries
        retry_delay = self.settings.retry_delay

        self.logger.debug(f"NetSuite API request: {method} {endpoint}")

        for attempt in range(max_retries):
            try:
                response = self.client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                )
                response.raise_for_status()
                self.logger.debug(f"NetSuite API success: {method} {endpoint}")
                return response.json()

            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 400 and e.response.status_code < 500:
                    # Client errors - don't retry
                    self.logger.error(
                        f"NetSuite API client error: {method} {endpoint} - "
                        f"Status {e.response.status_code}: {e.response.text}"
                    )
                    raise NetSuiteAPIError(
                        f"NetSuite API error (HTTP {e.response.status_code}): "
                        f"{e.response.text}"
                    ) from e
                last_error = e

            except httpx.HTTPError as e:
                last_error = e

            if attempt < max_retries - 1:
                retry_num = attempt + 1
                wait_time = retry_delay * (2**attempt)
                self.logger.warning(
                    f"NetSuite API retry {retry_num}/{max_retries - 1}: "
                    f"{method} {endpoint} - waiting {wait_time}s"
                )
                time.sleep(wait_time)

        self.logger.error(
            f"NetSuite API connection failed after {max_retries} attempts: {last_error}"
        )
        raise NetSuiteConnectionError(
            f"Failed after {max_retries} attempts: {last_error}"
        ) from last_error

    def get_record(self, record_type: str, record_id: str) -> dict[str, Any]:
        """
        Get single record by ID.

        Args:
            record_type: Type of record (e.g., 'vendor', 'customer')
            record_id: Internal ID of record

        Returns:
            Record data as dictionary

        Raises:
            NetSuiteAPIError: If record not found or API error
        """
        endpoint = f"{record_type}/{record_id}"
        return self._request("GET", endpoint)

    def query_records(
        self,
        record_type: str,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Query records with pagination.

        Args:
            record_type: Type of record to query
            limit: Maximum records to return
            offset: Starting offset for pagination

        Returns:
            Response with items array and pagination info

        Raises:
            NetSuiteAPIError: If query fails
        """
        params = {
            "limit": limit,
            "offset": offset,
        }
        return self._request("GET", record_type, params=params)
