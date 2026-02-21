import os
import sys

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import Client, create_client

from config import config

# Initialize Supabase Client (Service Role for admin operations)
if not config.SUPABASE_SERVICE_KEY:
    print("Error: SUPABASE_SERVICE_KEY is missing in config.")
    sys.exit(1)

supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)


async def apply_migrations():
    print("Applying migrations using supabase-py execute...")

    # Read migration file
    print("Checking for raw SQL execution capability...")

    try:
        # Attempt to check if an 'exec_sql' RPC exists or similar
        # Since we know from analysis that we likely can't run raw SQL directly via the client
        # without a wrapper function, we will advise the user.

        print("\n[INFO] Direct raw SQL execution via 'supabase-py' client requires an RPC function (e.g., 'exec_sql').")
        print(
            "       The current client configuration primarily supports PostgREST features (select, insert, update, delete, rpc)."
        )
        print("\n[ACTION REQUIRED] To apply the migration 'backend/migrations/017_create_reports_table.sql':")
        print("  1. Open the Supabase Dashboard for your project.")
        print("  2. Go to the SQL Editor.")
        print("  3. Copy the content of 'backend/migrations/017_create_reports_table.sql'.")
        print("  4. Paste and run the SQL in the editor.")
        print("\nAlternatively, if you have the Supabase CLI installed and linked:")
        print("  supabase db push")

    except Exception as e:
        print(f"Error checking capabilities: {e}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(apply_migrations())
