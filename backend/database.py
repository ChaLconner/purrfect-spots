from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import config
from logger import logger

# Create Async Engine
# The pool_size and max_overflow should be tuned based on deployment needs
# connect_timeout prevents multi-minute hangs when the DB host is unreachable
db_available = False
engine = None  # type: ignore[assignment]

if config.DATABASE_URL:
    try:
        engine = create_async_engine(
            config.DATABASE_URL,
            echo=config.DEBUG,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_timeout=10,  # Wait max 10s for connection from pool
            pool_recycle=300,  # Recycle connections every 5 minutes
            connect_args={
                "timeout": 10,  # asyncpg connection timeout (seconds)
                "command_timeout": 30,  # Max time for any single command
            },
        )
        db_available = True
        logger.info("SQLAlchemy database engine created successfully")
    except Exception as e:
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
)  # type: ignore[assignment]


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

    try:
        async with AsyncSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()
    except Exception as e:
        logger.warning(f"Failed to acquire database session: {e}. Yielding None (Supabase fallback will be used).")
        yield None
