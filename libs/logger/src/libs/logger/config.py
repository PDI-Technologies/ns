"""Logging configuration schema."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from libs.logger.exceptions import LoggingConfigError

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class LoggingConfig(BaseModel):
    """Logging configuration schema.

    All fields are required. Application will fail if any field is missing.
    """

    level: LogLevel = Field(
        ...,
        description="Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    file_path: str = Field(
        ...,
        description="Directory for active log files (relative to cwd)",
    )
    archive_path: str = Field(
        ...,
        description="Directory for archived log files",
    )
    max_size_mb: int = Field(
        ...,
        gt=0,
        description="Max log file size in MB before archiving",
    )

    @field_validator("file_path", "archive_path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Validate that path is not empty."""
        if not v or not v.strip():
            raise LoggingConfigError("Path cannot be empty")
        return v.strip()

    def get_file_path(self) -> Path:
        """Get file_path as Path object."""
        return Path(self.file_path)

    def get_archive_path(self) -> Path:
        """Get archive_path as Path object."""
        return Path(self.archive_path)

    def get_max_bytes(self) -> int:
        """Get max size in bytes."""
        return self.max_size_mb * 1024 * 1024


def load_logging_config(config_dict: dict[str, object]) -> LoggingConfig:
    """Load and validate logging configuration from config dictionary.

    Args:
        config_dict: Configuration dictionary from YAML file

    Returns:
        Validated LoggingConfig instance

    Raises:
        LoggingConfigError: If logging config is missing or invalid
    """
    if "logging" not in config_dict:
        raise LoggingConfigError(
            "Missing 'logging' section in config.yaml. "
            "Logging configuration is required."
        )

    logging_data = config_dict["logging"]
    if not isinstance(logging_data, dict):
        raise LoggingConfigError("'logging' section must be a dictionary")

    try:
        return LoggingConfig.model_validate(logging_data)
    except Exception as e:
        raise LoggingConfigError(f"Invalid logging configuration: {e}") from e
