import { PERMISSIONS } from '@/constants/permissions';
import type { User } from '@/types/auth';
import { normalizePermissions } from '@/utils/permissionNormalization';

type AdminUser = Pick<User, 'permissions' | 'role'> | null | undefined;

type AdminRoute = {
  path: string;
  permission: string;
};

const ADMIN_BYPASS_PERMISSIONS = new Set<string>([PERMISSIONS.ACCESS_ADMIN]);
const ADMIN_SHELL_PERMISSIONS = new Set<string>(Object.values(PERMISSIONS));

const ADMIN_ROUTE_ORDER: AdminRoute[] = [
  { path: '/admin', permission: PERMISSIONS.SYSTEM_STATS },
  { path: '/admin/users', permission: PERMISSIONS.USERS_READ },
  { path: '/admin/photos', permission: PERMISSIONS.CONTENT_READ },
  { path: '/admin/reports', permission: PERMISSIONS.REPORTS_READ },
  { path: '/admin/audit-logs', permission: PERMISSIONS.AUDIT_READ },
  { path: '/admin/settings', permission: PERMISSIONS.SYSTEM_SETTINGS },
  { path: '/admin/treats', permission: PERMISSIONS.TREATS_MANAGE },
  { path: '/admin/roles', permission: PERMISSIONS.ROLES_MANAGE },
  { path: '/admin/security', permission: PERMISSIONS.SYSTEM_STATS },
  { path: '/admin/comments', permission: PERMISSIONS.COMMENTS_MANAGE },
];

function getPermissions(user: AdminUser): string[] {
  return normalizePermissions(user?.permissions || []);
}

export function hasAdminBypass(user: AdminUser): boolean {
  const role = user?.role?.toLowerCase();
  if (role === 'admin' || role === 'super_admin') {
    return true;
  }

  return getPermissions(user).some((permission) => ADMIN_BYPASS_PERMISSIONS.has(permission));
}

export function canAccessAdminShell(user: AdminUser): boolean {
  if (hasAdminBypass(user)) {
    return true;
  }

  return getPermissions(user).some((permission) => ADMIN_SHELL_PERMISSIONS.has(permission));
}

export function hasAdminPermission(user: AdminUser, permission: string): boolean {
  return hasAdminBypass(user) || getPermissions(user).includes(permission);
}

export function getDefaultAdminPath(user: AdminUser): string | null {
  if (!canAccessAdminShell(user)) {
    return null;
  }

  for (const route of ADMIN_ROUTE_ORDER) {
    if (hasAdminPermission(user, route.permission)) {
      return route.path;
    }
  }

  return null;
}
