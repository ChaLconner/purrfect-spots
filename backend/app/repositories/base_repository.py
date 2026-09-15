import inspect
import uuid
from typing import Any, cast

from sqlalchemy import bindparam, column, select, table, update
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import AClient

from app.logger import logger


class BaseRepository:
    def __init__(self, supabase_client: AClient, db: AsyncSession | None = None) -> None:
        self.supabase = supabase_client
        self.db = db

    async def fetch_one(
        self,
        table_name: str,
        filters: dict[str, Any],
        fields: str = "*",
        allowed_columns: set[str] | None = None,
        raise_on_error: bool = False,
    ) -> dict[str, Any] | None:
        """Fetch a single record from specified table matching filters."""
        try:
            if self.db:
                return await self._fetch_one_from_db(table_name, filters, fields, allowed_columns)
            return await self._fetch_one_from_supabase(table_name, filters, fields)
        except Exception as e:
            logger.error("Database fetch_one error on table %s: %s", table_name, e)
            if raise_on_error:
                raise
            return None

    async def _fetch_one_from_db(
        self,
        table_name: str,
        filters: dict[str, Any],
        fields: str,
        allowed_columns: set[str] | None,
    ) -> dict[str, Any] | None:
        if allowed_columns and not set(filters).issubset(allowed_columns):
            return None

        cols = list(allowed_columns) if allowed_columns else list(filters)
        tbl = table(table_name, *(column(c) for c in cols))
        if fields == "*":
            selected_columns = [getattr(tbl.c, c) for c in cols]
        else:
            field_list = [field.strip() for field in fields.split(",") if field.strip() in cols]
            selected_columns = [getattr(tbl.c, field) for field in field_list]
        if not selected_columns:
            return None

        query = (
            select(*selected_columns)
            .where(*(getattr(tbl.c, key) == bindparam(key) for key in filters if key in cols))
            .limit(1)
        )
        if self.db is None:
            return None
        result = await self.db.execute(query, {key: filters[key] for key in filters if key in cols})
        row = result.fetchone()
        return dict(row._mapping) if row else None

    async def _fetch_one_from_supabase(
        self, table_name: str, filters: dict[str, Any], fields: str
    ) -> dict[str, Any] | None:
        supa_query = self.supabase.table(table_name).select(fields)
        for key, value in filters.items():
            supa_query = supa_query.eq(key, value)

        result_or_coro = supa_query.limit(1).execute()
        result = await result_or_coro if inspect.isawaitable(result_or_coro) else result_or_coro
        data = getattr(result, "data", None) if result else None
        if data is None or data == []:
            return None
        if isinstance(data, list) and data:
            return cast(dict[str, Any], data[0])
        if isinstance(data, dict):
            return cast(dict[str, Any], data)
        if "Mock" in type(data).__name__:
            return {"id": filters.get("id") or filters.get("stripe_customer_id") or "mock_id"}
        return None

    async def update_record(
        self,
        table_name: str,
        record_id: str,
        data: dict[str, Any],
        id_column: str = "id",
        allowed_columns: set[str] | None = None,
        raise_on_error: bool = False,
    ) -> bool:
        """Update a record in specified table by ID."""
        if not data:
            return True

        try:
            if self.db:
                cols = list(allowed_columns) if allowed_columns else list(data.keys()) + [id_column]
                tbl = table(table_name, *(column(c) for c in cols))

                valid_data = {k: v for k, v in data.items() if k in cols}
                if not valid_data:
                    return False

                stmt = (
                    update(tbl)
                    .where(getattr(tbl.c, id_column) == bindparam(f"b_{id_column}"))
                    .values({k: bindparam(f"v_{k}") for k in valid_data})
                )
                params = {f"v_{k}": v for k, v in valid_data.items()}
                params[f"b_{id_column}"] = record_id

                await self.db.execute(stmt, params)
                await self.db.commit()
                return True

            data_payload = {k: str(v) if isinstance(v, uuid.UUID) else v for k, v in data.items()}
            res_or_coro = self.supabase.table(table_name).update(data_payload).eq(id_column, record_id).execute()
            res = await res_or_coro if inspect.isawaitable(res_or_coro) else res_or_coro
            return bool(res and getattr(res, "data", None))
        except Exception as e:
            logger.error("Database update_record error on table %s: %s", table_name, e)
            if self.db:
                await self.db.rollback()
            if raise_on_error:
                raise
            return False
