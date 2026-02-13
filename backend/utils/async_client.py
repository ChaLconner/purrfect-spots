
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

    async def rpc(self, function_name: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a Postgres function (RPC) asynchronously.
        """
        url = f"{self.base_url}/rpc/{function_name}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, headers=self.headers, json=params or {})
                response.raise_for_status()
                return cast(List[Dict[str, Any]], response.json())
            except httpx.HTTPStatusError as e:
                logger.error(f"Async RPC {function_name} failed: {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Async RPC {function_name} error: {type(e).__name__}: {str(e)}")
                raise

    async def select(self, table: str, columns: str = "*", order: Optional[str] = None, 
                     limit: Optional[int] = None, offset: Optional[int] = None, 
                     filters: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query asynchronously.
        Very basic implementation for common use cases.
        """
        url = f"{self.base_url}/{table}"
        params = {"select": columns}
        
        if order:
            params["order"] = order
        if limit is not None:
            params["limit"] = str(limit)
        if offset is not None:
            params["offset"] = str(offset)
            
        if filters:
            params.update(filters)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                return cast(List[Dict[str, Any]], response.json())
            except httpx.HTTPStatusError as e:
                logger.error(f"Async SELECT {table} failed: {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Async SELECT {table} error: {str(e)}")
                raise

# Singleton instance
async_supabase = AsyncSupabaseClient()
