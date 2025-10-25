"""Logger factory for creating configured loggers."""

import logging

from libs.logger.config import LoggingConfig
from libs.logger.formatter import CustomFormatter
from libs.logger.handlers import ArchivingRotatingFileHandler


def get_logger(app_name: str, config: LoggingConfig) -> logging.Logger:
    """Create and configure a logger for the application.

    Args:
        app_name: Application name (used for log filename: {app_name}.log)
        config: Validated logging configuration

    Returns:
        Configured logger instance
    """
    # Get root logger for the application
    logger = logging.getLogger(app_name)
    logger.setLevel(config.level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create log file path: {file_path}/{app_name}.log
    log_file = config.get_file_path() / f"{app_name}.log"

    # Create archiving rotating file handler
    file_handler = ArchivingRotatingFileHandler(
        filename=log_file,
        archive_dir=config.get_archive_path(),
        max_bytes=config.get_max_bytes(),
        backup_count=10,  # Keep 10 archived files
    )

    # Set custom formatter
    formatter = CustomFormatter()
    file_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def setup_module_logger(module_name: str, config: LoggingConfig) -> logging.Logger:
    """Set up a logger for a specific module.

    This is useful for getting loggers in individual modules while using
    the same configuration.

    Args:
        module_name: Name of the module (typically __name__)
        config: Validated logging configuration

    Returns:
        Logger instance for the module
    """
    logger = logging.getLogger(module_name)
    logger.setLevel(config.level)
    return logger
