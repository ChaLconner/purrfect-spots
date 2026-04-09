from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from logger import logger
from supabase import AClient


class ReportService:
    def __init__(self, supabase: AClient, db: AsyncSession | None = None) -> None:
        self.supabase = supabase
        self.db = db
        # Consistent column selection for reports
        self.REPORT_COLUMNS = "id, photo_id, comment_id, reporter_id, reason, details, status, created_at"

    async def create_report(
        self,
        photo_id: str | None = None,
        comment_id: str | None = None,
        reporter_id: str | None = None,
        reason: str | None = None,
        details: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new report for a photo or comment.
        """
        if not photo_id and not comment_id:
            raise ValueError("Either photo_id or comment_id must be provided")

        try:
            data = {
                "photo_id": photo_id,
                "comment_id": comment_id,
                "reporter_id": reporter_id,
                "reason": reason,
                "details": details,
                "status": "pending",
            }
            if self.db:
                try:
                    # Basic SQL for reports table
                    query_str = (
                        "INSERT INTO reports (photo_id, comment_id, reporter_id, reason, details, status) "
                        "VALUES (:photo_id, :comment_id, :reporter_id, :reason, :details, :status) "
                        "RETURNING id, photo_id, comment_id, reporter_id, reason, details, status, created_at"
                    )
                    query = text(query_str)
                    result = await self.db.execute(query, data)
                    await self.db.commit()
                    row = result.fetchone()
                    if row:
                        return dict(row._mapping)
                except Exception as e:
                    await self.db.rollback()
                    logger.warning(f"SQL report creation failed, falling back to Supabase client: {e}")

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
                try:
                    query = text(
                        "SELECT id, photo_id, comment_id, reporter_id, reason, details, status, created_at "
                        "FROM reports WHERE reporter_id = :u_id ORDER BY created_at DESC"
                    )
                    result = await self.db.execute(query, {"u_id": user_id})
                    reports = []
                    for row in result.fetchall():
                        reports.append(dict(row._mapping))
                    return reports
                except Exception as e:
                    logger.warning(f"SQL fetch user reports failed, falling back to Supabase client: {e}")
            res = (
                await self.supabase.table("reports")
                .select(self.REPORT_COLUMNS)
                .eq("reporter_id", user_id)
                .order("created_at", desc=True)
                .execute()
            )
            from typing import cast

            return cast(list[dict[str, Any]], res.data or [])
        except Exception as e:
            logger.error(f"Failed to fetch user reports: {e}")
            return []
