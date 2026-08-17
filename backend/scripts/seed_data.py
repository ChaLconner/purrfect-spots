import contextlib
import os
import random
from pathlib import Path
from typing import Any, cast

from dotenv import load_dotenv
from faker import Faker
from supabase import Client, create_client

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Initialize Supabase
url = os.environ.get("SUPABASE_URL", "")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

if not url or not key:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(url, key)
fake = Faker()


def _load_seed_users() -> list[dict[str, Any]]:
    users: list[dict[str, Any]] = []
    for _ in range(5):
        # Note: We can't set passwords directly via Supabase client easily for auth schema,
        # so we'll just insert into public.users for now to simulate existence.
        # Ideally, we'd use supabase.auth.admin.create_user if we wanted login capability.
        # For this seed script, we'll insert into public.users directly to link with other tables.

        # However, public.users usually references auth.users via foreign key trigger.
        # If triggers are strict, we might fail.
        # But based on typical Supabase setups, inserts to public.users directly might fail if ID doesn't exist in auth.users.
        # Let's try creating via auth admin if possible, or just mock data if RLS allows.

        # Actually, let's just create "mock" records in public.users if we have permissions (Service Role).
        # We'll generate a random UUID.

        # IMPORTANT: If your public.users table has a foreign key to auth.users that is strictly enforced,
        # this simple insert will fail unless we also insert into auth.users.
        # For a simple seed script, we will try to use existing users if any, or create fake ones assuming no strict FK constraint or using a workaround.

        # Let's try to fetch existing users first to be safe.
        existing_users = supabase.table("users").select("id").limit(10).execute()
        if existing_users.data:
            users.extend(cast(list[dict[str, Any]], existing_users.data))
        else:
            # Fallback: Try to insert dummy users directly (might fail on FK)
            # Better approach: Create a user via Auth API if we were doing a full integration seed.
            # For now, let's assume we have some users or we can't seed properly without them.
            print("⚠️ No existing users found. Please register a user via the app first for best results.")
            return []
    return users


def _create_seed_photos(users: list[dict[str, Any]]) -> list[dict[str, Any]]:
    print("Creating cat photos...")
    photos: list[dict[str, Any]] = []
    cat_images = [
        "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba",
        "https://images.unsplash.com/photo-1573865526739-10659fec78a5",
        "https://images.unsplash.com/photo-1495360019602-e001922271aa",
        "https://images.unsplash.com/photo-1511044568932-338cba0fb803",
        "https://images.unsplash.com/photo-1519052537078-e6302a4968ef",
    ]
    for _i in range(10):
        owner = random.choice(users)  # NOSONAR python:S2245 - PRNG for fake seed data only
        photo_data = {
            "user_id": owner["id"],
            "url": random.choice(cat_images),  # NOSONAR python:S2245
            "description": fake.text(),
            "latitude": float(fake.latitude()) % 2 + 13.0,
            "longitude": float(fake.longitude()) % 2 + 100.0,
            "image_url": random.choice(cat_images),  # NOSONAR python:S2245 - PRNG for fake seed data only
            "location_name": fake.city(),
        }
        del photo_data["url"]
        res = supabase.table("cat_photos").insert(photo_data).execute()
        if res.data:
            photos.append(cast(dict[str, Any], res.data[0]))
    print(f"Created {len(photos)} photos.")
    return photos


def _create_seed_interactions(photos: list[dict[str, Any]], users: list[dict[str, Any]]) -> None:
    print("Creating interactions...")
    for photo in photos:
        for _ in range(random.randint(0, 5)):  # NOSONAR python:S2245
            actor = random.choice(users)  # NOSONAR python:S2245
            with contextlib.suppress(Exception):
                supabase.table("photo_likes").insert({"user_id": actor["id"], "photo_id": photo["id"]}).execute()

        for _ in range(random.randint(0, 3)):  # NOSONAR python:S2245
            if not users:
                continue
            actor = random.choice(users)  # NOSONAR python:S2245
            supabase.table("photo_comments").insert(
                {"user_id": actor["id"], "photo_id": photo["id"], "content": fake.sentence()}
            ).execute()


def seed_data() -> None:
    print("🌱 Starting data seeding...")

    users = _load_seed_users()
    if not users:
        return

    print(f"Found {len(users)} users to act as actors.")
    _create_seed_interactions(_create_seed_photos(users), users)
    print("✅ Seed data inserted successfully!")


if __name__ == "__main__":
    seed_data()
