from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from dependencies import get_async_supabase_admin_client
from logger import logger
from middleware.auth_middleware import require_permission
from schemas.settings_schemas import (
    ConfigHistoryResponse,
    ConfigResponse,
    ConfigUpdate,
    PendingActionRequest,
    PendingConfigChangeResponse,
)
from schemas.user import User
from services.email_service import email_service
from services.encryption_service import encryption_service
from services.line_service import line_service

router = APIRouter()


@router.get("/", response_model=list[ConfigResponse])
async def get_all_settings(
    current_admin: Annotated[User, Depends(require_permission("system:settings"))],
    category: Annotated[str | None, Query()] = None,
):
    """Get all system settings with metadata."""
    try:
        admin_client = await get_async_supabase_admin_client()
        query = (
            admin_client.table("system_configs")
            .select(
                "key, value, type, description, is_public, is_encrypted, updated_at, category, requires_approval, updated_by"
            )
            .order("category")
            .order("key")
        )
        if category:
            query = query.eq("category", category)
        result = await query.execute()

        # SECURITY: Decrypt encrypted values before returning
        decrypted_data = []
        for item in result.data or []:
            if item.get("is_encrypted") and isinstance(item.get("value"), dict):
                try:
                    item["value"] = encryption_service.decrypt_value(item["value"])
                    item["is_encrypted_display"] = True
                except Exception as e:
                    logger.warning(f"Failed to decrypt setting {item.get('key')}: {e}")
                    item["value"] = "[ENCRYPTED - Unable to decrypt]"
                    item["is_encrypted_display"] = True
            decrypted_data.append(item)

        return decrypted_data
    except Exception as e:
        logger.error("Failed to fetch settings: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch system settings")


@router.get("/history/{key}/", response_model=list[ConfigHistoryResponse])
async def get_setting_history(key: str, current_admin: Annotated[User, Depends(require_permission("system:settings"))]):
    """Get evolution history for a specific setting."""
    try:
        admin_client = await get_async_supabase_admin_client()
        result = (
            await admin_client.table("config_history")
            .select(
                "id, config_key, old_value, new_value, changed_by, change_reason, created_at, user:users!changed_by(email)"
            )
            .eq("config_key", key)
            .order("created_at", descending=True)
            .execute()
        )
        history_entries = []
        for entry in result.data or []:
            user_info = entry.pop("user", None)
            entry["user_email"] = user_info.get("email") if isinstance(user_info, dict) else None
            history_entries.append(entry)
        return history_entries
    except Exception as e:
        logger.error("Failed to fetch history for %s: %s", key, e)
        raise HTTPException(status_code=500, detail="Failed to fetch config history")


@router.put("/{key}/", response_model=ConfigResponse | PendingConfigChangeResponse)
async def update_setting(
    request: Request,
    key: str,
    update_data: ConfigUpdate,
    current_admin: Annotated[User, Depends(require_permission("system:settings"))],
):
    """Update a setting OR create an approval request if required."""
    try:
        admin_client = await get_async_supabase_admin_client()

        check = (
            await admin_client.table("system_configs")
            .select("value, requires_approval, type, is_encrypted")
            .eq("key", key)
            .single()
            .execute()
        )
        if not check.data:
            raise HTTPException(status_code=404, detail="Setting not found")

        setting = check.data

        # SECURITY: Encrypt value if setting is marked as encrypted
        value_to_store = update_data.value
        old_value_for_history = setting["value"]
        if setting.get("is_encrypted", False):
            try:
                encrypted = encryption_service.encrypt_value(update_data.value, setting.get("type", "string"))
                value_to_store = encrypted
            except Exception as e:
                logger.error(f"Failed to encrypt setting {key}: {e}")
                raise HTTPException(status_code=500, detail="Failed to encrypt sensitive setting")

        # Check if approval is required (Maker-Checker)
        if setting.get("requires_approval", False):
            pending = (
                await admin_client.table("pending_config_changes")
                .insert(
                    {
                        "config_key": key,
                        "proposed_value": value_to_store,
                        "requester_id": current_admin.id,
                        "status": "pending",
                    }
                )
                .execute()
            )

            requester_name = current_admin.name or current_admin.email
            msg = f"\n[PURRFECT ADMIN]\n⚠️ Approval Required\nSetting: {key}\nRequested by: {requester_name}"
            await line_service.send_notification(msg)

            return pending.data[0]

        # Immediate update if no approval needed
        update_values = {"value": value_to_store, "updated_by": current_admin.id}
        if update_data.description is not None:
            update_values["description"] = update_data.description
        if update_data.category is not None:
            update_values["category"] = update_data.category

        result = (
            await admin_client.table("system_configs")
            .update(update_values)
            .eq("key", key)
            .select(
                "key, value, type, description, category, is_public, is_encrypted, requires_approval, updated_at, updated_by"
            )
            .single()
            .execute()
        )

        # Log to Detailed Config History
        await (
            admin_client.table("config_history")
            .insert(
                {
                    "config_key": key,
                    "old_value": old_value_for_history,
                    "new_value": value_to_store,
                    "changed_by": current_admin.id,
                    "change_reason": "Direct administrative update",
                }
            )
            .execute()
        )

        return result.data
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update setting %s: %s", key, e)
        raise HTTPException(status_code=500, detail="Failed to update system setting")


