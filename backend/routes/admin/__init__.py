from fastapi import APIRouter

from .audit import router as audit_router
from .content import router as content_router
from .reports import router as reports_router
from .stats import router as stats_router
from .users import router as users_router

router = APIRouter(prefix="/admin", tags=["admin"])

router.include_router(users_router)
router.include_router(stats_router)
router.include_router(content_router)
router.include_router(reports_router)
router.include_router(audit_router)
