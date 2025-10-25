"""
NetSuite Token-Based Authentication (TBA) - OAuth 1.0.

DEPRECATED: TBA will be removed in February 2025.
Use OAuth 2.0 for new integrations.
"""

import hashlib
import hmac
import secrets
import time
from urllib.parse import quote, urlparse

from vendor_analysis.core.config import Settings
from vendor_analysis.netsuite.auth_base import NetSuiteAuthProvider


class TBAAuthProvider(NetSuiteAuthProvider):
    """Token-Based Authentication (OAuth 1.0) provider."""

    def __init__(self, settings: Settings) -> None:
        """Initialize TBA auth provider with settings."""
        self.settings = settings

    def get_auth_headers(self, url: str, method: str = "GET") -> dict[str, str]:
        """
        Get OAuth 1.0 authorization headers for API requests.

        Args:
            url: Full request URL
            method: HTTP method (GET, POST, etc.)

        Returns:
            Dictionary with Authorization header containing OAuth 1.0 signature

        Raises:
            NetSuiteConnectionError: If signature generation fails
        """
        # Generate OAuth 1.0 parameters
        timestamp = str(int(time.time()))
        nonce = secrets.token_hex(16)

        # Build OAuth parameters
        oauth_params = {
            "oauth_consumer_key": self.settings.ns_consumer_key,
            "oauth_token": self.settings.ns_token_id,
            "oauth_signature_method": "HMAC-SHA256",
            "oauth_timestamp": timestamp,
            "oauth_nonce": nonce,
            "oauth_version": "1.0",
        }

        # Generate signature
        signature = self._generate_signature(url, method, oauth_params)
        oauth_params["oauth_signature"] = signature

        # Build Authorization header
        auth_header = self._build_auth_header(oauth_params)

        return {"Authorization": auth_header}

    def _generate_signature(
        self, url: str, method: str, oauth_params: dict[str, str]
    ) -> str:
        """
        Generate OAuth 1.0 HMAC-SHA256 signature.

        Args:
            url: Request URL
            method: HTTP method
            oauth_params: OAuth parameters

        Returns:
            Base64-encoded signature
        """
        # Extract base URL and query parameters
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"

        # Combine OAuth params with query string params
        all_params = dict(oauth_params)
        if parsed_url.query:
            from urllib.parse import parse_qsl

            query_params = parse_qsl(parsed_url.query)
            # Ensure all values are strings
            all_params.update({k: str(v) for k, v in query_params})

        # Build parameter string (sorted alphabetically)
        params = sorted(all_params.items())
        param_string = "&".join(
            f"{quote(str(k), safe='')}={quote(str(v), safe='')}" for k, v in params
        )

        # Build signature base string
        base_string = "&".join(
            [
                method.upper(),
                quote(base_url, safe=""),
                quote(param_string, safe=""),
            ]
        )

        # Build signing key
        signing_key = "&".join(
            [
                quote(self.settings.ns_consumer_secret, safe=""),
                quote(self.settings.ns_token_secret, safe=""),
            ]
        )

        # Generate HMAC-SHA256 signature
        signature_bytes = hmac.new(
            signing_key.encode("utf-8"),
            base_string.encode("utf-8"),
            hashlib.sha256,
        ).digest()

        # Base64 encode
        import base64

        return base64.b64encode(signature_bytes).decode("utf-8")

    def _build_auth_header(self, oauth_params: dict[str, str]) -> str:
        """
        Build OAuth 1.0 Authorization header.

        Args:
            oauth_params: OAuth parameters including signature

        Returns:
            Authorization header value
        """
        realm = self.settings.ns_account_id
        auth_parts = [f'OAuth realm="{realm}"']

        for key, value in sorted(oauth_params.items()):
            encoded_value = quote(value, safe="")
            auth_parts.append(f'{key}="{encoded_value}"')

        return ", ".join(auth_parts)
