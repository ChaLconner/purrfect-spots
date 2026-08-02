import os
from collections.abc import AsyncGenerator

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import config
from app.logger import logger


def _positive_int_env(name: str, default: int, *, minimum: int = 0) -> int:
    """Read bounded pool settings without crashing on malformed deployment env."""
    try:
        return max(minimum, int(os.getenv(name, str(default))))
    except (TypeError, ValueError):
        logger.warning("Invalid %s; using default %s", name, default)
        return default


# Create Async Engine
db_available = False
engine = None

if config.DATABASE_URL:
    try:
        url = make_url(config.DATABASE_URL)
        if url.drivername in ("postgres", "postgresql"):
            url = url.set(drivername="postgresql+asyncpg")
        if url.host == "localhost":
            url = url.set(host="127.0.0.1")
        db_url = url.render_as_string(hide_password=False)

        engine = create_async_engine(
            db_url,
            echo=config.DEBUG,
            pool_size=_positive_int_env("DB_POOL_SIZE", 5, minimum=1),
            max_overflow=_positive_int_env("DB_MAX_OVERFLOW", 10),
            pool_pre_ping=True,
            pool_timeout=_positive_int_env("DB_POOL_TIMEOUT", 30, minimum=1),
            pool_recycle=_positive_int_env("DB_POOL_RECYCLE", 1800, minimum=60),
            connect_args={
                "timeout": _positive_int_env("DB_CONNECT_TIMEOUT", 15, minimum=1),
                "command_timeout": _positive_int_env("DB_COMMAND_TIMEOUT", 60, minimum=1),
                "prepared_statement_cache_size": 0,  # REQUIRED for Supabase transaction pooler
                "statement_cache_size": 0,  # Extra safety for some asyncpg versions
            },
        )
        db_available = True
        logger.info(
            "SQLAlchemy database engine created successfully (pool max=%s)",
            _positive_int_env("DB_POOL_SIZE", 5, minimum=1) + _positive_int_env("DB_MAX_OVERFLOW", 10),
        )
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
