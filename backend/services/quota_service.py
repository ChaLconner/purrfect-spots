import datetime
from typing import Any, cast

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from config import config
from logger import logger
from supabase import AClient


class QuotaService:
    # Daily image upload limits
    FREE_LIMIT = config.QUOTA_FREE_LIMIT
    PRO_LIMIT = config.QUOTA_PRO_LIMIT
    GLOBAL_SYSTEM_LIMIT = 2000  # System-wide safety buffer

    def __init__(self, supabase: AClient, db: AsyncSession | None = None) -> None:
        self.supabase: AClient = supabase
        self.db = db

    async def get_quota_usage(self, user_id: str) -> tuple[int, datetime.datetime | None]:
        """
        Calculates the number of used slots in the current 24h window.
        A window starts at the first upload and resets 24h later.
        Returns (used_count, window_start_time).
        """
        now = datetime.datetime.now(datetime.UTC)
        # We fetch last 48 hours to reliably find the transition into the current active window.
        since = now - datetime.timedelta(hours=48)

        try:
            if self.db:
                query = text(
                    "SELECT uploaded_at FROM cat_photos "
                    "WHERE user_id = :u_id "
                    "AND uploaded_at > :since "
                    "AND deleted_at IS NULL "
                    "ORDER BY uploaded_at ASC"
                )
                result = await self.db.execute(query, {"u_id": user_id, "since": since})
                rows = result.fetchall()
                timestamps = [row[0] for row in rows]
            else:
                res = (
                    await self.supabase.table("cat_photos")
                    .select("uploaded_at")
                    .eq("user_id", user_id)
                    .gt("uploaded_at", since.isoformat())
                    .is_("deleted_at", "null")
                    .order("uploaded_at", desc=False)
                    .execute()
                )
                timestamps = [
                    datetime.datetime.fromisoformat(cast(dict[str, Any], item)["uploaded_at"].replace("Z", "+00:00"))
                    for item in res.data
                ]

            if not timestamps:
                return 0, None

            # Algorithm to find the active window:
            active_window_start = None
            count = 0
            for dt in timestamps:
                # If no window started, or this upload is after the 24h window of the previous start
                if active_window_start is None or dt >= active_window_start + datetime.timedelta(hours=24):
                    active_window_start = dt
                    count = 1
                else:
                    count += 1

            # Final check: is the last window found already expired?
            if active_window_start and now >= active_window_start + datetime.timedelta(hours=24):
                return 0, None

            return count, active_window_start

        except Exception as e:
            logger.error(f"Failed to calculate quota usage for user {user_id}: {e}")
            # Fail closed for security
            return 9999, None

    async def check_quota(self, user_id: str, is_pro: bool) -> bool:
        """
        Check if user has sufficient quota within the 24-hour rolling window.
        """
        max_quota = self.PRO_LIMIT if is_pro else self.FREE_LIMIT

        # 1. Check Global usage (System-wide daily limit)
        today = datetime.date.today().isoformat()
        try:
            if self.db:
                query = text("SELECT total_uploads FROM system_daily_stats WHERE date = :today LIMIT 1")
                result = await self.db.execute(query, {"today": today})
                row = result.fetchone()
                sys_total = row[0] if row else 0
            else:
                sys_usage = (
                    await self.supabase.table("system_daily_stats")
                    .select("total_uploads")
                    .eq("date", today)
                    .maybe_single()
                    .execute()
                )
                sys_total = (
                    cast(dict[str, Any], sys_usage.data).get("total_uploads", 0) if sys_usage and sys_usage.data else 0
                )

            if sys_total >= self.GLOBAL_SYSTEM_LIMIT:
                logger.critical(f"System Global Quota Reached: {sys_total}/{self.GLOBAL_SYSTEM_LIMIT}")
                return False
        except Exception as e:
            logger.error(f"Global quota check failed: {e}")

        # 2. Check User Rolling Quota
        usage_count, _ = await self.get_quota_usage(user_id)

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
            # RPC call still uses Supabase client as it's easier than converting RPC to SQL
            # unless it's a simple logic.
            await self.supabase.rpc("increment_usage", {"p_user_id": user_id, "p_date": today}).execute()
        except Exception as e:
            logger.error(f"Failed to increment legacy quota for user {user_id}: {e}")

    async def get_user_quota_status(self, user_id: str, is_pro: bool) -> dict[str, Any]:
        """Get quota usage details for UI based on rolling window."""
        max_quota = self.PRO_LIMIT if is_pro else self.FREE_LIMIT

        try:
            used, window_start = await self.get_quota_usage(user_id)
            resets_at = (window_start + datetime.timedelta(hours=24)).isoformat() if window_start else None

            remaining = max(0, max_quota - used)

            return {
                "used": used,
                "limit": max_quota,
                "remaining": remaining,
                "is_pro": is_pro,
                "reset_type": "first_upload_window",
                "resets_at": resets_at,
            }
        except Exception as e:
            logger.error(f"Failed to get quota status: {e}")
            return {"used": 0, "limit": max_quota, "remaining": 0, "is_pro": is_pro}
