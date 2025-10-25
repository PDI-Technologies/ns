"""
Configuration management with dual-source pattern.

Credentials from .env, settings from config.yaml.
Follows fail-fast discipline - missing config causes immediate failure.
"""

import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from financial_analytics.core.exceptions import ConfigurationError
from libs.logger import get_logger as create_logger, load_logging_config


class DatabaseConfig(BaseModel):
    """Database configuration from config.yaml."""

    host: str
    port: int
    name: str


class NetSuiteConfig(BaseModel):
    """NetSuite configuration from config.yaml."""

    account_id: str
    base_url: str | None = None


class SalesforceConfig(BaseModel):
    """Salesforce configuration from config.yaml."""

    enabled: bool = False


class AnalyticsConfig(BaseModel):
    """Analytics configuration from config.yaml."""

    default_period_months: int = 12
    vendor_analysis_top_n: int = 25
    duplicate_threshold: float = 0.85
    page_size: int = 100
    max_retries: int = 3
    retry_delay_seconds: int = 2


class YAMLConfig(BaseModel):
    """Complete YAML configuration structure."""

    database: DatabaseConfig
    netsuite: NetSuiteConfig
    salesforce: SalesforceConfig
    logging: dict[str, Any]  # Raw logging config (validated by libs.logger)
    analytics: AnalyticsConfig


def load_yaml_config(path: Path) -> YAMLConfig:
    """
    Load and validate YAML configuration.

    Args:
        path: Path to config.yaml file

    Returns:
        Validated YAMLConfig object

    Raises:
        ConfigurationError: If config file missing or invalid
    """
    if not path.exists():
        raise ConfigurationError(
            f"Configuration file not found: {path}\n"
            f"Create a config.yaml file in the application directory."
        )

    try:
        with open(path) as f:
            data: dict[str, Any] = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Invalid YAML in {path}: {e}") from e

    try:
        return YAMLConfig(**data)
    except Exception as e:
        raise ConfigurationError(f"Invalid configuration structure in {path}: {e}") from e


class Settings(BaseSettings):
    """
    Application settings from .env and config.yaml.

    Credentials come from .env (required).
    Application settings come from config.yaml (required).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    # NetSuite credentials (from .env)
    ns_client_id: str = Field(..., description="NetSuite OAuth 2.0 Consumer Key")
    ns_client_secret: str = Field(..., description="NetSuite OAuth 2.0 Consumer Secret")

    # Database credentials (from .env)
    db_user: str = Field(..., description="PostgreSQL username")
    db_password: str = Field(..., description="PostgreSQL password")

    # Optional Salesforce (from .env)
    sf_enabled: bool = Field(default=False, description="Enable Salesforce integration")

    # Internal state
    _yaml_config: YAMLConfig | None = None

    @property
    def yaml_config(self) -> YAMLConfig:
        """Lazy-load YAML configuration."""
        if self._yaml_config is None:
            config_path = Path("config.yaml")
            self._yaml_config = load_yaml_config(config_path)
        return self._yaml_config

    @property
    def database_url(self) -> str:
        """Build PostgreSQL connection URL."""
        db = self.yaml_config.database
        return f"postgresql://{self.db_user}:{self.db_password}@{db.host}:{db.port}/{db.name}"

    @property
    def ns_account_id(self) -> str:
        """NetSuite account ID from YAML config."""
        return self.yaml_config.netsuite.account_id

    @property
    def page_size(self) -> int:
        """Default page size for API calls."""
        return self.yaml_config.analytics.page_size

    @property
    def max_retries(self) -> int:
        """Maximum retry attempts for API calls."""
        return self.yaml_config.analytics.max_retries

    @property
    def retry_delay(self) -> int:
        """Delay in seconds between retries."""
        return self.yaml_config.analytics.retry_delay_seconds

    @property
    def duplicate_threshold(self) -> float:
        """Similarity threshold for duplicate detection."""
        return self.yaml_config.analytics.duplicate_threshold

    @property
    def top_n_vendors(self) -> int:
        """Default number of top vendors to show."""
        return self.yaml_config.analytics.vendor_analysis_top_n

    @property
    def analysis_months(self) -> int:
        """Default period for financial analysis (in months)."""
        return self.yaml_config.analytics.default_period_months


# Global logger instance
_app_logger: logging.Logger | None = None


def get_logger() -> logging.Logger:
    """
    Get application logger (singleton).

    Returns:
        Configured logger instance

    Raises:
        ConfigurationError: If logger not initialized
    """
    if _app_logger is None:
        raise ConfigurationError("Logger not initialized. Call initialize_logger() first.")
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
        _app_logger = create_logger("financial-analytics", logging_config)
        return _app_logger
    except Exception as e:
        raise ConfigurationError(f"Failed to initialize logger: {e}") from e
