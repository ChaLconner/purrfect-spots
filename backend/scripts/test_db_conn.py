import asyncio

from sqlalchemy.ext.asyncio import create_async_engine

from config import config


async def test_conn() -> None:
    print(f"Testing connection to: {config.DATABASE_URL.replace('postgres:', 'postgres:REDACTED@')}")
    engine = create_async_engine(config.DATABASE_URL)
    try:
        async with engine.connect() as _:
            print("Successfully connected to database!")
    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_conn())
