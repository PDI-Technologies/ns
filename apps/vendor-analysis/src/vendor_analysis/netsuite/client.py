"""
Read-only NetSuite SuiteTalk REST API client.

CRITICAL: This client enforces read-only operations. Any attempt to use
non-GET methods will raise ReadOnlyViolationError.
"""

import logging
import time
from typing import Any

import httpx

from vendor_analysis.core.config import Settings, get_logger
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
from vendor_analysis.netsuite.auth_factory import create_auth_provider


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
        self.logger = get_logger()
        self.auth = create_auth_provider(settings)
        self.base_url = NETSUITE_BASE_URL_TEMPLATE.format(
            account_id=settings.ns_account_id,
            version=NETSUITE_API_VERSION,
        )
        self.client = httpx.Client(timeout=300.0)  # 5 minutes for SuiteQL large queries
        self.logger.debug(f"NetSuite client initialized for account {settings.ns_account_id}")

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

        # Build full URL including query parameters (required for OAuth 1.0 signature)
        base_url = f"{self.base_url}/{endpoint}"
        if params:
            from urllib.parse import urlencode

            query_string = urlencode(params)
            full_url = f"{base_url}?{query_string}"
        else:
            full_url = base_url

        headers = {
            **self.auth.get_auth_headers(url=full_url, method=method),
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        last_error: Exception | None = None
        max_retries = self.settings.max_retries
        retry_delay = self.settings.retry_delay

        self.logger.debug(f"NetSuite API request: {method} {endpoint}")

        for attempt in range(max_retries):
            try:
                # Use full_url which already includes params - don't pass params separately
                response = self.client.request(
                    method=method,
                    url=full_url,
                    headers=headers,
                )

                if response.status_code == 200:
                    self.logger.debug(f"NetSuite API success: {method} {endpoint}")
                    return response.json()  # type: ignore[no-any-return]

                # Non-200 response
                error_detail = self._parse_error_response(response)
                self.logger.error(
                    f"NetSuite API error: {method} {endpoint} - "
                    f"Status {response.status_code}: {error_detail}"
                )
                raise NetSuiteAPIError(
                    f"NetSuite API error ({response.status_code}): {error_detail}"
                )

            except httpx.HTTPError as e:
                last_error = e
                if attempt < max_retries - 1:
                    retry_num = attempt + 1
                    wait_time = retry_delay * (attempt + 1)
                    self.logger.warning(
                        f"NetSuite API retry {retry_num}/{max_retries - 1}: "
                        f"{method} {endpoint} - waiting {wait_time}s"
                    )
                    time.sleep(wait_time)
                    continue
                self.logger.error(
                    f"NetSuite API connection failed after {max_retries} attempts: {e}"
                )
                raise NetSuiteConnectionError(f"Failed after {max_retries} attempts: {e}") from e

        # Should never reach here, but satisfy type checker
        self.logger.error(f"NetSuite API request failed after {max_retries} retries")
        raise NetSuiteConnectionError(f"Request failed after {max_retries} retries: {last_error}")

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

    def query_suiteql(self, sql_query: str, limit: int = 1000, offset: int = 0) -> dict[str, Any]:
        """
        Execute SuiteQL query to fetch records with all fields.

        SuiteQL returns complete records in a single query, avoiding N+1 API calls.
        Much faster than query_records() + get_record() loop.

        Args:
            sql_query: SuiteQL SELECT statement
            limit: Page size (max 1000)
            offset: Offset for pagination

        Returns:
            Query response with items array containing full records

        Raises:
            NetSuiteAPIError: If query fails
        """
        # Build SuiteQL URL relative to base
        # base_url is like: https://610574.suitetalk.api.netsuite.com/services/rest/record/v1
        # SuiteQL is at: https://610574.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql
        suiteql_url = self.base_url.replace('/record/v1', '/query/v1/suiteql')

        # Build query string for OAuth signature
        from urllib.parse import urlencode
        query_string = urlencode({"limit": limit, "offset": offset})
        full_url = f"{suiteql_url}?{query_string}"

        # Get auth headers
        headers = {
            **self.auth.get_auth_headers(url=full_url, method="POST"),
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Prefer": "transient"  # Required for SuiteQL
        }

        params = {"limit": limit, "offset": offset}
        body = {"q": sql_query}

        response = self.client.post(
            suiteql_url,
            headers=headers,
            json=body,
            params=params,
        )

        if response.status_code != 200:
            error_detail = self._parse_error_response(response)
            self.logger.error(f"SuiteQL query failed: {error_detail}")
            self.logger.error(f"Query: {sql_query}")
            raise NetSuiteAPIError(
                f"SuiteQL query error ({response.status_code}): {error_detail}"
            )

        return response.json()

    def query_records(
        self,
        record_type: str,
        query: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Query records with optional filter.

        NOTE: NetSuite query endpoint only returns record IDs and links.
        To get full record data, use get_record() for each ID returned.

        Args:
            record_type: NetSuite record type (e.g., 'vendor')
            query: SuiteQL query or filter expression
            limit: Max records to return
            offset: Pagination offset

        Returns:
            Query response with items (containing only IDs) and metadata
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
