import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.supabase_client import get_supabase_admin_client

async def cleanup_roles():
    admin = get_supabase_admin_client()
    
    # 1. Fetch all roles
    roles_res = admin.table("roles").select("*").execute()
    all_roles = roles_res.data
    print(f"Found {len(all_roles)} roles.")
    
    # Map roles by normalized name
    role_map = {}
    for r in all_roles:
        norm_name = r["name"].lower().replace(" ", "_")
        if norm_name == "super_admin": norm_name = "admin" # Normalize admin
        
        if norm_name not in role_map:
            role_map[norm_name] = []
        role_map[norm_name].append(r)

    # 2. Pick survivors and migrate users
    survivors = {} # name -> role_obj
    
    # Ensure we have 'admin' and 'user' survivors
    for name in ["admin", "user"]:
        # Find any role that matches this name (or super_admin for admin)
        options = role_map.get(name, [])
        if name == "admin":
            options.extend(role_map.get("super_admin", []))
            # Remove duplicates from super_admin list if any
            unique_options = []
            seen_ids = set()
            for o in options:
                if o["id"] not in seen_ids:
                    unique_options.append(o)
                    seen_ids.add(o["id"])
            options = unique_options

        if not options:
            print(f"Mandatory role '{name}' not found. Creating it later or pick any.")
            continue
            
        survivor = options[0]
        survivors[name] = survivor
        print(f"Survivor for {name}: {survivor['name']} ({survivor['id']})")
        
        # Migrate all users from other options to this survivor
        for other in options[1:]:
            print(f"Migrating users from {other['name']} to survivor {survivor['name']}")
            admin.table("users").update({"role_id": survivor["id"]}).eq("role_id", other["id"]).execute()

    # 3. Handle 'moderator' or others - migrate to 'user'
    user_survivor = survivors.get("user")
    if user_survivor:
        for name, roles in role_map.items():
            if name not in ["admin", "user", "super_admin"]:
                for r in roles:
                    print(f"Migrating users from {r['name']} (unwanted role) to user survivor")
                    admin.table("users").update({"role_id": user_survivor["id"]}).eq("role_id", r["id"]).execute()

    # 4. Delete non-survivors
    survivor_ids = [s["id"] for s in survivors.values()]
    for r in all_roles:
        if r["id"] not in survivor_ids:
            print(f"Deleting role {r['name']} ({r['id']})")
            # Clear role_permissions first to avoid FK errors
            admin.table("role_permissions").delete().eq("role_id", r["id"]).execute()
            admin.table("roles").delete().eq("id", r["id"]).execute()

    # 5. Final Rename
    for name, survivor in survivors.items():
        if survivor["name"] != name:
            print(f"Renaming {survivor['name']} to {name}")
            admin.table("roles").update({"name": name}).eq("id", survivor["id"]).execute()

    print("Cleanup successful!")

if __name__ == "__main__":
    asyncio.run(cleanup_roles())
