"""
Data Breach Detection and Notification System for Purrfect Spots

Provides automated breach detection for:
- Bulk data exports
- Unusual admin access patterns
- Failed authentication spikes
- Data modification anomalies
- Unauthorized access attempts

And notification workflows for:
- Admin alerts
- User notifications (when required by PDPA/GDPR)
- Regulatory reporting (72-hour requirement)
"""

from datetime import UTC, datetime
from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from postgrest.types import CountMethod
from pydantic import BaseModel, Field

from dependencies import get_async_supabase_admin_client
from limiter import limiter
from logger import logger
from middleware.auth_middleware import require_permission
from schemas.user import User
from services.email_service import email_service
from services.line_service import line_service
from utils.security_alerts import get_alert_summary

router = APIRouter()


class BreachReport(BaseModel):
    """Model for reporting a suspected data breach."""

    breach_type: str = Field(
        ..., description="Type of breach (unauthorized_access, data_leak, account_compromise, system_intrusion)"
    )
    description: str = Field(..., min_length=10, max_length=5000, description="Detailed description of the breach")
    affected_users: list[str] | None = Field(None, description="List of affected user IDs")
    severity: str = Field(default="medium", description="Severity level (low, medium, high, critical)")


BREACH_TYPES = {
    "unauthorized_access": "Unauthorized Access",
    "data_leak": "Data Leak/Exposure",
    "account_compromise": "Account Compromise",
    "system_intrusion": "System Intrusion",
    "insider_threat": "Insider Threat",
    "third_party_breach": "Third-Party Service Breach",
}

SEVERITY_LEVELS = {
    "low": {"color": "yellow", "response_time_hours": 72, "notify_users": False, "notify_regulator": False},
    "medium": {"color": "orange", "response_time_hours": 48, "notify_users": False, "notify_regulator": False},
    "high": {"color": "red", "response_time_hours": 24, "notify_users": True, "notify_regulator": True},
    "critical": {"color": "darkred", "response_time_hours": 1, "notify_users": True, "notify_regulator": True},
}


