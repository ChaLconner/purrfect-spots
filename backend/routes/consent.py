"""
Consent Management System for Purrfect Spots

Provides user consent tracking for:
- Terms of Service acceptance
- Privacy Policy acceptance
- Marketing communications opt-in
- Data processing consent (PDPA/GDPR)
- Cookie consent
"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from postgrest.types import CountMethod

from dependencies import get_async_supabase_admin_client
from limiter import limiter
from logger import logger
from middleware.auth_middleware import get_current_user, require_permission
from schemas.consent import ConsentRecord
from schemas.user import User

router = APIRouter()


CONSENT_TYPES = {
    "tos": "Terms of Service",
    "privacy": "Privacy Policy",
    "marketing": "Marketing Communications",
    "data_processing": "Data Processing (PDPA/GDPR)",
    "cookies": "Cookie Consent",
}


def _is_missing_relation_error(error: Exception) -> bool:
    error_str = str(error)
    return "PGRST205" in error_str or "schema cache" in error_str or "Could not find the table" in error_str


@router.get("/my-consents")
async def get_my_consents(
    current_user: User = Depends(get_current_user),
):
    """Get all consent records for the current user."""
    try:
        admin_client = await get_async_supabase_admin_client()
        result = (
            await admin_client.table("user_consents")
            .select("*")
            .eq("user_id", current_user.id)
            .order("consent_type")
            .order("granted_at", desc=True)
            .execute()
        )

        consents = {}
        for record in result.data or []:
            ctype = record["consent_type"]
            if ctype not in consents:
                consents[ctype] = {
                    "consent_type": ctype,
                    "label": CONSENT_TYPES.get(ctype, ctype),
                    "granted": record["granted"],
                    "granted_at": record["granted_at"],
                    "ip_address": record.get("ip_address"),
                    "version": record.get("version"),
                }

        return {"consents": list(consents.values())}
    except Exception as e:
        if _is_missing_relation_error(e):
            logger.warning("Consent tables are unavailable; returning empty consent list")
            return {"consents": []}
        logger.error("Failed to fetch user consents: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch consent records")


@router.post("/consent")
@limiter.limit("10/minute")
async def record_consent(
    request: Request,
    consent: ConsentRecord,
    current_user: User = Depends(get_current_user),
):
    """
    Record user consent for a specific type.
    Users can grant or withdraw consent at any time.
    """
    if consent.consent_type not in CONSENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid consent type. Valid types: {list(CONSENT_TYPES.keys())}")

    try:
        admin_client = await get_async_supabase_admin_client()

        # Get current policy version
        version = "1.0"
        try:
            version_res = (
                await admin_client.table("consent_versions")
                .select("version")
                .eq("consent_type", consent.consent_type)
                .eq("is_active", True)
                .single()
                .execute()
            )
            version = version_res.data.get("version", "1.0") if version_res.data else "1.0"
        except Exception as version_error:
            if not _is_missing_relation_error(version_error):
                raise
            logger.warning("Consent version table is unavailable; using default version 1.0")

        # Record the consent
        record = {
            "user_id": current_user.id,
            "consent_type": consent.consent_type,
            "granted": consent.granted,
            "granted_at": datetime.now(UTC).isoformat(),
            "ip_address": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown")[:200],
            "version": version,
        }

        try:
            await admin_client.table("user_consents").insert(record).execute()
        except Exception as insert_error:
            if not _is_missing_relation_error(insert_error):
                raise
            logger.warning("Consent history table is unavailable; storing consent state in users table only")

        # Update user's consent status in users table for quick lookup
        if consent.consent_type == "tos":
            await (
                admin_client.table("users")
                .update({"tos_accepted": consent.granted})
                .eq("id", current_user.id)
                .execute()
            )
        elif consent.consent_type == "privacy":
            await (
                admin_client.table("users")
                .update({"privacy_accepted": consent.granted})
                .eq("id", current_user.id)
                .execute()
            )
        elif consent.consent_type == "marketing":
            await (
                admin_client.table("users")
                .update({"marketing_opt_in": consent.granted})
                .eq("id", current_user.id)
                .execute()
            )

        action = "granted" if consent.granted else "withdrawn"
        logger.info(f"Consent {action} | user_id={current_user.id} | type={consent.consent_type} | version={version}")

        return {
            "message": f"Consent {action} successfully",
            "consent_type": consent.consent_type,
            "granted": consent.granted,
            "version": version,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to record consent: %s", e)
        raise HTTPException(status_code=500, detail="Failed to record consent")


# ==========================================
# Admin endpoints for consent management
# ==========================================


@router.get("/admin/consents")
@limiter.limit("30/minute")
async def admin_list_consents(
    request: Request,
    consent_type: Annotated[str | None, Query()] = None,
    granted: Annotated[bool | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    current_admin: Annotated[User | None, Depends(require_permission("users:read"))] = None,
):
    """Admin: List all user consent records."""
    try:
        admin_client = await get_async_supabase_admin_client()
        query = (
            admin_client.table("user_consents")
            .select("*, users(email, name)", count=CountMethod.exact)
            .order("granted_at", desc=True)
            .range(offset, offset + limit - 1)
        )

        if consent_type:
            query = query.eq("consent_type", consent_type)
        if granted is not None:
            query = query.eq("granted", granted)

        result = await query.execute()
        return {"data": result.data, "total": result.count or 0}
    except Exception as e:
        if _is_missing_relation_error(e):
            logger.warning("Consent tables are unavailable; returning empty admin consent list")
            return {"data": [], "total": 0}
        logger.error("Failed to list consents: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch consent records")


@router.get("/admin/consent-stats")
async def admin_consent_stats(
    current_admin: Annotated[User | None, Depends(require_permission("system:stats"))] = None,
):
    """Admin: Get consent statistics across all users."""
    try:
        admin_client = await get_async_supabase_admin_client()
        stats = {}

        for ctype in CONSENT_TYPES:
            granted_res = (
                await admin_client.table("user_consents")
                .select("id", count=CountMethod.exact)
                .eq("consent_type", ctype)
                .eq("granted", True)
                .execute()
            )
            withdrawn_res = (
                await admin_client.table("user_consents")
                .select("id", count=CountMethod.exact)
                .eq("consent_type", ctype)
                .eq("granted", False)
                .execute()
            )
            stats[ctype] = {
                "label": CONSENT_TYPES[ctype],
                "granted": granted_res.count or 0,
                "withdrawn": withdrawn_res.count or 0,
            }

        return {"stats": stats}
    except Exception as e:
        if _is_missing_relation_error(e):
            logger.warning("Consent tables are unavailable; returning empty consent stats")
            return {"stats": {}}
        logger.error("Failed to fetch consent stats: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch consent statistics")
