
import asyncio
import os
import sys

# Add parent directory to path to import services/config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client, Client
from config import config

# Initialize Supabase Client (Service Role for seeding)
# Check if service role key exists, otherwise warn
if not config.SUPABASE_SERVICE_KEY:
    print("Error: SUPABASE_SERVICE_KEY is missing in config.")
    sys.exit(1)

supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)

# Initial Data Definitions
INITIAL_ROLES = [
    {
        "name": "Super Admin",
        "description": "Full access to all system features",
        "is_system": True
    },
    {
        "name": "User",
        "description": "Standard user access",
        "is_system": True
    },
    {
        "name": "Moderator",
        "description": "Can manage content and users",
        "is_system": False
    }
]

INITIAL_PERMISSIONS = [
    # User Management
    {"code": "users:read", "group": "User Management", "description": "View user list and details"},
    {"code": "users:create", "group": "User Management", "description": "Create new users"},
    {"code": "users:update", "group": "User Management", "description": "Edit user details"},
    {"code": "users:delete", "group": "User Management", "description": "Delete users"},
    {"code": "users:ban", "group": "User Management", "description": "Ban/Unban users"},
    
    # Role Management
    {"code": "roles:read", "group": "Role Management", "description": "View roles"},
    {"code": "roles:manage", "group": "Role Management", "description": "Create/Edit/Delete roles"},
    
    # Content Management
    {"code": "content:read", "group": "Content Management", "description": "View all content"},
    {"code": "content:delete", "group": "Content Management", "description": "Delete any content"},
    
    # System
    {"code": "system:audit_logs", "group": "System", "description": "View audit logs"},
    {"code": "system:config", "group": "System", "description": "Manage system configurations"},
]

ROLE_PERMISSION_MAPPING = {
    "Super Admin": ["*"], # * means all permissions
    "Moderator": ["users:read", "users:ban", "content:read", "content:delete"],
    "User": [] # Basic users have no admin permissions
}

async def seed_data():
    print("Starting database seeding...")

    # 1. Seed Permissions
    print("Seeding Permissions...")
    permission_map = {} # code -> id
    
    for perm in INITIAL_PERMISSIONS:
        try:
            # Upsert permission
            res = supabase.table("permissions").upsert(
                perm, on_conflict="code"
            ).execute()
            if res.data:
                permission_map[perm["code"]] = res.data[0]["id"]
        except Exception as e:
            print(f"Error seeding permission {perm['code']}: {e}")

    # 2. Seed Roles
    print("Seeding Roles...")
    role_map = {} # name -> id

    for role in INITIAL_ROLES:
        try:
            # Upsert role
            res = supabase.table("roles").upsert(
                role, on_conflict="name"
            ).execute()
            if res.data:
                role_map[role["name"]] = res.data[0]["id"]
        except Exception as e:
            print(f"Error seeding role {role['name']}: {e}")

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
            role_permissions_to_insert.append({
                "role_id": role_id,
                "permission_id": pid
            })

    if role_permissions_to_insert:
        try:
            # Bulk insert (ignore duplicates if possible via separate logic or try/except per batch)
            # Supabase upsert requires unique constraint on (role_id, permission_id) which we created
            res = supabase.table("role_permissions").upsert(
                 role_permissions_to_insert, on_conflict="role_id, permission_id"
             ).execute()
            print(f"Assigned permissions to roles successfully.")
        except Exception as e:
             print(f"Error assigning permissions: {e}")

    print("Seeding completed successfully!")

if __name__ == "__main__":
    asyncio.run(seed_data())
