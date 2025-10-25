"""
NetSuite authentication abstraction.

Provides a common interface for different authentication methods.
"""

from abc import ABC, abstractmethod


class NetSuiteAuthProvider(ABC):
    """Abstract base class for NetSuite authentication providers."""

    @abstractmethod
    def get_auth_headers(self, url: str, method: str = "GET") -> dict[str, str]:
        """
        Get authorization headers for API requests.

        Args:
            url: Full request URL
            method: HTTP method (GET, POST, etc.)

        Returns:
            Dictionary with authorization headers

        Raises:
            NetSuiteConnectionError: If authentication fails
        """
        pass
