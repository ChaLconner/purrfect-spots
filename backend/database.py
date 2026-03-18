from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import config

# Create Async Engine
# The pool_size and max_overflow should be tuned based on deployment needs
engine = create_async_engine(
    config.DATABASE_URL,
    echo=config.DEBUG,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models"""

    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides an async database session.
    Ensures the session is closed after the request is finished.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
