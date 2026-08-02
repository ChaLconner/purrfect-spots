from typing import Any

from sqlalchemy import column, select, table, text
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import AClient

from app.compat import structlog
from app.schemas.user import User
from app.utils.supabase_client import get_admin_client_or_fallback

logger = structlog.get_logger(__name__)


class UserBaseMixin:
    """Base mixin for user service containing shared state and helpers."""

    _cached_user_role_id: str | None = None
    SERVICE_SUPABASE_AUTH = "Supabase Auth"
    # Centralized user column selection to avoid over-fetching
    USER_COLUMNS = "id, email, name, username, picture, bio, google_id, treat_balance, total_treats_received, is_pro, stripe_customer_id, subscription_end_date, cancel_at_period_end, role_id, created_at, updated_at, banned_at"

    def _prefixed_user_columns(self, prefix: str) -> str:
        """Helper to prefix user columns for JOIN queries."""
        return ", ".join([f"{prefix}.{c}" for c in self.USER_COLUMNS.split(", ")])

    @property
    def supabase(self) -> AClient:
        raise NotImplementedError

    @property
    def supabase_admin(self) -> AClient | None:
        raise NotImplementedError

    @property
    def db(self) -> AsyncSession | None:
        raise NotImplementedError

    async def _get_admin_client(self) -> AClient:
        return await get_admin_client_or_fallback(self.supabase_admin)

    async def _get_user_role_id(self) -> str | None:
        """Get the ID of the 'user' role from the roles table (Async)"""
        if UserBaseMixin._cached_user_role_id:
            return UserBaseMixin._cached_user_role_id

        try:
            if self.db:
                query = text("SELECT id FROM roles WHERE name = 'user' LIMIT 1")
                result = await self.db.execute(query)
                row = result.fetchone()
                if row:
                    UserBaseMixin._cached_user_role_id = str(row[0])
                    return UserBaseMixin._cached_user_role_id
            else:
                from typing import cast

                admin = await self._get_admin_client()
                res = await admin.table("roles").select("id").eq("name", "user").execute()
                if res.data:
                    data = cast(list[dict[str, Any]], res.data)
                    UserBaseMixin._cached_user_role_id = cast(str, data[0]["id"])
                    return UserBaseMixin._cached_user_role_id
        except Exception as e:
            logger.warning("Failed to fetch default user role ID: %s", e)
        return None

    @staticmethod
    def _users_table() -> Any:
        return table(
            "users",
            column("id"),
            column("email"),
            column("name"),
            column("username"),
            column("picture"),
            column("bio"),
            column("google_id"),
            column("treat_balance"),
            column("total_treats_received"),
            column("is_pro"),
            column("stripe_customer_id"),
            column("subscription_end_date"),
            column("cancel_at_period_end"),
            column("role_id"),
            column("created_at"),
            column("updated_at"),
            column("banned_at"),
        )

    @staticmethod
    def _roles_table() -> Any:
        return table("roles", column("id"), column("name"))

    @staticmethod
    def _permissions_table() -> Any:
        return table("permissions", column("id"), column("code"))

    @staticmethod
    def _role_permissions_table() -> Any:
        return table("role_permissions", column("role_id"), column("permission_id"))

    @staticmethod
    def _extract_role_dict(role_data: Any) -> dict[str, Any] | None:
        """Normalize Supabase embedded role relations that may be returned as dict or list."""
        if isinstance(role_data, dict):
            return role_data
        if isinstance(role_data, list) and role_data:
            first = role_data[0]
            if isinstance(first, dict):
                return first
        return None

    def _map_db_user_to_model(self, data: dict[str, Any]) -> User:
        """Map DB result with nested role/permissions to User model"""
        from typing import cast

        permissions: list[str] = []

        role_data = data.get("roles")
        role_dict = self._extract_role_dict(role_data)
        if role_dict:
            rps = cast(list[dict[str, Any]], role_dict.get("role_permissions", []))
            for rp in rps:
                perm = cast(dict[str, Any] | None, rp.get("permissions"))
                if perm and isinstance(perm, dict) and "code" in perm:
                    permissions.append(cast(str, perm["code"]))

        user_fields = data.copy()
        user_fields.pop("roles", None)
        user_fields.pop("permissions", None)
        user_fields.pop("role", None)
        if role_dict and "name" in role_dict:
            user_fields["role"] = role_dict["name"]

        return User(**user_fields, permissions=permissions)

    async def _log_audit_event(self, action: str, user_id: str, resource: str = "users") -> None:
        """Helper to log audit events to PostgreSQL or Supabase."""
        if self.db:
            await self.db.execute(
                text("INSERT INTO audit_logs (action, user_id, resource) VALUES (:action, :u_id, :resource)"),
                {"action": action, "u_id": user_id, "resource": resource},
            )
        else:
            admin = await self._get_admin_client()
            await (
                admin.table("audit_logs").insert({"action": action, "user_id": user_id, "resource": resource}).execute()
            )

    def _build_user_with_role_query(self) -> Any:
        """Helper to build base SQLAlchemy query joining users with roles."""
        users = self._users_table()
        roles = self._roles_table()
        return select(*users.c, roles.c.name.label("role_name")).select_from(
            users.outerjoin(roles, users.c.role_id == roles.c.id)
        )

    async def get_user_by_id(self, user_id: str) -> User | None:
        """Abstract method to be implemented in subclasses or other mixins."""
        raise NotImplementedError
