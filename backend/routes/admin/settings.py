from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List, Any, Annotated
from dependencies import get_async_supabase_admin_client
from middleware.auth_middleware import require_permission
from schemas.user import User
from schemas.settings_schemas import (
    ConfigUpdate, 
    ConfigResponse, 
    ConfigHistoryResponse, 
    PendingConfigChangeResponse,
    PendingActionRequest
)
from logger import logger
from datetime import datetime
from services.email_service import email_service
from services.line_service import line_service

router = APIRouter()

@router.get("/", response_model=List[ConfigResponse])
async def get_all_settings(
    current_admin: Annotated[User, Depends(require_permission("system:settings"))]
):
    """Get all system settings with metadata."""
    try:
        admin_client = await get_async_supabase_admin_client()
        result = await admin_client.table("system_configs").select("*").execute()
        return result.data
    except Exception as e:
        logger.error("Failed to fetch settings: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch system settings")

@router.get("/history/{key}", response_model=List[ConfigHistoryResponse])
async def get_setting_history(
    key: str,
    current_admin: Annotated[User, Depends(require_permission("system:settings"))]
):
    """Get evolution history for a specific setting."""
    try:
        admin_client = await get_async_supabase_admin_client()
        result = await admin_client.table("config_history") \
            .select("*") \
            .eq("config_key", key) \
            .order("created_at", descending=True) \
            .execute()
        return result.data
    except Exception as e:
        logger.error("Failed to fetch history for %s: %s", key, e)
        raise HTTPException(status_code=500, detail="Failed to fetch config history")

@router.put("/{key}", response_model=ConfigResponse | PendingConfigChangeResponse)
async def update_setting(
    request: Request,
    key: str,
    update_data: ConfigUpdate,
    current_admin: Annotated[User, Depends(require_permission("system:settings"))]
):
    """Update a setting OR create an approval request if required."""
    try:
        admin_client = await get_async_supabase_admin_client()
        
        # Check if setting exists and if it requires approval
        check = await admin_client.table("system_configs").select("*").eq("key", key).single().execute()
        if not check.data:
            raise HTTPException(status_code=404, detail="Setting not found")
        
        setting = check.data
        
        # Check if approval is required (Maker-Checker)
        if setting.get("requires_approval", False):
            # Create a pending change
            pending = await admin_client.table("pending_config_changes").insert({
                "config_key": key,
                "proposed_value": update_data.value,
                "requester_id": current_admin.id,
                "status": "pending"
            }).execute()
            
            # Trigger Notifications (Phase 3)
            requester_name = current_admin.name or current_admin.email
            msg = f"\n[PURRFECT ADMIN]\n⚠️ Approval Required\nSetting: {key}\nRequested by: {requester_name}"
            await line_service.send_notification(msg)
            
            # Email Notification to other admins (optional, using placeholder for simplicity)
            # email_service.send_admin_config_request("admin@purrfectspots.com", requester_name, key)
            
            return pending.data[0]

        # Immediate update if no approval needed
        update_values = {"value": update_data.value, "updated_by": current_admin.id}
        if update_data.description is not None:
            update_values["description"] = update_data.description
        if update_data.category is not None:
            update_values["category"] = update_data.category
            
        result = await admin_client.table("system_configs").update(update_values).eq("key", key).execute()
        
        # Log to Detailed Config History
        await admin_client.table("config_history").insert({
            "config_key": key,
            "old_value": setting["value"],
            "new_value": update_data.value,
            "changed_by": current_admin.id,
            "change_reason": "Direct administrative update"
        }).execute()
        
        return result.data[0]
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        logger.error("Failed to update setting %s: %s", key, e)
        raise HTTPException(status_code=500, detail="Failed to update system setting")