@router.get("/pending/", response_model=list[PendingConfigChangeResponse])
async def get_pending_changes(current_admin: Annotated[User, Depends(require_permission("system:settings"))]):
    """Get all pending config changes (Checkers)"""
    try:
        admin_client = await get_async_supabase_admin_client()
        result = (
            await admin_client.table("pending_config_changes")
            .select(
                "id, config_key, proposed_value, requester_id, approver_id, status, rejection_reason, created_at, updated_at, requester:users!requester_id(email)"
            )
            .eq("status", "pending")
            .execute()
        )

        pending_changes = result.data or []
        config_keys = list({item["config_key"] for item in pending_changes})
        current_values_by_key: dict[str, object | None] = {}

        if config_keys:
            configs_res = await (
                admin_client.table("system_configs").select("key, value").in_("key", config_keys).execute()
            )
            current_values_by_key = {config["key"]: config.get("value") for config in (configs_res.data or [])}

        normalized_changes = []
        for item in pending_changes:
            requester_info = item.pop("requester", None)
            item["requester_email"] = requester_info.get("email") if isinstance(requester_info, dict) else None
            item["current_value"] = current_values_by_key.get(item["config_key"])
            normalized_changes.append(item)

        return normalized_changes
    except Exception as e:
        logger.error("Failed to fetch pending changes: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch pending changes")


@router.post("/approve/{change_id}/", response_model=ConfigResponse)
async def approve_change(
    change_id: str,
    current_admin: Annotated[User, Depends(require_permission("system:settings"))],
    payload: PendingActionRequest | None = None,
):
    """Approve a pending config change (Checker)."""
    try:
        admin_client = await get_async_supabase_admin_client()

        # 1. Fetch pending change
        pending_check = (
            await admin_client.table("pending_config_changes").select("*").eq("id", change_id).single().execute()
        )
        if not pending_check.data or pending_check.data["status"] != "pending":
            raise HTTPException(status_code=404, detail="Pending change not found or already processed")

        change = pending_check.data

        # Prevent self-approval (Maker cannot be Checker)
        if str(change["requester_id"]) == str(current_admin.id):
            raise HTTPException(status_code=403, detail="You cannot approve your own changes")

        # 2. Fetch current config
        config_check = (
            await admin_client.table("system_configs").select("*").eq("key", change["config_key"]).single().execute()
        )
        current_config = config_check.data

        # 3. Update main config
        update_result = (
            await admin_client.table("system_configs")
            .update({"value": change["proposed_value"], "updated_by": current_admin.id})
            .eq("key", change["config_key"])
            .select(
                "key, value, type, description, category, is_public, is_encrypted, requires_approval, updated_at, updated_by"
            )
            .single()
            .execute()
        )

        # 4. Record History
        await (
            admin_client.table("config_history")
            .insert(
                {
                    "config_key": change["config_key"],
                    "old_value": current_config["value"],
                    "new_value": change["proposed_value"],
                    "changed_by": current_admin.id,
                    "change_reason": f"Approved from Request {change_id}",
                }
            )
            .execute()
        )

        # 5. Update Pending record
        await (
            admin_client.table("pending_config_changes")
            .update({"status": "approved", "approver_id": current_admin.id, "updated_at": datetime.now().isoformat()})
            .eq("id", change_id)
            .execute()
        )

        # 6. Notify Requester (Phase 3)
        requester_res = (
            await admin_client.table("users").select("email").eq("id", change["requester_id"]).single().execute()
        )
        if requester_res.data:
            email_service.send_admin_config_result(
                requester_res.data["email"],
                change["config_key"],
                "approved",
                (current_admin.name or current_admin.email),
            )

        return update_result.data
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error("Approval failed for change %s: %s", change_id, e)
        raise HTTPException(status_code=500, detail="Approval process failed")


@router.post("/reject/{change_id}/", response_model=dict)
async def reject_change(
    change_id: str,
    current_admin: Annotated[User, Depends(require_permission("system:settings"))],
    payload: PendingActionRequest,
):
    """Reject a pending config change."""
    try:
        admin_client = await get_async_supabase_admin_client()

        # 1. Fetch pending change first to get requester info
        pending_check = (
            await admin_client.table("pending_config_changes").select("*").eq("id", change_id).single().execute()
        )
        if not pending_check.data or pending_check.data["status"] != "pending":
            raise HTTPException(status_code=404, detail="Pending change not found or already processed")

        change = pending_check.data

        # 2. Update status to rejected
        await (
            admin_client.table("pending_config_changes")
            .update(
                {
                    "status": "rejected",
                    "approver_id": current_admin.id,
                    "rejection_reason": payload.rejection_reason,
                    "updated_at": datetime.now().isoformat(),
                }
            )
            .eq("id", change_id)
            .execute()
        )

        # 3. Notify Requester (Phase 3)
        requester_res = (
            await admin_client.table("users").select("email").eq("id", change["requester_id"]).single().execute()
        )
        if requester_res.data:
            email_service.send_admin_config_result(
                requester_res.data["email"],
                change["config_key"],
                "rejected",
                (current_admin.name or current_admin.email),
                payload.rejection_reason,
            )

        return {"status": "rejected", "change_id": change_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Rejection failed for %s: %s", change_id, e)
        raise HTTPException(status_code=500, detail="Rejection process failed")
