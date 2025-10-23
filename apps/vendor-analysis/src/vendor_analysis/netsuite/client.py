"""
Read-only NetSuite SuiteTalk REST API client.

CRITICAL: This client enforces read-only operations. Any attempt to use
non-GET methods will raise ReadOnlyViolationError.
"""

import time
from typing import Any, Final

import httpx

from vendor_analysis.core.config import Settings
from vendor_analysis.core.constants import (
    ALLOWED_HTTP_METHODS,
    NETSUITE_API_VERSION,
    NETSUITE_BASE_URL_TEMPLATE,
)
from vendor_analysis.core.exceptions import (
    NetSuiteAPIError,
    NetSuiteConnectionError,
    ReadOnlyViolationError,
)
from vendor_analysis.netsuite.auth import NetSuiteAuth


class NetSuiteClient:
    """
    Read-only NetSuite SuiteTalk REST API client.

    Enforces read-only access - only GET requests allowed.
    """

    def __init__(self, settings: Settings) -> None:
        """
        Initialize NetSuite client.

        Args:
            settings: Application settings with NetSuite credentials
        """
        self.settings = settings
        self.auth = NetSuiteAuth(settings)
        self.base_url = NETSUITE_BASE_URL_TEMPLATE.format(
            account_id=settings.ns_account_id,
            version=NETSUITE_API_VERSION,
        )
        self.client = httpx.Client(timeout=30.0)

    def _enforce_read_only(self, method: str) -> None:
        """
        Enforce read-only constraint.

        Args:
            method: HTTP method

        Raises:
            ReadOnlyViolationError: If method is not GET
        """
        if method.upper() not in ALLOWED_HTTP_METHODS:
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

        for attempt in range(max_retries):
            try:
                response = self.client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                )

                if response.status_code == 200:
                    return response.json()  # type: ignore[no-any-return]

                # Non-200 response
                error_detail = self._parse_error_response(response)
                raise NetSuiteAPIError(
                    f"NetSuite API error ({response.status_code}): {error_detail}"
                )

            except httpx.HTTPError as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                raise NetSuiteConnectionError(
                    f"Failed after {max_retries} attempts: {e}"
                ) from e

        # Should never reach here, but satisfy type checker
        raise NetSuiteConnectionError(
            f"Request failed after {max_retries} retries: {last_error}"
        )

    def _parse_error_response(self, response: httpx.Response) -> str:
        """Parse error message from NetSuite response."""
        try:
            error_data = response.json()
            if "o:errorDetails" in error_data:
                details = error_data["o:errorDetails"]
                if isinstance(details, list) and details:
                    return details[0].get("detail", response.text)
            return error_data.get("message", response.text)
        except Exception:
            return response.text

    def get_record(
        self,
        record_type: str,
        record_id: str,
        fields: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Get single record by ID.

        Args:
            record_type: NetSuite record type (e.g., 'vendor')
            record_id: Internal record ID
            fields: Optional list of fields to return

        Returns:
            Record data
        """
        endpoint = f"{record_type}/{record_id}"
        params = {"fields": ",".join(fields)} if fields else None
        return self._request("GET", endpoint, params=params)

    def query_records(
        self,
        record_type: str,
        query: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Query records with optional filter.

        Args:
            record_type: NetSuite record type (e.g., 'vendor')
            query: SuiteQL query or filter expression
            limit: Max records to return
            offset: Pagination offset

        Returns:
            Query response with items and metadata
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if query:
            params["q"] = query

        return self._request("GET", record_type, params=params)

    def __enter__(self) -> "NetSuiteClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit - close HTTP client."""
        self.client.close()
