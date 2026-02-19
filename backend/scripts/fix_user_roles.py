import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.supabase_client import get_supabase_admin_client

async def fix_roles():
    admin = get_supabase_admin_client()
    
    # 1. Get roles
    roles_res = admin.table("roles").select("id, name").execute()
    roles = {r["name"]: r["id"] for r in roles_res.data}
    
    if "admin" not in roles or "user" not in roles:
        print("Required roles not found. Please run seed_admin_data.py first.")
        print(f"Current roles: {roles}")
        return

    # 2. Target admins
    admin_emails = [
        "chaluntonvipusanapas@gmail.com",
        "professional_fes@hotmail.com"
    ]
    
    print(f"Setting {admin_emails} as admin...")
    for email in admin_emails:
        admin.table("users").update({
            "role_id": roles["admin"]
        }).eq("email", email).execute()

    # 3. Set everyone else to user if they don't have a role
    print("Setting default role for others...")
    admin.table("users").update({
        "role_id": roles["user"]
    }).is_("role_id", "null").execute()
    
    print("Done!")

if __name__ == "__main__":
    asyncio.run(fix_roles())
