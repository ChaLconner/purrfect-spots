"""
User Repository for managing user database operations
"""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from supabase import AClient

from app.repositories.base_repository import BaseRepository

USER_ALLOWED_COLUMNS = {
    "id",
    "email",
    "stripe_customer_id",
    "is_pro",
    "subscription_end_date",
    "cancel_at_period_end",
    "treat_balance",
}


class UserRepository(BaseRepository):
    def __init__(self, supabase_client: AClient, db: AsyncSession | None = None) -> None:
        super().__init__(supabase_client, db=db)

    async def get_user(self, filters: dict[str, Any], fields: str = "*") -> dict[str, Any] | None:
        """Fetch user record by filter criteria."""
        return await self.fetch_one("users", filters, fields=fields, allowed_columns=USER_ALLOWED_COLUMNS)

    async def get_user_strict(self, filters: dict[str, Any], fields: str = "*") -> dict[str, Any] | None:
        """Fetch user, propagating database failures for billing-critical writes."""
        return await self.fetch_one(
            "users", filters, fields=fields, allowed_columns=USER_ALLOWED_COLUMNS, raise_on_error=True
        )

    async def update_user(self, user_id: str, updates: dict[str, Any]) -> bool:
        """Update user record by user ID."""
        return await self.update_record("users", user_id, updates, id_column="id", allowed_columns=USER_ALLOWED_COLUMNS)

    async def update_user_strict(self, user_id: str, updates: dict[str, Any]) -> bool:
        """Update user, propagating database failures for billing-critical writes."""
        return await self.update_record(
            "users",
            user_id,
            updates,
            id_column="id",
            allowed_columns=USER_ALLOWED_COLUMNS,
            raise_on_error=True,
        )
