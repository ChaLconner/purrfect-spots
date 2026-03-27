from typing import Any

import structlog
from sqlalchemy import text

from schemas.user import User
from services.user.base_mixin import UserBaseMixin

logger = structlog.get_logger(__name__)


class UserReadMixin(UserBaseMixin):
    """Mixin for user-related read operations."""

    async def get_user_by_id(self, user_id: str) -> User | None:
        """Get user by ID from database with Role and Permissions (Async)"""
        try:
            if self.db:
                query = text(
                    f"SELECT {self._prefixed_user_columns('u')}, r.name as role_name "
                    "FROM users u "
                    "LEFT JOIN roles r ON u.role_id = r.id "
                    "WHERE u.id = :u_id LIMIT 1"
                )
                db_res = await self.db.execute(query, {"u_id": user_id})
                row = db_res.fetchone()
                if row:
                    data = dict(row._mapping)
                    perm_query = text(
                        "SELECT p.code FROM permissions p "
                        "JOIN role_permissions rp ON p.id = rp.permission_id "
                        "JOIN users u ON rp.role_id = u.role_id "
                        "WHERE u.id = :u_id"
                    )
                    perm_db_res = await self.db.execute(perm_query, {"u_id": user_id})
                    permissions = [r[0] for r in perm_db_res]

                    user_data = data.copy()
                    user_data["role"] = data.get("role_name")
                    return User(**user_data, permissions=permissions)
            else:
                query_str = f"{self.USER_COLUMNS}, roles(name, role_permissions(permissions(code)))"
                admin = await self._get_admin_client()
                supa_res = await admin.table("users").select(query_str).eq("id", user_id).execute()
                if supa_res.data:
                    return self._map_db_user_to_model(supa_res.data[0])
            return None
        except Exception as e:
            logger.debug("Failed to retrieve profile by ID: %s", e)
            return None

    async def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        """Get user by email from database (Async)"""
        try:
            if self.db:
                query = text(f"SELECT {self.USER_COLUMNS} FROM users WHERE email = :email LIMIT 1")
                db_res = await self.db.execute(query, {"email": email})
                row = db_res.fetchone()
                return dict(row._mapping) if row else None
            admin = await self._get_admin_client()
            supa_res = await admin.table("users").select(self.USER_COLUMNS).eq("email", email).maybe_single().execute()
            return supa_res.data if supa_res and supa_res.data else None
        except Exception as e:
            logger.debug("Failed to retrieve profile by email: %s", e)
            return None

    async def get_user_by_username(self, username: str) -> User | None:
        """Get user by username from database (Async)"""
        try:
            if self.db:
                query = text(
                    f"SELECT {self._prefixed_user_columns('u')}, r.name as role_name "
                    "FROM users u "
                    "LEFT JOIN roles r ON u.role_id = r.id "
                    "WHERE LOWER(u.username) = LOWER(:username) LIMIT 1"
                )
                result = await self.db.execute(query, {"username": username})
                row = result.fetchone()
                if row:
                    data = dict(row._mapping)
                    perm_query = text(
                        "SELECT p.code FROM permissions p "
                        "JOIN role_permissions rp ON p.id = rp.permission_id "
                        "JOIN users u ON rp.role_id = u.role_id "
                        "WHERE LOWER(u.username) = LOWER(:username)"
                    )
                    perm_res = await self.db.execute(perm_query, {"username": username})
                    permissions = [r[0] for r in perm_res]

                    user_data = data.copy()
                    user_data["role"] = data.get("role_name")
                    return User(**user_data, permissions=permissions)
            else:
                admin = await self._get_admin_client()
                query_str = f"{self.USER_COLUMNS}, roles(name, role_permissions(permissions(code)))"
                supa_res = (
                    await admin.table("users").select(query_str).ilike("username", username).maybe_single().execute()
                )
                if supa_res and supa_res.data:
                    return self._map_db_user_to_model(supa_res.data)
            return None
        except Exception as e:
            logger.debug("Failed to retrieve profile by username: %s", e)
            return None
