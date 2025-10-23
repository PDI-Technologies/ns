"""
NetSuite OAuth 2.0 authentication (Client Credentials flow).

Handles token acquisition, caching, and refresh.
"""

import time
from dataclasses import dataclass
from typing import Final

import httpx

from vendor_analysis.core.config import Settings
from vendor_analysis.core.exceptions import NetSuiteConnectionError


@dataclass
class OAuth2Token:
    """OAuth 2.0 access token with expiration."""

    access_token: str
    token_type: str
    expires_at: float  # Unix timestamp

    @property
    def is_expired(self) -> bool:
        """Check if token is expired (with 60s buffer)."""
        return time.time() >= (self.expires_at - 60)


class NetSuiteAuth:
    """Manages NetSuite OAuth 2.0 authentication."""

    TOKEN_ENDPOINT: Final[str] = (
        "https://{account_id}.suitetalk.api.netsuite.com/services/rest/auth/oauth2/v1/token"
    )

    def __init__(self, settings: Settings) -> None:
        """Initialize auth manager with settings."""
        self.settings = settings
        self._token: OAuth2Token | None = None

    def get_access_token(self) -> str:
        """
        Get valid access token, refreshing if needed.

        Returns:
            Valid access token string

        Raises:
            NetSuiteConnectionError: If token acquisition fails
        """
        if self._token is None or self._token.is_expired:
            self._token = self._request_new_token()

        return self._token.access_token

    def _request_new_token(self) -> OAuth2Token:
        """
        Request new OAuth 2.0 access token using client credentials.

        Returns:
            New OAuth2Token

        Raises:
            NetSuiteConnectionError: If token request fails
        """
        url = self.TOKEN_ENDPOINT.format(account_id=self.settings.ns_account_id)

        data = {
            "grant_type": "client_credentials",
            "client_id": self.settings.ns_client_id,
            "client_secret": self.settings.ns_client_secret,
        }

        try:
            response = httpx.post(
                url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise NetSuiteConnectionError(
                f"Failed to obtain OAuth 2.0 token: {e}"
            ) from e

        token_data = response.json()

        return OAuth2Token(
            access_token=token_data["access_token"],
            token_type=token_data["token_type"],
            expires_at=time.time() + token_data["expires_in"],
        )

    def get_auth_headers(self) -> dict[str, str]:
        """
        Get authorization headers for API requests.

        Returns:
            Dictionary with Authorization header
        """
        token = self.get_access_token()
        return {"Authorization": f"Bearer {token}"}
