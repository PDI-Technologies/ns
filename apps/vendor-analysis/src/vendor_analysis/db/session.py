"""Database session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from vendor_analysis.core.config import Settings
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


def init_database(settings: Settings) -> None:
    """
    Initialize database schema (create all tables).

    Args:
        settings: Application settings

    Raises:
        DatabaseError: If schema creation fails
    """
    try:
        engine = create_db_engine(settings)
        Base.metadata.create_all(engine)
    except Exception as e:
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
    try:
        engine = create_db_engine(settings)
        session_factory = sessionmaker(bind=engine)
        return session_factory()
    except Exception as e:
        raise DatabaseError(f"Failed to create database session: {e}") from e
