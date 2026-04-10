"""
Security monitoring endpoint for admin panel

Provides real-time security metrics, alert summaries, and system health checks.
"""

from fastapi import APIRouter, Depends, HTTPException

from middleware.auth_middleware import require_permission
from schemas.user import User
from utils.security_alerts import get_alert_summary, reset_alerts
from utils.session_concurrency import get_session_summary, reset_sessions

router = APIRouter()


@router.get("/security/summary")
async def get_security_summary(
    current_admin: User = Depends(require_permission("system:stats")),
):
    """
    Get comprehensive security summary for admin dashboard.
    Combines alert tracking, session management, and system health.
    """
    try:
        alert_summary = get_alert_summary()
        session_summary = get_session_summary()

        # Map to frontend structure expected by AdminSecurity.vue
        return {
            "alerts": {
                "total": (
                    alert_summary.get("active_failed_login_sources", 0)
                    + alert_summary.get("active_permission_violation_sources", 0)
                    + alert_summary.get("bulk_operations_tracked", 0)
                ),
                "critical": alert_summary.get("active_failed_login_sources", 0),
                "warnings": (
                    alert_summary.get("active_permission_violation_sources", 0)
                    + alert_summary.get("bulk_operations_tracked", 0)
                ),
            },
            "sessions": {
                "active": session_summary.get("total_active_sessions", 0),
                "concurrent_users": session_summary.get("users_with_active_sessions", 0),
                "peak_today": session_summary.get("total_active_sessions", 0),  # Simplified for in-memory
            },
            "recent": [],  # Recent detailed alerts can be added here if session persistency is added
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch security summary: {e}")


@router.post("/security/alerts/reset")
async def reset_security_alerts(
    current_admin: User = Depends(require_permission("system:settings")),
):
    """
    Reset all security alert tracking.
    Requires system:settings permission.
    """
    try:
        reset_alerts()
        return {"message": "Security alerts reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset alerts: {e}")


@router.post("/security/sessions/reset")
async def reset_all_sessions(
    current_admin: User = Depends(require_permission("system:settings")),
):
    """
    Reset all session tracking.
    Requires system:settings permission.
    """
    try:
        reset_sessions()
        return {"message": "Session tracking reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset sessions: {e}")
