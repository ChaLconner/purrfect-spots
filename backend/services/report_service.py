from typing import Any

from supabase import AClient

from logger import logger


class ReportService:
    def __init__(self, supabase: AClient) -> None:
        self.supabase = supabase

    async def create_report(
        self, photo_id: str, reporter_id: str, reason: str, details: str | None = None
    ) -> dict[str, Any]:
        """
        Create a new report for a photo.
        """
        try:
            data = {
                "photo_id": photo_id,
                "reporter_id": reporter_id,
                "reason": reason,
                "details": details,
                "status": "pending",
            }
            res = await self.supabase.table("reports").insert(data).execute()
            if not res.data:
                raise ValueError("Failed to create report")
            return res.data[0]
        except Exception as e:
            logger.error(f"Report creation failed: {e}")
            raise

    async def get_user_reports(self, user_id: str) -> list[dict[str, Any]]:
        """
        List reports submitted by a specific user.
        """
        try:
            res = (
                await self.supabase.table("reports")
                .select("*")
                .eq("reporter_id", user_id)
                .order("created_at", desc=True)
                .execute()
            )
            return res.data or []
        except Exception as e:
            logger.error(f"Failed to fetch user reports: {e}")
            return []
