import datetime
from typing import Any

from postgrest.types import CountMethod
from supabase import AClient

from config import config
from logger import logger


class QuotaService:
    # Daily image upload limits
    FREE_LIMIT = config.QUOTA_FREE_LIMIT
    PRO_LIMIT = config.QUOTA_PRO_LIMIT
    GLOBAL_SYSTEM_LIMIT = 2000  # System-wide safety buffer

    def __init__(self, supabase: AClient) -> None:
        self.supabase: AClient = supabase

    async def get_recent_upload_count(self, user_id: str) -> int:
        """
        Efficiently count active uploads in the last 24 hours.
        Respects the 24-hour rolling window requirement.
        """
        # Calculate 24 hours ago in UTC
        now = datetime.datetime.now(datetime.UTC)
        twenty_four_hours_ago = (now - datetime.timedelta(hours=24)).isoformat()

        try:
            # Query the main photos table for accurate rolling window count
            res = (
                await self.supabase.table("cat_photos")
                .select("id", count=CountMethod.exact)
                .eq("user_id", user_id)
                .gt("uploaded_at", twenty_four_hours_ago)
                .is_("deleted_at", "null")
                .execute()
            )

            return res.count if hasattr(res, "count") and res.count is not None else 0
        except Exception as e:
            logger.error(f"Failed to fetch recent upload count for user {user_id}: {e}")
            # Fail closed for security - assume limit reached on error
            return 9999

    async def check_quota(self, user_id: str, is_pro: bool) -> bool:
        """
        Check if user has sufficient quota within the 24-hour rolling window.
        """
        max_quota = self.PRO_LIMIT if is_pro else self.FREE_LIMIT

        # 1. Check Global usage (System-wide daily limit)
        today = datetime.date.today().isoformat()
        try:
            sys_usage = (
                await self.supabase.table("system_daily_stats")
                .select("total_uploads")
                .eq("date", today)
                .maybe_single()
                .execute()
            )

            sys_total = sys_usage.data["total_uploads"] if sys_usage and sys_usage.data else 0
            if sys_total >= self.GLOBAL_SYSTEM_LIMIT:
                logger.critical(f"System Global Quota Reached: {sys_total}/{self.GLOBAL_SYSTEM_LIMIT}")
                return False
        except Exception as e:
            logger.error(f"Global quota check failed: {e}")

        # 2. Check User Rolling Quota
        usage_count = await self.get_recent_upload_count(user_id)

        if usage_count >= max_quota:
            logger.warning(f"User {user_id} hit rolling quota: {usage_count}/{max_quota}")
            return False

        return True

    async def check_and_increment(self, user_id: str, is_pro: bool) -> bool:
        """
        Check quota and perform analytics increment.
        Actual quota is enforced by the rolling window check against cat_photos.
        """
        if not await self.check_quota(user_id, is_pro):
            return False

        # Legacy Support: Continue tracking daily stats for dashboards
        await self.increment_usage(user_id)
        return True

    async def increment_usage(self, user_id: str) -> None:
        """Increment usage count for user and system via existing RPC for analytics."""
        today = datetime.date.today().isoformat()
        try:
            await self.supabase.rpc("increment_usage", {"p_user_id": user_id, "p_date": today}).execute()
        except Exception as e:
            logger.error(f"Failed to increment legacy quota for user {user_id}: {e}")

    async def get_user_quota_status(self, user_id: str, is_pro: bool) -> dict[str, Any]:
        """Get quota usage details for UI based on rolling window."""
        max_quota = self.PRO_LIMIT if is_pro else self.FREE_LIMIT

        try:
            used = await self.get_recent_upload_count(user_id)
            remaining = max(0, max_quota - used)

            return {
                "used": used,
                "limit": max_quota,
                "remaining": remaining,
                "is_pro": is_pro,
                "reset_type": "24h_rolling",
            }
        except Exception as e:
            logger.error(f"Failed to get quota status: {e}")
            return {"used": 0, "limit": max_quota, "remaining": 0, "error": True}
