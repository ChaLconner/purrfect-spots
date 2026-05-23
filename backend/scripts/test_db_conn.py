import asyncio

from sqlalchemy.ext.asyncio import create_async_engine

from config import config


async def test_conn() -> None:
    db_url = config.DATABASE_URL
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgresql://") and "+asyncpg" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    print(f"Testing connection to: {db_url.replace('postgres:', 'postgres:REDACTED@')}")
    engine = create_async_engine(db_url)
    try:
        async with engine.connect() as _:
            print("Successfully connected to database!")
    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_conn())
