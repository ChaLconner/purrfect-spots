from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import AClient

from logger import logger


class ReportService:
    def __init__(self, supabase: AClient, db: AsyncSession | None = None) -> None:
        self.supabase = supabase
        self.db = db

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
            if self.db:
                query = text(
                    "INSERT INTO reports (photo_id, reporter_id, reason, details, status) "
                    "VALUES (:photo_id, :reporter_id, :reason, :details, :status) "
                    "RETURNING *"
                )
                result = await self.db.execute(query, data)
                await self.db.commit()
                row = result.fetchone()
                if not row:
                    raise ValueError("Failed to create report")
                return dict(row._mapping)
            res = await self.supabase.table("reports").insert(data).execute()
            if not res or not res.data:
                raise ValueError("Failed to create report")
            from typing import cast

            return cast(dict[str, Any], res.data[0])
        except Exception as e:
            logger.error(f"Report creation failed: {e}")
            raise

    async def get_user_reports(self, user_id: str) -> list[dict[str, Any]]:
        """
        List reports submitted by a specific user.
        """
        try:
            if self.db:
                query = text("SELECT * FROM reports WHERE reporter_id = :u_id ORDER BY created_at DESC")
                result = await self.db.execute(query, {"u_id": user_id})
                reports = []
                for row in result.fetchall():
                    reports.append(dict(row._mapping))
                return reports
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
