from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

USERS_READ = "users:read"
USERS_WRITE = "users:write"
USERS_UPDATE = "users:update"
USERS_DELETE = "users:delete"

CONTENT_READ = "content:read"
CONTENT_WRITE = "content:write"
CONTENT_DELETE = "content:delete"

REPORTS_READ = "reports:read"
REPORTS_UPDATE = "reports:update"

SYSTEM_STATS = "system:stats"
SYSTEM_SETTINGS = "system:settings"
AUDIT_READ = "audit:read"
TREATS_MANAGE = "treats:manage"
COMMENTS_MANAGE = "comments:manage"
ROLES_READ = "roles:read"
ROLES_MANAGE = "roles:manage"

ACCESS_ADMIN = "access:admin"

ADMIN_ROLE_NAMES = frozenset({"admin", "super_admin"})


@dataclass(frozen=True)
class PermissionDefinition:
    code: str
    group: str
    description: str


PERMISSION_DEFINITIONS: tuple[PermissionDefinition, ...] = (
    PermissionDefinition(USERS_READ, "User Management", "View user list and details"),
    PermissionDefinition(USERS_WRITE, "User Management", "Edit user profile details"),
    PermissionDefinition(USERS_UPDATE, "User Management", "Update user roles and moderation state"),
    PermissionDefinition(USERS_DELETE, "User Management", "Delete or anonymize user accounts"),
    PermissionDefinition(CONTENT_READ, "Content Management", "View all uploaded content"),
    PermissionDefinition(CONTENT_WRITE, "Content Management", "Edit uploaded content metadata"),
    PermissionDefinition(CONTENT_DELETE, "Content Management", "Delete uploaded content"),
    PermissionDefinition(REPORTS_READ, "Moderation", "View user reports"),
    PermissionDefinition(REPORTS_UPDATE, "Moderation", "Resolve or dismiss reports"),
    PermissionDefinition(SYSTEM_STATS, "System", "View dashboard and security statistics"),
    PermissionDefinition(SYSTEM_SETTINGS, "System", "Manage system settings"),
    PermissionDefinition(AUDIT_READ, "System", "View audit logs"),
    PermissionDefinition(TREATS_MANAGE, "Treats", "Manage treats balances and transactions"),
    PermissionDefinition(COMMENTS_MANAGE, "Moderation", "Manage comments"),
    PermissionDefinition(ROLES_READ, "Role Management", "View roles"),
    PermissionDefinition(ROLES_MANAGE, "Role Management", "Manage role permissions"),
    PermissionDefinition(ACCESS_ADMIN, "Access Control", "Full admin shell access bypass"),
)

ALL_PERMISSION_CODES = tuple(permission.code for permission in PERMISSION_DEFINITIONS)

LEGACY_PERMISSION_ALIASES: dict[str, str] = {
    "admin_access": ACCESS_ADMIN,
    "system:audit_logs": AUDIT_READ,
    "system:config": SYSTEM_SETTINGS,
    "users:create": USERS_WRITE,
    "users:ban": USERS_UPDATE,
}

SYSTEM_ROLE_PERMISSION_CODES: dict[str, tuple[str, ...]] = {
    "admin": ALL_PERMISSION_CODES,
    "super_admin": ALL_PERMISSION_CODES,
    "moderator": (
        CONTENT_READ,
        CONTENT_WRITE,
        CONTENT_DELETE,
        REPORTS_READ,
        REPORTS_UPDATE,
        COMMENTS_MANAGE,
    ),
    "user": (),
}


def canonical_permission_records() -> list[dict[str, str]]:
    return [
        {"code": permission.code, "group": permission.group, "description": permission.description}
        for permission in PERMISSION_DEFINITIONS
    ]


def normalize_permission_code(permission: str | None) -> str | None:
    if not permission:
        return None
    return LEGACY_PERMISSION_ALIASES.get(permission, permission)


def normalize_permissions(permissions: Iterable[str] | None) -> list[str]:
    if permissions is None:
        return []

    normalized: list[str] = []
    seen: set[str] = set()

    for permission in permissions:
        if not isinstance(permission, str) or not permission:
            continue

        canonical = normalize_permission_code(permission)
        if canonical and canonical not in seen:
            seen.add(canonical)
            normalized.append(canonical)

    return normalized


def is_admin_role(role: str | None) -> bool:
    if not role:
        return False
    return role.lower() in ADMIN_ROLE_NAMES


def has_admin_access(role: str | None, permissions: Iterable[str] | None) -> bool:
    return is_admin_role(role) or ACCESS_ADMIN in set(normalize_permissions(permissions))