@router.post("/report")
@limiter.limit("5/minute")
async def report_breach(
    request: Request,
    report: BreachReport,
    current_admin: Annotated[User, Depends(require_permission("system:settings"))],
):
    """
    Report a suspected data breach.
    Creates an incident record and triggers notifications based on severity.
    """
    if report.breach_type not in BREACH_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid breach type. Valid types: {list(BREACH_TYPES.keys())}")
    if report.severity not in SEVERITY_LEVELS:
        raise HTTPException(status_code=400, detail=f"Invalid severity. Valid levels: {list(SEVERITY_LEVELS.keys())}")

    try:
        admin_client = await get_async_supabase_admin_client()

        # Create incident record
        incident = {
            "incident_type": report.breach_type,
            "severity": report.severity,
            "description": report.description,
            "reported_by": current_admin.id,
            "status": "investigating",
            "detected_at": datetime.now(UTC).isoformat(),
            "ip_address": request.client.host if request.client else "unknown",
            "affected_user_count": len(report.affected_users) if report.affected_users else 0,
        }

        result = await admin_client.table("security_incidents").insert(cast(dict[str, Any], incident)).execute()
        incident_id = cast(dict[str, Any], cast(list[Any], result.data)[0])["id"] if result.data else None

        # Record affected users
        if report.affected_users and incident_id:
            affected_records = [{"incident_id": incident_id, "user_id": uid} for uid in report.affected_users]
            await (
                admin_client.table("incident_affected_users")
                .insert(cast(list[dict[str, Any]], affected_records))
                .execute()
            )

        # Trigger notifications based on severity
        severity_config = SEVERITY_LEVELS[report.severity]
        notification_msg = (
            f"\n[PURRFECT SECURITY ALERT]\n"
            f"🚨 Data Breach Reported\n"
            f"Type: {BREACH_TYPES[report.breach_type]}\n"
            f"Severity: {report.severity.upper()}\n"
            f"Reported by: {current_admin.name or current_admin.email}\n"
            f"Response required within: {severity_config['response_time_hours']} hours"
        )

        # Send Line notification for high/critical
        if report.severity in ("high", "critical"):
            await line_service.send_notification(notification_msg)

        # Send email to all admins
        try:
            admin_emails_res = (
                await admin_client.table("users").select("email").in_("role", ["admin", "super_admin"]).execute()
            )
            for admin_user in cast(list[dict[str, Any]], admin_emails_res.data or []):
                if admin_user.get("email"):
                    email_service.send_security_alert(
                        to_email=cast(str, admin_user["email"]),
                        alert_type="data_breach",
                        severity=report.severity,
                        details=notification_msg,
                    )
        except Exception as e:
            logger.error(f"Failed to send breach notification emails: {e}")

        logger.warning(
            f"BREACH_REPORTED | incident_id={incident_id} | type={report.breach_type} | "
            f"severity={report.severity} | reported_by={current_admin.id}"
        )

        return {
            "message": "Breach report submitted successfully",
            "incident_id": incident_id,
            "severity": report.severity,
            "response_time_hours": severity_config["response_time_hours"],
            "notify_users": severity_config["notify_users"],
            "notify_regulator": severity_config["notify_regulator"],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to report breach: %s", e)
        raise HTTPException(status_code=500, detail="Failed to submit breach report")


@router.get("/incidents")
@limiter.limit("30/minute")
async def list_incidents(
    request: Request,
    current_admin: Annotated[User | None, Depends(require_permission("audit:read"))] = None,
    status: Annotated[str | None, Query()] = None,
    severity: Annotated[str | None, Query()] = None,
    incident_type: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """List all security incidents."""
    try:
        admin_client = await get_async_supabase_admin_client()
        query = (
            admin_client.table("security_incidents")
            .select("*, reporter:users!reported_by(email, name)", count=CountMethod.exact)
            .order("detected_at", desc=True)
            .range(offset, offset + limit - 1)
        )

        if status:
            query = query.eq("status", status)
        if severity:
            query = query.eq("severity", severity)
        if incident_type:
            query = query.eq("incident_type", incident_type)

        result = await query.execute()
        result_list = cast(list[dict[str, Any]], result.data or [])
        return {"data": result_list, "total": result.count or 0}
    except Exception as e:
        logger.error("Failed to list incidents: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch incidents")


@router.get("/incidents/{incident_id}")
async def get_incident_details(
    incident_id: str,
    current_admin: Annotated[User | None, Depends(require_permission("audit:read"))] = None,
):
    """Get detailed information about a specific incident."""
    try:
        admin_client = await get_async_supabase_admin_client()

        incident_res = (
            await admin_client.table("security_incidents")
            .select("*, reporter:users!reported_by(email, name)")
            .eq("id", incident_id)
            .maybe_single()
            .execute()
        )

        if not incident_res.data:
            raise HTTPException(status_code=404, detail="Incident not found")

        incident = cast(dict[str, Any], incident_res.data)

        # Get affected users
        affected_res = (
            await admin_client.table("incident_affected_users")
            .select("*, users(email, name)")
            .eq("incident_id", incident_id)
            .execute()
        )
        incident["affected_users"] = cast(list[dict[str, Any]], affected_res.data or [])

        # Get timeline entries
        timeline_res = (
            await admin_client.table("incident_timeline")
            .select("*, user:users!updated_by(email, name)")
            .eq("incident_id", incident_id)
            .order("created_at", desc=True)
            .execute()
        )
        incident["timeline"] = cast(list[dict[str, Any]], timeline_res.data or [])

        return incident
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get incident details: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch incident details")


class BreachStatusUpdate(BaseModel):
    status: str = Field(..., description="New status (investigating, contained, resolved, false_positive)")
    notes: str | None = None


@router.put("/incidents/{incident_id}/status")
async def update_incident_status(
    incident_id: str,
    request: Request,
    update_data: BreachStatusUpdate,
    current_admin: Annotated[User, Depends(require_permission("system:settings"))] = None,
):
    """Update the status of a security incident."""
    valid_statuses = ["investigating", "contained", "resolved", "false_positive"]
    status = update_data.status
    notes = update_data.notes
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Valid statuses: {valid_statuses}")

    try:
        admin_client = await get_async_supabase_admin_client()

        # Update incident status
        db_update = {
            "status": status,
            "updated_at": datetime.now(UTC).isoformat(),
        }
        if status == "resolved":
            db_update["resolved_at"] = datetime.now(UTC).isoformat()
            db_update["resolved_by"] = current_admin.id

        result = (
            await admin_client.table("security_incidents")
            .update(cast(dict[str, Any], db_update))
            .eq("id", incident_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Incident not found")

        # Add timeline entry
        await (
            admin_client.table("incident_timeline")
            .insert(
                {
                    "incident_id": incident_id,
                    "action": f"Status changed to {status}",
                    "notes": notes,
                    "updated_by": current_admin.id,
                }
            )
            .execute()
        )

        # If resolved, trigger resolution notification
        if status == "resolved" and result.data:
            incident = cast(dict[str, Any], result.data[0])
            incident_type = cast(str, incident.get("incident_type", "unknown"))
            notification_msg = (
                f"\n[PURRFECT SECURITY UPDATE]\n"
                f"✅ Incident Resolved\n"
                f"Type: {BREACH_TYPES.get(incident_type, incident_type)}\n"
                f"Resolved by: {current_admin.name or current_admin.email}"
            )
            await line_service.send_notification(notification_msg)

        return {"message": f"Incident status updated to {status}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update incident status: %s", e)
        raise HTTPException(status_code=500, detail="Failed to update incident status")


@router.get("/breach-summary")
async def get_breach_summary(
    current_admin: Annotated[User | None, Depends(require_permission("system:stats"))] = None,
):
    """Get summary of breach detection and incident status."""
    try:
        admin_client = await get_async_supabase_admin_client()

        # Incident counts by status
        status_counts = {}
        for status in ["investigating", "contained", "resolved", "false_positive"]:
            res = (
                await admin_client.table("security_incidents")
                .select("id", count=CountMethod.exact)
                .eq("status", status)
                .execute()
            )
            status_counts[status] = res.count or 0

        # Incident counts by severity
        severity_counts = {}
        for severity in ["low", "medium", "high", "critical"]:
            res = (
                await admin_client.table("security_incidents")
                .select("id", count=CountMethod.exact)
                .eq("severity", severity)
                .execute()
            )
            severity_counts[severity] = res.count or 0

        # SLA breaches (incidents past response time)
        sla_breach_res = await admin_client.rpc("check_incident_sla_breaches").execute()
        sla_breaches = sla_breach_res.data or []

        # Security alerts summary
        alerts = get_alert_summary()

        return {
            "incidents_by_status": status_counts,
            "incidents_by_severity": severity_counts,
            "sla_breaches": sla_breaches,
            "active_alerts": alerts,
            "generated_at": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        logger.error("Failed to get breach summary: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch breach summary")


@router.get("/regulatory-report")
async def generate_regulatory_report(
    start_date: Annotated[str, Query(description="Start date (ISO format)")],
    end_date: Annotated[str, Query(description="End date (ISO format)")],
    current_admin: Annotated[User, Depends(require_permission("system:settings"))] = None,
):
    """
    Generate regulatory compliance report for data breaches.
    Used for PDPA/GDPR 72-hour notification requirement documentation.
    """
    try:
        admin_client = await get_async_supabase_admin_client()

        incidents = (
            await admin_client.table("security_incidents")
            .select("*")
            .gte("detected_at", start_date)
            .lte("detected_at", end_date)
            .order("detected_at", desc=True)
            .execute()
        )

        incident_list = cast(list[dict[str, Any]], incidents.data or [])
        return {
            "report_period": {"start": start_date, "end": end_date},
            "total_incidents": len(incident_list),
            "high_severity_count": sum(1 for i in incident_list if i.get("severity") in ("high", "critical")),
            "resolved_count": sum(1 for i in incident_list if i.get("status") == "resolved"),
            "sla_breach_count": sum(1 for i in incident_list if i.get("sla_breached")),
            "incidents": incident_list,
            "generated_at": datetime.now(UTC).isoformat(),
            "generated_by": current_admin.id,
        }
    except Exception as e:
        logger.error("Failed to generate regulatory report: %s", e)
        raise HTTPException(status_code=500, detail="Failed to generate report")
