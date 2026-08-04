import asyncio
import sys
from pathlib import Path
from typing import Any, cast

# Add parent directory to path to import services/config
sys.path.append(str(Path(__file__).parent.parent))

from app.config import config
from app.constants.admin_permissions import SYSTEM_ROLE_PERMISSION_CODES, canonical_permission_records
from app.utils.supabase_client import get_supabase_admin_client

# Initialize Supabase Client (Service Role for seeding)
# Check if service role key exists, otherwise warn
if not config.SUPABASE_SERVICE_KEY:
    print("Error: SUPABASE_SERVICE_KEY is missing in config.")
    sys.exit(1)

supabase = get_supabase_admin_client()

# Initial Data Definitions
INITIAL_ROLES = [
    {"name": "admin", "description": "Administrator with full access", "is_system": True},
    {"name": "super_admin", "description": "Super administrator with unrestricted access", "is_system": True},
    {"name": "moderator", "description": "Moderator with scoped admin permissions", "is_system": True},
    {"name": "user", "description": "Standard user access", "is_system": True},
]

INITIAL_PERMISSIONS = canonical_permission_records()

ROLE_PERMISSION_MAPPING = SYSTEM_ROLE_PERMISSION_CODES


async def seed_data() -> None:
    print("Starting database seeding...")

    # 1. Seed Permissions
    print("Seeding Permissions...")
    permission_map: dict[str, str] = {}  # code -> id

    for perm in INITIAL_PERMISSIONS:
        try:
            perm_record = cast(dict[str, Any], perm)
            # Upsert permission
            res = supabase.table("permissions").upsert(cast(Any, perm_record), on_conflict="code").execute()
            if res.data:
                rows = cast(list[dict[str, Any]], res.data)
                permission_map[cast(str, perm_record["code"])] = cast(str, rows[0]["id"])
        except Exception as e:
            print(f"Error seeding permission {perm_record['code']}: {e}")

    # 2. Seed Roles
    print("Seeding Roles...")
    role_map: dict[str, str] = {}  # name -> id

    for role in INITIAL_ROLES:
        try:
            role_record = cast(dict[str, Any], role)
            # Upsert role
            res = supabase.table("roles").upsert(cast(Any, role_record), on_conflict="name").execute()
            if res.data:
                rows = cast(list[dict[str, Any]], res.data)
                role_map[cast(str, role_record["name"])] = cast(str, rows[0]["id"])
        except Exception as e:
            print(f"Error seeding role {role_record['name']}: {e}")

    # 3. Assign Permissions to Roles
    print("Assigning Permissions to Roles...")
    role_permissions_to_insert = []

    # Get all permission IDs for wildcard
    all_perm_ids = list(permission_map.values())

    for role_name, perm_codes in ROLE_PERMISSION_MAPPING.items():
        role_id = role_map.get(role_name)
        if not role_id:
            continue

        target_perm_ids = []
        if "*" in perm_codes:
            target_perm_ids = all_perm_ids
        else:
            for code in perm_codes:
                if code in permission_map:
                    target_perm_ids.append(permission_map[code])

        for pid in target_perm_ids:
            role_permissions_to_insert.append({"role_id": role_id, "permission_id": pid})

    if role_permissions_to_insert:
        try:
            # Bulk insert (ignore duplicates if possible via separate logic or try/except per batch)
            # Supabase upsert requires unique constraint on (role_id, permission_id) which we created
            res = (
                supabase.table("role_permissions")
                .upsert(role_permissions_to_insert, on_conflict="role_id, permission_id")
                .execute()
            )
            print("Assigned permissions to roles successfully.")
        except Exception as e:
            print(f"Error assigning permissions: {e}")

    print("Seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed_data())
