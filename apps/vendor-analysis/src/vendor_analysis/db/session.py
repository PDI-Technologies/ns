"""Database session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from vendor_analysis.core.config import Settings, get_logger
from vendor_analysis.core.exceptions import DatabaseError
from vendor_analysis.db.models import Base


def create_db_engine(settings: Settings):
    """
    Create SQLAlchemy engine from settings.

    Args:
        settings: Application settings

    Returns:
        SQLAlchemy engine
    """
    return create_engine(settings.database_url, echo=False, future=True)


def init_database(settings: Settings, drop_existing: bool = False) -> None:
    """
    Initialize database schema (create all tables).

    Args:
        settings: Application settings
        drop_existing: If True, drop all existing tables before creating (WARNING: data loss)

    Raises:
        DatabaseError: If schema creation fails
    """
    logger = get_logger()
    try:
        engine = create_db_engine(settings)

        if drop_existing:
            logger.warning("Dropping all existing tables (data will be lost)")
            Base.metadata.drop_all(engine)
            logger.info("All tables dropped successfully")

        logger.info("Creating database schema")
        Base.metadata.create_all(engine)
        logger.info("Database schema initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise DatabaseError(f"Failed to initialize database: {e}") from e


def get_session(settings: Settings) -> Session:
    """
    Get database session.

    Args:
        settings: Application settings

    Returns:
        SQLAlchemy session

    Raises:
        DatabaseError: If session creation fails
    """
    logger = get_logger()
    try:
        logger.debug("Creating database session")
        engine = create_db_engine(settings)
        session_factory = sessionmaker(bind=engine)
        session = session_factory()
        logger.debug("Database session created successfully")
        return session
    except Exception as e:
        logger.error(f"Failed to create database session: {e}")
        raise DatabaseError(f"Failed to create database session: {e}") from e
