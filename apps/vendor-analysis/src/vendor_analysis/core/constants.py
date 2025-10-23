"""Application constants - immutable values only."""

from typing import Final

# NetSuite API
NETSUITE_API_VERSION: Final[str] = "v1"
NETSUITE_BASE_URL_TEMPLATE: Final[str] = (
    "https://{account_id}.suitetalk.api.netsuite.com/services/rest/record/{version}"
)

# HTTP Methods - READ ONLY (enforced by design)
ALLOWED_HTTP_METHODS: Final[frozenset[str]] = frozenset(["GET"])

# All other configuration comes from config.yaml (fail if missing)
