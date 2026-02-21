import asyncio
import os

from dotenv import load_dotenv
from supabase import acreate_client

load_dotenv("../.env")


async def main():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        print("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
        return

    client = await acreate_client(url, key)
    try:
        res = await client.table("cat_photos").select("id", count="exact").limit(1).execute()
        print(f"Count: {res.count}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
