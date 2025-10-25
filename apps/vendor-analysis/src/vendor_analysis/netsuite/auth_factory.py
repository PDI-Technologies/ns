"""
Factory for creating authentication providers.

Selects appropriate auth method based on configuration.
"""

from vendor_analysis.core.config import Settings
from vendor_analysis.core.exceptions import ConfigurationError
from vendor_analysis.netsuite.auth import OAuth2AuthProvider
from vendor_analysis.netsuite.auth_base import NetSuiteAuthProvider
from vendor_analysis.netsuite.auth_tba import TBAAuthProvider


def create_auth_provider(settings: Settings) -> NetSuiteAuthProvider:
    """
    Create appropriate authentication provider based on configuration.

    Args:
        settings: Application settings

    Returns:
        Configured authentication provider

    Raises:
        ConfigurationError: If auth_method is invalid or required credentials missing
    """
    auth_method = settings.yaml_config.application.auth_method.lower()

    if auth_method == "tba":
        return TBAAuthProvider(settings)
    elif auth_method == "oauth2":
        return OAuth2AuthProvider(settings)
    else:
        raise ConfigurationError(
            f"Invalid auth_method '{auth_method}' in config.yaml. "
            f"Must be 'tba' or 'oauth2'."
        )
