import { PERMISSIONS } from '@/constants/permissions';

export const LEGACY_PERMISSION_ALIASES: Record<string, string> = {
  admin_access: PERMISSIONS.ACCESS_ADMIN,
  'system:audit_logs': PERMISSIONS.AUDIT_READ,
  'system:config': PERMISSIONS.SYSTEM_SETTINGS,
  'users:create': PERMISSIONS.USERS_WRITE,
  'users:ban': PERMISSIONS.USERS_UPDATE,
};

export function normalizePermissions(permissions: unknown): string[] {
  if (!Array.isArray(permissions)) {
    return [];
  }

  const normalized = new Set<string>();
  for (const permission of permissions) {
    if (typeof permission !== 'string' || !permission) {
      continue;
    }

    normalized.add(permission);
    const alias = LEGACY_PERMISSION_ALIASES[permission];
    if (alias) {
      normalized.add(alias);
    }
  }

  return [...normalized];
}
