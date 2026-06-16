"""Database availability probe and store selection.

Implements the offline-first ``db_available`` pattern: on startup we probe the
configured database with a short connect timeout; if reachable, runs and the
audit trail persist to PostgreSQL via :class:`DatabaseStore` and survive
restarts. If the database is unavailable — or its driver is not installed, the
offline-first default for tests and the demo — we transparently fall back to
:class:`InMemoryStore` so the service still runs with NO database.

The ``DatabaseManager`` (and thus the DB driver import) is built lazily inside
``check_db`` so merely importing this module never requires a Postgres driver.
"""

from typing import Optional

from loguru import logger
from sqlalchemy import text

from .config import AppConfig
from .store import DatabaseStore, InMemoryStore

config = AppConfig()

db_manager = None  # lazily constructed in check_db()
db_available: bool = False


def _get_manager():
    """Lazily build the shared DatabaseManager (imports the DB driver).

    For Postgres we rebuild the engine with a short ``connect_timeout`` so the
    availability probe fails fast instead of hanging when no database is running.
    """
    global db_manager
    if db_manager is None:
        from shared_core.database import DatabaseManager

        url = config.DATABASE_URL
        db_manager = DatabaseManager(
            url,
            pool_size=config.DB_POOL_SIZE,
            max_overflow=config.DB_MAX_OVERFLOW,
            pool_timeout=config.DB_POOL_TIMEOUT,
        )
        if url.startswith("postgresql"):
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker

            db_manager.engine = create_engine(
                url,
                pool_pre_ping=True,
                pool_size=config.DB_POOL_SIZE,
                max_overflow=config.DB_MAX_OVERFLOW,
                pool_timeout=config.DB_POOL_TIMEOUT,
                connect_args={"connect_timeout": config.DB_CONNECT_TIMEOUT},
            )
            db_manager.SessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=db_manager.engine
            )
    return db_manager


def check_db() -> bool:
    """Probe database connectivity and cache the result in ``db_available``.

    Returns ``False`` (and logs a warning) if the driver is missing or the
    database is unreachable, so callers fall back to the in-memory store.
    """
    global db_available
    try:
        manager = _get_manager()
        with manager.SessionLocal() as session:
            session.execute(text("SELECT 1"))
        manager.create_tables()
        db_available = True
        logger.info("Database connected — runs and audit will persist.")
    except Exception as exc:
        db_available = False
        logger.warning(
            "Database unavailable — falling back to in-memory store: {}", exc
        )
    return db_available


def build_store(in_memory_fallback: Optional[InMemoryStore] = None):
    """Return the active store based on the last probe result."""
    if db_available and db_manager is not None:
        return DatabaseStore(db_manager.get_session)
    return in_memory_fallback or InMemoryStore()
