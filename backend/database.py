import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import config
from logger import logger

# Create Async Engine
# The pool_size and max_overflow should be tuned based on deployment needs
# connect_timeout prevents multi-minute hangs when the DB host is unreachable
db_available = False
engine = None

if config.DATABASE_URL:
    try:
        # Ensure the DATABASE_URL uses the asyncpg driver
        db_url = config.DATABASE_URL
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif db_url.startswith("postgresql://") and "+asyncpg" not in db_url:
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        # SECURITY/PERFORMANCE: Replace localhost with 127.0.0.1 to avoid [Errno 99] (IPv6 binding issues)
        # This is especially common in WSL2 environments where IPv6 loopback may not be configured.
        if "localhost" in db_url.lower():
            db_url = db_url.replace("localhost", "127.0.0.1")

        engine = create_async_engine(
            db_url,
            echo=config.DEBUG,
            pool_size=int(os.getenv("DB_POOL_SIZE", "1")),  # Vercel/lambda: 1. Locally: maybe more.
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "2")),
            pool_pre_ping=True,
            pool_timeout=30,  # Wait max 30s for connection from pool
            pool_recycle=300,  # Recycle connections every 5 minutes
            connect_args={
                "timeout": 15,  # asyncpg connection timeout (seconds)
                "command_timeout": 60,  # Max time for any single command
                "prepared_statement_cache_size": 0,  # REQUIRED for Supabase transaction pooler
                "statement_cache_size": 0,  # Extra safety for some asyncpg versions
            },
        )
        db_available = True
        logger.info("SQLAlchemy database engine created successfully")
    except Exception as e:
        if "Errno 99" in str(e) or "EADDRNOTAVAIL" in str(e):
            logger.warning(
                f"Database connection blocked: {e}. "
                "This usually happens when local ports are exhausted or IPv6 is misconfigured. "
                "Restarting your computer/server usually clears this state."
            )
        else:
            logger.warning(f"Failed to create database engine: {e}. Services will use Supabase client fallback.")
else:
    logger.info("DATABASE_URL not configured - using Supabase client API directly")

# Async Session Factory
AsyncSessionLocal = (
    async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    if engine is not None
    else None
)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models"""

    pass


async def get_db() -> AsyncGenerator[AsyncSession | None, None]:
    """
    FastAPI dependency that provides an async database session.
    Returns None if the database engine is not available.
    Ensures the session is closed after the request is finished.
    """
    if not db_available or AsyncSessionLocal is None:
        yield None
        return

    session_yielded = False
    try:
        async with AsyncSessionLocal() as session:
            session_yielded = True
            yield session
    except Exception as e:
        # If an exception occurs, we only yield None if we haven't already yielded a session.
        # This prevents the "generator didn't stop after athrow()" error in FastAPI.
        if not session_yielded:
            logger.warning(f"Failed to acquire database session: {e}. Falling back to Supabase client API.")
            yield None
        else:
            # Re-raise the exception so it can be handled by FastAPI's exception handlers
            # and properly trigger the session's __aexit__ (closing the session).
            raise
