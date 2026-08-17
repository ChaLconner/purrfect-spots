from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.logger import logger
from app.middleware.auth_middleware import require_permission
from app.routes.admin.helpers import ADMIN_ERROR_RESPONSES
from app.schemas.user import User
from app.tasks.cleanup_tasks import run_maintenance_tasks

router = APIRouter()


@router.post("/maintenance/cleanup", responses=ADMIN_ERROR_RESPONSES)
async def trigger_cleanup(
    current_admin: Annotated[User, Depends(require_permission("system:settings"))],
) -> dict:
    """
    Manually trigger background cleanup tasks.
    Used for maintenance or via external CRON triggers in serverless environments.
    """
    try:
        result = await run_maintenance_tasks()
        if result.get("status") == "failed":
            raise HTTPException(status_code=500, detail=result)
        return result
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        logger.error(f"Maintenance cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {e}")
