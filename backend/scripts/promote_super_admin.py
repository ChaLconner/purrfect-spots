import asyncio
import os
import sys

# Add parent directory to path to import services/config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import Client, create_client

from config import config

# Initialize Supabase Client (Service Role for admin updates)
if not config.SUPABASE_SERVICE_KEY:
    print("Error: SUPABASE_SERVICE_KEY is missing in config.")
    sys.exit(1)

supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)

TARGET_EMAIL = "professional_fes@hotmail.com"
TARGET_ROLE = "super_admin"


async def promote_user():
    print(f"Promoting user {TARGET_EMAIL} to {TARGET_ROLE}...")

    # 1. Get Role ID for Super Admin
    role_res = supabase.table("roles").select("id").eq("name", TARGET_ROLE).execute()
    if not role_res.data:
        print(f"Error: Role '{TARGET_ROLE}' not found.")
        return

    role_id = role_res.data[0]["id"]
    print(f"Found Role ID: {role_id}")

    # 2. Get User ID by Email (This might work via auth API if enabled, or query users table directly)
    # Since we have a public.users table mirror, we query that.
    user_res = supabase.table("users").select("id").eq("email", TARGET_EMAIL).execute()

    if not user_res.data:
        print(f"Error: User with email '{TARGET_EMAIL}' not found in public.users table.")
        print("Please ensure you have registered this user via the frontend first.")
        return

    user_id = user_res.data[0]["id"]
    print(f"Found User ID: {user_id}")

    # 3. Update User Role
    try:
        update_res = (
            supabase.table("users")
            .update(
                {
                    "role_id": role_id
                    # "role": "super_admin" # Legacy field removed or not accessible
                }
            )
            .eq("id", user_id)
            .execute()
        )

        if update_res.data:
            print(f"Successfully promoted {TARGET_EMAIL} to {TARGET_ROLE}!")
        else:
            print("Update executed but no data returned (check RLS if using anon key, but we are using service key).")

    except Exception as e:
        print(f"Failed to update user: {e}")


if __name__ == "__main__":
    asyncio.run(promote_user())
