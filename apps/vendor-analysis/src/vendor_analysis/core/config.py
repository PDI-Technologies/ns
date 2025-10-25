"""
Application configuration using pydantic-settings.

Loads from config.yaml and .env files.
FAIL-FAST: No defaults, no fallbacks - missing config = application fails.
"""

from pathlib import Path
from typing import Any

import logging

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from libs.logger import LoggingConfig, get_logger as create_logger, load_logging_config
from vendor_analysis.core.exceptions import ConfigurationError


class DatabaseConfig(BaseModel):
    """Database configuration from YAML."""

    host: str
    port: int
    name: str


class ApplicationConfig(BaseModel):
    """Application settings from YAML."""

    auth_method: str = Field(
        ...,
        description="Authentication method: 'tba' or 'oauth2'",
        pattern="^(tba|oauth2)$",
    )


class AnalysisConfig(BaseModel):
    """Analysis configuration from YAML."""

    duplicate_similarity_threshold: float
    trend_analysis_months: int
    top_vendors_default: int
    batch_size: int  # SuiteQL batch size for efficient bulk queries
    max_retries: int
    retry_delay_seconds: int


class YAMLConfig(BaseModel):
    """Complete YAML configuration structure."""

    database: DatabaseConfig
    application: ApplicationConfig
    logging: dict[str, Any]  # Raw logging config (will be validated by libs.logger)
    analysis: AnalysisConfig


def load_yaml_config(config_path: Path) -> YAMLConfig:
    """
    Load and validate YAML configuration.

    Args:
        config_path: Path to config.yaml

    Returns:
        Validated YAML configuration

    Raises:
        ConfigurationError: If config file missing or invalid
    """
    if not config_path.exists():
        raise ConfigurationError(
            f"Configuration file not found: {config_path}\n"
            f"Create config.yaml with required settings."
        )

    try:
        with open(config_path) as f:
            yaml_data = yaml.safe_load(f)
    except Exception as e:
        raise ConfigurationError(f"Failed to load config.yaml: {e}") from e

    try:
        return YAMLConfig(**yaml_data)
    except Exception as e:
        raise ConfigurationError(f"Invalid configuration in config.yaml: {e}") from e


class Settings(BaseSettings):
    """
    Application settings from .env and config.yaml.

    FAIL-FAST: All credentials are REQUIRED from .env
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # Allow NS_ACCOUNT_ID to match ns_account_id
        extra="ignore",
    )

    # NetSuite credentials (REQUIRED from .env as NS_ACCOUNT_ID, etc.)
    ns_account_id: str = Field(..., description="NetSuite account ID")
    ns_consumer_key: str = Field(..., description="Consumer key (from integration record)")
    ns_consumer_secret: str = Field(
        ..., description="Consumer secret (from integration record)"
    )
    ns_token_id: str = Field(..., description="Token ID (from access token)")
    ns_token_secret: str = Field(..., description="Token secret (from access token)")

    # Database credentials (REQUIRED from .env as DB_USER, DB_PASSWORD)
    db_user: str = Field(..., description="Database user")
    db_password: str = Field(..., description="Database password")

    # YAML config (loaded separately)
    _yaml_config: YAMLConfig | None = None

    @field_validator(
        "ns_account_id",
        "ns_consumer_key",
        "ns_consumer_secret",
        "ns_token_id",
        "ns_token_secret",
        mode="before",
    )
    @classmethod
    def validate_required_env(cls, v: Any, info: Any) -> str:
        """Ensure required environment variables are set."""
        if not v:
            raise ConfigurationError(
                f"{info.field_name} is required in .env file but was not found or is empty"
            )
        return str(v)

    @property
    def yaml_config(self) -> YAMLConfig:
        """
        Get YAML configuration (lazy loaded).

        Raises:
            ConfigurationError: If config.yaml missing or invalid
        """
        if self._yaml_config is None:
            config_path = Path("config.yaml")
            self._yaml_config = load_yaml_config(config_path)
        return self._yaml_config

    @property
    def database_url(self) -> str:
        """PostgreSQL connection URL from .env + config.yaml."""
        db_config = self.yaml_config.database
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{db_config.host}:{db_config.port}/{db_config.name}"
        )

    @property
    def duplicate_threshold(self) -> float:
        """Duplicate similarity threshold from config.yaml."""
        return self.yaml_config.analysis.duplicate_similarity_threshold

    @property
    def trend_months(self) -> int:
        """Trend analysis months from config.yaml."""
        return self.yaml_config.analysis.trend_analysis_months

    @property
    def top_vendors_count(self) -> int:
        """Default top vendors count from config.yaml."""
        return self.yaml_config.analysis.top_vendors_default

    @property
    def batch_size(self) -> int:
        """NetSuite SuiteQL batch size from config.yaml."""
        return self.yaml_config.analysis.batch_size

    @property
    def max_retries(self) -> int:
        """Max API retries from config.yaml."""
        return self.yaml_config.analysis.max_retries

    @property
    def retry_delay(self) -> int:
        """Retry delay seconds from config.yaml."""
        return self.yaml_config.analysis.retry_delay_seconds


# Global logger instance
_app_logger: logging.Logger | None = None


def get_settings() -> Settings:
    """
    Get validated application settings.

    Raises:
        ConfigurationError: If .env or config.yaml missing/invalid
    """
    return Settings()  # type: ignore[call-arg]


def get_logger() -> logging.Logger:
    """
    Get application logger (singleton).

    Returns:
        Configured logger instance

    Raises:
        ConfigurationError: If logger not initialized
    """
    if _app_logger is None:
        raise ConfigurationError(
            "Logger not initialized. Call initialize_logger() first."
        )
    return _app_logger


def initialize_logger() -> logging.Logger:
    """
    Initialize application logger from config.yaml.

    Returns:
        Configured logger instance

    Raises:
        ConfigurationError: If config.yaml missing or invalid
    """
    global _app_logger

    if _app_logger is not None:
        return _app_logger

    # Load config
    config_path = Path("config.yaml")
    if not config_path.exists():
        raise ConfigurationError(
            f"Configuration file not found: {config_path}\n"
            f"Create config.yaml with required settings."
        )

    try:
        with open(config_path) as f:
            config_dict = yaml.safe_load(f)
    except Exception as e:
        raise ConfigurationError(f"Failed to load config.yaml: {e}") from e

    # Load logging config and create logger
    try:
        logging_config = load_logging_config(config_dict)
        _app_logger = create_logger("vendor-analysis", logging_config)
        return _app_logger
    except Exception as e:
        raise ConfigurationError(f"Failed to initialize logger: {e}") from e
