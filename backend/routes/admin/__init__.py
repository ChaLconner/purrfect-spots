from fastapi import APIRouter

from .audit import router as audit_router
from .comments import router as comments_router
from .content import router as content_router
from .reports import router as reports_router
from .roles import router as roles_router
from .security import router as security_router
from .settings import router as settings_router
from .stats import router as stats_router
from .treats import router as treats_router
from .users import router as users_router

router = APIRouter(prefix="/admin", tags=["admin"])

router.include_router(users_router)
router.include_router(stats_router)
router.include_router(content_router)
router.include_router(reports_router)
router.include_router(audit_router)
router.include_router(settings_router, prefix="/settings")
router.include_router(treats_router, prefix="/treats")
router.include_router(roles_router, prefix="/roles")
router.include_router(comments_router, prefix="/comments")
router.include_router(security_router)
