"""
NetSuite OAuth 2.0 authentication.

Implements OAuth 2.0 Client Credentials flow as required by NetSuite (Feb 2025+).
Based on patterns from netsuite-integrations skill and vendor-analysis implementation.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

import httpx

from financial_analytics.core.config import Settings
from financial_analytics.core.constants import NETSUITE_OAUTH_URL_TEMPLATE
from financial_analytics.core.exceptions import NetSuiteConnectionError


@dataclass
class OAuth2Token:
    """OAuth 2.0 access token with expiration tracking."""

    access_token: str
    token_type: str
    expires_at: datetime

    def is_expired(self) -> bool:
        """Check if token is expired (with 60-second buffer)."""
        return datetime.now() >= self.expires_at - timedelta(seconds=60)


class NetSuiteAuth:
    """
    NetSuite OAuth 2.0 authentication handler.

    Manages token lifecycle with automatic refresh.
    Fail-fast: Raises exception immediately on auth failure.
    """

    def __init__(self, settings: Settings) -> None:
        """
        Initialize NetSuite authentication.

        Args:
            settings: Application settings with NetSuite credentials

        Raises:
            ConfigurationError: If required credentials missing
        """
        self.settings = settings
        self.token: OAuth2Token | None = None
        self.oauth_url = NETSUITE_OAUTH_URL_TEMPLATE.format(
            account_id=settings.ns_account_id
        )

    def get_access_token(self) -> str:
        """
        Get current access token, refreshing if needed.

        Returns:
            Valid OAuth 2.0 access token

        Raises:
            NetSuiteConnectionError: If token request fails
        """
        if self.token is None or self.token.is_expired():
            self._request_new_token()

        assert self.token is not None  # For type checker
        return self.token.access_token

    def _request_new_token(self) -> None:
        """
        Request new OAuth 2.0 access token.

        Raises:
            NetSuiteConnectionError: If request fails
        """
        try:
            response = httpx.post(
                self.oauth_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.settings.ns_client_id,
                    "client_secret": self.settings.ns_client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise NetSuiteConnectionError(
                f"Failed to obtain OAuth 2.0 token: {e}"
            ) from e

        data = response.json()

        self.token = OAuth2Token(
            access_token=data["access_token"],
            token_type=data["token_type"],
            expires_at=datetime.now() + timedelta(seconds=data["expires_in"]),
        )

    def get_auth_headers(self) -> dict[str, str]:
        """
        Get authorization headers for API requests.

        Returns:
            Dictionary with Authorization header
        """
        return {"Authorization": f"Bearer {self.get_access_token()}"}
