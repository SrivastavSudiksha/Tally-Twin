from sqlalchemy import create_engine, text

from sqlalchemy.orm import sessionmaker, Session

from typing import Generator

import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)

def _build_engine():

    settings = get_settings()

    url = settings.DATABASE_URL

    connect_args = {}

    is_sqlite = url.startswith("sqlite")

    if is_sqlite:

        connect_args = {"check_same_thread": False}

    kwargs = {

        "connect_args": connect_args,

        "pool_pre_ping": True,

        "echo": settings.DEBUG and not settings.is_production,

    }

    if not is_sqlite:

        kwargs["pool_size"] = settings.DB_POOL_SIZE

        kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW

        kwargs["pool_recycle"] = settings.DB_POOL_RECYCLE

    return create_engine(url, **kwargs)

engine = _build_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:

    """FastAPI dependency – yields a DB session and closes it after request."""

    db = SessionLocal()

    try:

        yield db

    finally:

        db.close()

def check_db_connection() -> bool:

    """Return True if DB is reachable."""

    try:

        with engine.connect() as conn:

            conn.execute(text("SELECT 1"))

        return True

    except Exception as e:

        logger.error("Database health check failed: %s", e)

        return False

