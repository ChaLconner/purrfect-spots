import datetime
from typing import List

from supabase import AClient

from utils.cache import cache


class SeoService:
    def __init__(self, supabase_client: AClient) -> None:
        self.supabase = supabase_client
        self.base_url = "https://purrfectspots.xyz"

    @cache(expire=3600, key_prefix="sitemap", skip_args=1)
    async def generate_sitemap(self) -> str:
        """Generate XML sitemap for the website."""
        urls = [
            (f"{self.base_url}/", "1.0"),
            (f"{self.base_url}/login", "0.8"),
            (f"{self.base_url}/register", "0.8"),
            (f"{self.base_url}/gallery", "0.9"),
            (f"{self.base_url}/leaderboard", "0.7"),
            (f"{self.base_url}/subscription", "0.8"),
        ]

        # Fetch dynamic routes
        # 1. Gallery Images
        photos = await self._get_all_photo_ids()
        for photo_id in photos:
            urls.append((f"{self.base_url}/gallery/{photo_id}", "0.8"))

        # 2. User Profiles
        users = await self._get_all_user_ids()
        for user_id in users:
            urls.append((f"{self.base_url}/profile/{user_id}", "0.6"))

        # Build XML
        xml = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

        today = datetime.date.today().isoformat()

        for loc, priority in urls:
            xml.append("  <url>")
            xml.append(f"    <loc>{loc}</loc>")
            xml.append(f"    <lastmod>{today}</lastmod>")
            xml.append("    <changefreq>daily</changefreq>")
            xml.append(f"    <priority>{priority}</priority>")
            xml.append("  </url>")

        xml.append("</urlset>")

        return "\n".join(xml)

    async def _get_all_photo_ids(self) -> List[str]:
        try:
            # Fetch visible photos, limit to most recent 1000 to avoid huge sitemap
            res = await self.supabase.table("cat_photos") \
                .select("id") \
                .is_("deleted_at", "null") \
                .order("uploaded_at", desc=True) \
                .limit(1000) \
                .execute()
                
            return [row["id"] for row in res.data]
        except Exception as e:
            print(f"Sitemap photo fetch error: {e}")
            return []

    async def _get_all_user_ids(self) -> List[str]:
        try:
            # Fetch active users
            res = await self.supabase.table("users").select("id").limit(1000).execute()
            return [row["id"] for row in res.data]
        except Exception as e:
            print(f"Sitemap user fetch error: {e}")
            return []
