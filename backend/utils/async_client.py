from typing import Any, Dict, List, Optional, cast

import httpx

from config import config
from logger import logger


class AsyncSupabaseClient:
    """
    High-performance async client for Supabase using httpx.
    Used for high-traffic read operations to avoid blocking the event loop.
    """

    def __init__(self) -> None:
        self.base_url = f"{config.SUPABASE_URL}/rest/v1"
        self.headers = {
            "apikey": config.SUPABASE_KEY,
            "Authorization": f"Bearer {config.SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }
        self.timeout = httpx.Timeout(10.0, connect=5.0)

    async def rpc(
        self, function_name: str, params: Optional[Dict[str, Any]] = None, jwt_token: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a Postgres function (RPC) asynchronously.
        """
        url = f"{self.base_url}/rpc/{function_name}"

        headers = self.headers.copy()
        if jwt_token:
            headers["Authorization"] = f"Bearer {jwt_token}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, headers=headers, json=params or {})
                response.raise_for_status()
                return cast(List[Dict[str, Any]], response.json())
            except httpx.HTTPStatusError as e:
                is_auth_error = e.response.status_code in (401, 403)
                log_func = logger.warning if is_auth_error else logger.error
                log_func(f"Async RPC {function_name} failed ({e.response.status_code}): {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Async RPC {function_name} error: {type(e).__name__}: {str(e)}")
                raise

    async def select(
        self,
        table: str,
        columns: str = "*",
        order: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        filters: Optional[Dict[str, str]] = None,
        jwt_token: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query asynchronously.
        Very basic implementation for common use cases.
        """
        url = f"{self.base_url}/{table}"
        # Use list of tuples (or dict items) to support duplicate keys in filters
        # e.g. ?latitude=gte.10&latitude=lte.20
        params: List[tuple[str, str]] = [("select", columns)]

        if order:
            params.append(("order", order))
        if limit is not None:
            params.append(("limit", str(limit)))
        if offset is not None:
            params.append(("offset", str(offset)))

        if filters:
            if isinstance(filters, dict):
                params.extend(filters.items())
            elif isinstance(filters, list):
                params.extend(filters)

        headers = self.headers.copy()
        if jwt_token:
            headers["Authorization"] = f"Bearer {jwt_token}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                return cast(List[Dict[str, Any]], response.json())
            except httpx.HTTPStatusError as e:
                is_auth_error = e.response.status_code in (401, 403)
                log_func = logger.warning if is_auth_error else logger.error
                log_func(f"Async SELECT {table} failed ({e.response.status_code}): {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Async SELECT {table} error: {str(e)}")
                raise

    async def count(self, table: str, filters: Optional[Dict[str, str]] = None, jwt_token: Optional[str] = None) -> int:
        """
        Get the exact count of rows in a table asynchronously.
        Uses PostGrest 'Prefer: count=exact' header if possible, or HEAD request.
        """
        url = f"{self.base_url}/{table}"

        headers = self.headers.copy()
        headers["Prefer"] = "count=exact"
        if jwt_token:
            headers["Authorization"] = f"Bearer {jwt_token}"

        params = {"select": "id", "limit": "1"}  # Minimal data transfer
        if filters:
            params.update(filters)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                # HEAD is even more efficient for just getting headers
                response = await client.head(url, headers=headers, params=params)
                response.raise_for_status()

                # Extract from Content-Range header: "0-0/123" -> 123
                content_range = response.headers.get("Content-Range")
                if content_range and "/" in content_range:
                    return int(content_range.split("/")[-1])
                return 0
            except Exception as e:
                logger.error(f"Async COUNT {table} failed: {str(e)}")
                # Fallback to a small select if HEAD fails for some reason
                try:
                    res = await self.select(table, columns="id", filters=filters, jwt_token=jwt_token)
                    return len(res)
                except Exception as fallback_err:
                    logger.warning(f"Async COUNT {table} fallback also failed: {fallback_err}")
                    return 0

    async def insert(self, table: str, data: Dict[str, Any], jwt_token: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Execute an INSERT query asynchronously.
        Returns the inserted record(s).
        """
        url = f"{self.base_url}/{table}"

        headers = self.headers.copy()
        headers["Prefer"] = "return=representation"  # Ensure we get data back
        if jwt_token:
            headers["Authorization"] = f"Bearer {jwt_token}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, headers=headers, json=data)
                response.raise_for_status()
                return cast(List[Dict[str, Any]], response.json())
            except httpx.HTTPStatusError as e:
                is_auth_error = e.response.status_code in (401, 403)
                log_func = logger.warning if is_auth_error else logger.error
                log_func(f"Async INSERT {table} failed ({e.response.status_code}): {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Async INSERT {table} error: {str(e)}")
                raise

    async def delete(
        self, table: str, filters: Dict[str, str], jwt_token: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a DELETE query asynchronously.
        """
        url = f"{self.base_url}/{table}"

        headers = self.headers.copy()
        if jwt_token:
            headers["Authorization"] = f"Bearer {jwt_token}"

        if not filters:
            raise ValueError("Delete requires filters to be safe")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.delete(url, headers=headers, params=filters)
                response.raise_for_status()
                # DELETE might return 204 No Content if Prefer: return=representation is not set
                # But our default header has it.
                if response.status_code == 204:
                    return []
                return cast(List[Dict[str, Any]], response.json())
            except httpx.HTTPStatusError as e:
                is_auth_error = e.response.status_code in (401, 403)
                log_func = logger.warning if is_auth_error else logger.error
                log_func(f"Async DELETE {table} failed ({e.response.status_code}): {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Async DELETE {table} error: {str(e)}")
                raise

    async def update(
        self, table: str, data: Dict[str, Any], filters: Dict[str, str], jwt_token: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute an UPDATE query asynchronously.
        Returns the updated record(s).
        """
        url = f"{self.base_url}/{table}"

        headers = self.headers.copy()
        headers["Prefer"] = "return=representation"
        if jwt_token:
            headers["Authorization"] = f"Bearer {jwt_token}"

        if not filters:
            raise ValueError("Update requires filters to be safe")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.patch(url, headers=headers, json=data, params=filters)
                response.raise_for_status()
                return cast(List[Dict[str, Any]], response.json())
            except httpx.HTTPStatusError as e:
                is_auth_error = e.response.status_code in (401, 403)
                log_func = logger.warning if is_auth_error else logger.error
                log_func(f"Async UPDATE {table} failed ({e.response.status_code}): {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Async UPDATE {table} error: {str(e)}")
                raise


# Singleton instance
async_supabase = AsyncSupabaseClient()