@router.get("/pending", response_model=List[PendingConfigChangeResponse])
async def get_pending_changes(
    current_admin: Annotated[User, Depends(require_permission("system:settings"))]
):
    """Get all pending config changes (Checkers)"""
    try:
        admin_client = await get_async_supabase_admin_client()
        result = await admin_client.table("pending_config_changes") \
            .select("*") \
            .eq("status", "pending") \
            .execute()
        return result.data
    except Exception as e:
        logger.error("Failed to fetch pending changes: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch pending changes")

@router.post("/approve/{change_id}", response_model=ConfigResponse)
async def approve_change(
    change_id: str,
    current_admin: Annotated[User, Depends(require_permission("system:settings"))],
    payload: Optional[PendingActionRequest] = None
):
    """Approve a pending config change (Checker)."""
    try:
        admin_client = await get_async_supabase_admin_client()
        
        # 1. Fetch pending change
        pending_check = await admin_client.table("pending_config_changes").select("*").eq("id", change_id).single().execute()
        if not pending_check.data or pending_check.data["status"] != "pending":
            raise HTTPException(status_code=404, detail="Pending change not found or already processed")
        
        change = pending_check.data
        
        # Prevent self-approval (Maker cannot be Checker)
        if str(change["requester_id"]) == str(current_admin.id):
            raise HTTPException(status_code=403, detail="You cannot approve your own changes")

        # 2. Fetch current config
        config_check = await admin_client.table("system_configs").select("*").eq("key", change["config_key"]).single().execute()
        current_config = config_check.data
        
        # 3. Update main config
        update_result = await admin_client.table("system_configs").update({
            "value": change["proposed_value"],
            "updated_by": current_admin.id
        }).eq("key", change["config_key"]).execute()
        
        # 4. Record History
        await admin_client.table("config_history").insert({
            "config_key": change["config_key"],
            "old_value": current_config["value"],
            "new_value": change["proposed_value"],
            "changed_by": current_admin.id,
            "change_reason": f"Approved from Request {change_id}"
        }).execute()
        
        # 5. Update Pending record
        await admin_client.table("pending_config_changes").update({
            "status": "approved",
            "approver_id": current_admin.id,
            "updated_at": datetime.now().isoformat()
        }).eq("id", change_id).execute()
        
        # 6. Notify Requester (Phase 3)
        requester_res = await admin_client.table("users").select("email").eq("id", change["requester_id"]).single().execute()
        if requester_res.data:
            email_service.send_admin_config_result(
                requester_res.data["email"],
                change["config_key"],
                "approved",
                (current_admin.full_name or current_admin.email)
            )

        return update_result.data[0]
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        logger.error("Approval failed for change %s: %s", change_id, e)
        raise HTTPException(status_code=500, detail="Approval process failed")

@router.post("/reject/{change_id}", response_model=dict)
async def reject_change(
    change_id: str,
    current_admin: Annotated[User, Depends(require_permission("system:settings"))],
    payload: PendingActionRequest
):
    """Reject a pending config change."""
    try:
        admin_client = await get_async_supabase_admin_client()
        
        # 1. Fetch pending change first to get requester info
        pending_check = await admin_client.table("pending_config_changes").select("*").eq("id", change_id).single().execute()
        if not pending_check.data:
            raise HTTPException(status_code=404, detail="Pending change not found")
        
        change = pending_check.data

        # 2. Update status to rejected
        await admin_client.table("pending_config_changes").update({
            "status": "rejected",
            "approver_id": current_admin.id,
            "rejection_reason": payload.rejection_reason,
            "updated_at": datetime.now().isoformat()
        }).eq("id", change_id).execute()
        
        # 3. Notify Requester (Phase 3)
        requester_res = await admin_client.table("users").select("email").eq("id", change["requester_id"]).single().execute()
        if requester_res.data:
            email_service.send_admin_config_result(
                requester_res.data["email"],
                change["config_key"],
                "rejected",
                (current_admin.full_name or current_admin.email),
                payload.rejection_reason
            )

        return {"status": "rejected", "change_id": change_id}
    except Exception as e:
        logger.error("Rejection failed for %s: %s", change_id, e)
        raise HTTPException(status_code=500, detail="Rejection process failed")

