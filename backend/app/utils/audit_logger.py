from typing import Any


async def log_admin_action(
    admin_client: Any,
    admin_id: str,
    action: str,
    target_type: str,
    target_id: str,
    details: dict[str, Any] | None = None,
) -> None:
    """
    Centralized utility to log administrative actions to the audit_logs table.
    """
    log_entry = {
        "admin_id": admin_id,
        "action": action,
        "target_type": target_type,
        "target_id": target_id,
        "details": details or {},
    }

    try:
        result = admin_client.table("audit_logs").insert(log_entry).execute()
        if hasattr(result, "__await__"):
            await result
    except Exception as e:
        # In a real app, we might want to use a logger here
        print(f"Failed to log audit action: {e}")
        # We don't raise here to avoid failing the main action if logging fails,
        # though in some systems this might be required for compliance.
