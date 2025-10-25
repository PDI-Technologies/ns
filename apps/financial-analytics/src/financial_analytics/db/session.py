"""
Database session management.

Following fail-fast discipline and vendor-analysis patterns.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from financial_analytics.core.config import Settings, get_logger
from financial_analytics.core.exceptions import DatabaseError
from financial_analytics.db.models import Base


def create_db_engine(database_url: str):
    """
    Create SQLAlchemy engine.

    Args:
        database_url: PostgreSQL connection URL

    Returns:
        SQLAlchemy engine
    """
    return create_engine(database_url, echo=False, future=True)


def get_session(settings: Settings) -> Session:
    """
    Get database session.

    Args:
        settings: Application settings

    Returns:
        SQLAlchemy session

    Raises:
        DatabaseError: If connection fails
    """
    logger = get_logger()
    try:
        logger.debug("Creating database session")
        engine = create_db_engine(settings.database_url)
        session_factory = sessionmaker(bind=engine)
        session = session_factory()
        logger.debug("Database session created successfully")
        return session
    except Exception as e:
        logger.error(f"Failed to create database session: {e}")
        raise DatabaseError(f"Failed to create database session: {e}") from e


def init_database(settings: Settings) -> None:
    """
    Initialize database schema (idempotent).

    Creates all tables if they don't exist.
    Safe to run multiple times.

    Args:
        settings: Application settings

    Raises:
        DatabaseError: If schema creation fails
    """
    logger = get_logger()
    try:
        logger.info("Initializing database schema")
        engine = create_db_engine(settings.database_url)
        Base.metadata.create_all(engine)
        logger.info("Database schema initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise DatabaseError(f"Failed to initialize database: {e}") from e
