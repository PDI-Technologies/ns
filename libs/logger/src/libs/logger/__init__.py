"""Shared logging library with rolling archives and custom formatting.

Public API:
    - get_logger: Create and configure a logger for an application
    - setup_module_logger: Get a logger for a specific module
    - load_logging_config: Load and validate logging configuration
    - LoggingConfig: Configuration schema
    - LoggingConfigError: Configuration error exception
"""

from libs.logger.config import LoggingConfig, load_logging_config
from libs.logger.exceptions import LoggingConfigError
from libs.logger.factory import get_logger, setup_module_logger

__all__ = [
    "get_logger",
    "setup_module_logger",
    "load_logging_config",
    "LoggingConfig",
    "LoggingConfigError",
]
