"""
Application constants.

Immutable values used throughout the application.
"""

from typing import Final

# HTTP Methods
ALLOWED_HTTP_METHODS: Final[frozenset[str]] = frozenset(["GET"])

# NetSuite API
NETSUITE_API_VERSION: Final[str] = "v1"
NETSUITE_BASE_URL_TEMPLATE: Final[str] = (
    "https://{account_id}.suitetalk.api.netsuite.com/services/rest/record/{version}"
)
NETSUITE_OAUTH_URL_TEMPLATE: Final[str] = (
    "https://{account_id}.suitetalk.api.netsuite.com/rest/oauth2/token"
)

# Database
DEFAULT_PAGE_SIZE: Final[int] = 100
DEFAULT_MAX_RETRIES: Final[int] = 3
DEFAULT_RETRY_DELAY: Final[int] = 2

# Analytics
DEFAULT_DUPLICATE_THRESHOLD: Final[float] = 0.85
DEFAULT_TOP_N_VENDORS: Final[int] = 25
DEFAULT_ANALYSIS_MONTHS: Final[int] = 12
