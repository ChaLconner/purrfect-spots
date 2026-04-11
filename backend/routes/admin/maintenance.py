from fastapi import APIRouter, Depends, HTTPException

from logger import logger
from middleware.auth_middleware import require_permission
from schemas.user import User
from tasks.cleanup_tasks import run_maintenance_tasks

router = APIRouter()


@router.post("/maintenance/cleanup")
async def trigger_cleanup(
    current_admin: User = Depends(require_permission("system:settings")),
) -> dict:
    """
    Manually trigger background cleanup tasks.
    Used for maintenance or via external CRON triggers in serverless environments.
    """
    try:
        return await run_maintenance_tasks()
    except Exception as e:
        logger.error(f"Maintenance cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {e}")
