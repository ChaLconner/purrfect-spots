import datetime
import uuid
from typing import Any, cast

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import AClient

from app.config import config
from app.logger import logger, sanitize_log_value
from app.schemas.gallery import UploadQuotaResponse


class QuotaServiceUnavailable(RuntimeError):
    """Raised when the authoritative quota reservation backend is unavailable."""


QUOTA_SERVICE_UNAVAILABLE_DETAIL = "Upload quota service unavailable"


class QuotaService:
    # Daily image upload limits
    FREE_LIMIT = config.QUOTA_FREE_LIMIT
    PRO_LIMIT = config.QUOTA_PRO_LIMIT
    GLOBAL_SYSTEM_LIMIT = 2000  # System-wide safety buffer

    def __init__(self, supabase: AClient, db: AsyncSession | None = None) -> None:
        self.supabase: AClient = supabase
        self.db = db

    async def _fetch_quota_timestamps(
        self, user_id: str, since: datetime.datetime, row_limit: int
    ) -> tuple[list[datetime.datetime], bool]:
        timestamps: list[datetime.datetime] = []
        if self.db:
            try:
                query = text(
                    "SELECT uploaded_at FROM cat_photos "
                    "WHERE user_id = :u_id AND uploaded_at > :since AND deleted_at IS NULL "
                    "ORDER BY uploaded_at DESC LIMIT :row_limit"
                )
                result = await self.db.execute(query, {"u_id": user_id, "since": since, "row_limit": row_limit})
                return [row[0] for row in reversed(result.fetchall())], True
            except Exception as exc:
                logger.warning("SQL quota fetch failed, falling back to Supabase client: %s", exc)
        if not self.supabase:
            return timestamps, False
        try:
            supabase_result = await (
                self.supabase.table("cat_photos")
                .select("uploaded_at")
                .eq("user_id", user_id)
                .gt("uploaded_at", since.isoformat())
                .is_("deleted_at", "null")
                .order("uploaded_at", desc=True)
                .limit(row_limit)
                .execute()
            )
            timestamps = [
                datetime.datetime.fromisoformat(cast(dict[str, Any], item)["uploaded_at"].replace("Z", "+00:00"))
                for item in supabase_result.data
            ]
            return list(reversed(timestamps)), True
        except Exception as exc:
            logger.error("Supabase quota fallback failed: %s", exc)
            return [], False

    @staticmethod
    def _active_quota_window(
        timestamps: list[datetime.datetime], now: datetime.datetime
    ) -> tuple[int, datetime.datetime | None]:
        active_window_start: datetime.datetime | None = None
        count = 0
        for timestamp in timestamps:
            if active_window_start is None or timestamp >= active_window_start + datetime.timedelta(hours=24):
                active_window_start = timestamp
                count = 1
            else:
                count += 1
        if active_window_start and now >= active_window_start + datetime.timedelta(hours=24):
            return 0, None
        return count, active_window_start

    async def get_quota_usage(self, user_id: str, max_rows: int | None = None) -> tuple[int, datetime.datetime | None]:
        """Calculate used slots in the current rolling 24-hour window."""
        now = datetime.datetime.now(datetime.UTC)
        since = now - datetime.timedelta(hours=48)
        row_limit = max(1, int(max_rows)) + 1 if max_rows is not None else max(self.PRO_LIMIT, self.FREE_LIMIT) + 1
        try:
            timestamps, source_succeeded = await self._fetch_quota_timestamps(user_id, since, row_limit)
            if not source_succeeded:
                return 9999, None
            if not timestamps:
                return 0, None
            return self._active_quota_window(timestamps, now)
        except Exception as e:
            logger.error(
                "Failed to calculate quota usage for user %s: %s",
                sanitize_log_value(user_id),
                sanitize_log_value(str(e)),
            )
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
            sys_total = 0
            source_succeeded = False
            if self.db:
                try:
                    query = text("SELECT total_uploads FROM system_daily_stats WHERE date = :today LIMIT 1")
                    result = await self.db.execute(query, {"today": today})
                    row = result.fetchone()
                    sys_total = row[0] if row else 0
                    source_succeeded = True
                except Exception as e:
                    logger.warning(f"SQL global quota check failed, falling back to Supabase client: {e}")
                    source_succeeded = False

            if not source_succeeded and self.supabase:
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
                source_succeeded = True

            if not source_succeeded:
                logger.error("Global quota check failed: no data source available")
                return False

            if sys_total >= self.GLOBAL_SYSTEM_LIMIT:
                logger.critical(f"System Global Quota Reached: {sys_total}/{self.GLOBAL_SYSTEM_LIMIT}")
                return False
        except Exception as e:
            logger.error("Global quota check failed: %s", sanitize_log_value(str(e)))
            return False

        # 2. Check User Rolling Quota
        usage_count, _ = await self.get_quota_usage(user_id, max_quota)

        if usage_count >= max_quota:
            logger.warning("User %s hit rolling quota: %s/%s", sanitize_log_value(user_id), usage_count, max_quota)
            return False

        return True

    @staticmethod
    def _rpc_bool(response: Any) -> bool:
        """Normalize PostgREST scalar RPC responses without trusting mock-like values."""
        data = getattr(response, "data", response)
        if isinstance(data, bool):
            return data
        if isinstance(data, (int, float)) and data in (0, 1):
            return bool(data)
        if isinstance(data, str) and data.lower() in {"true", "false"}:
            return data.lower() == "true"
        if isinstance(data, list) and len(data) == 1:
            return QuotaService._rpc_bool(data[0])
        if isinstance(data, dict) and len(data) == 1:
            return QuotaService._rpc_bool(next(iter(data.values())))
        return False

    async def reserve_upload_quota(self, user_id: str, is_pro: bool) -> str | None:
        """Atomically reserve one upload slot before expensive image processing."""
        reservation_id = str(uuid.uuid4())
        max_quota = self.PRO_LIMIT if is_pro else self.FREE_LIMIT
        expires_at = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
            seconds=config.UPLOAD_QUOTA_RESERVATION_TTL_SECONDS
        )
        try:
            response = await self.supabase.rpc(
                "reserve_upload_quota",
                {
                    "p_reservation_id": reservation_id,
                    "p_user_id": user_id,
                    "p_user_limit": max_quota,
                    "p_global_limit": self.GLOBAL_SYSTEM_LIMIT,
                    "p_expires_at": expires_at.isoformat(),
                },
            ).execute()
        except Exception as exc:
            logger.error("Upload quota reservation failed: %s", sanitize_log_value(str(exc)))
            raise QuotaServiceUnavailable(QUOTA_SERVICE_UNAVAILABLE_DETAIL) from exc

        return reservation_id if self._rpc_bool(response) else None

    async def complete_upload_quota(self, reservation_id: str) -> bool:
        """Mark a successfully persisted upload reservation as consumed."""
        try:
            response = await self.supabase.rpc("complete_upload_quota", {"p_reservation_id": reservation_id}).execute()
        except Exception as exc:
            logger.error("Upload quota completion failed: %s", sanitize_log_value(str(exc)))
            raise QuotaServiceUnavailable(QUOTA_SERVICE_UNAVAILABLE_DETAIL) from exc
        return self._rpc_bool(response)

    async def renew_upload_quota(self, reservation_id: str) -> bool:
        """Extend an active reservation before external storage work begins."""
        expires_at = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
            seconds=config.UPLOAD_QUOTA_RESERVATION_TTL_SECONDS
        )
        try:
            response = await self.supabase.rpc(
                "renew_upload_quota",
                {"p_reservation_id": reservation_id, "p_expires_at": expires_at.isoformat()},
            ).execute()
        except Exception as exc:
            logger.error("Upload quota renewal failed: %s", sanitize_log_value(str(exc)))
            raise QuotaServiceUnavailable(QUOTA_SERVICE_UNAVAILABLE_DETAIL) from exc
        return self._rpc_bool(response)

    async def release_upload_quota(self, reservation_id: str) -> bool:
        """Release a reservation when processing or persistence fails."""
        try:
            response = await self.supabase.rpc("release_upload_quota", {"p_reservation_id": reservation_id}).execute()
        except Exception as exc:
            logger.error("Upload quota release failed: %s", sanitize_log_value(str(exc)))
            raise QuotaServiceUnavailable(QUOTA_SERVICE_UNAVAILABLE_DETAIL) from exc
        return self._rpc_bool(response)

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
        """Increment the legacy per-user analytics counter after an upload."""
        today = datetime.date.today().isoformat()
        try:
            # RPC call still uses Supabase client as it's easier than converting RPC to SQL
            # unless it's a simple logic.
            await self.supabase.rpc("increment_usage", {"p_user_id": user_id, "p_date": today}).execute()
        except Exception as e:
            logger.error(
                "Failed to increment legacy quota for user %s: %s",
                sanitize_log_value(user_id),
                sanitize_log_value(str(e)),
            )

    async def get_user_quota_status(self, user_id: str, is_pro: bool) -> UploadQuotaResponse:
        """Get quota usage details for UI based on rolling window."""

        max_quota = self.PRO_LIMIT if is_pro else self.FREE_LIMIT

        try:
            used, window_start = await self.get_quota_usage(user_id, max_quota)
            resets_at = (window_start + datetime.timedelta(hours=24)).isoformat() if window_start else None

            remaining = max(0, max_quota - used)

            return UploadQuotaResponse(
                used=used,
                limit=max_quota,
                remaining=remaining,
                is_pro=is_pro,
                reset_type="first_upload_window",
                resets_at=resets_at,
            )
        except Exception as e:
            logger.error(f"Failed to get quota status: {e}")
            return UploadQuotaResponse(used=0, limit=max_quota, remaining=0, is_pro=is_pro)
