/**
 * Permission codes for access control
 */
export const PERMISSIONS = {
  // User Management
  USERS_READ: 'users:read',
  USERS_WRITE: 'users:write',
  USERS_DELETE: 'users:delete',
  USERS_UPDATE: 'users:update',

  // Content Management
  CONTENT_READ: 'content:read',
  CONTENT_DELETE: 'content:delete',

  // Moderation
  REPORTS_READ: 'reports:read',
  REPORTS_UPDATE: 'reports:update',

  // System
  SYSTEM_STATS: 'system:stats',
  SYSTEM_SETTINGS: 'system:settings',
  AUDIT_READ: 'audit:read',
  TREATS_MANAGE: 'treats:manage',
  CAT_MANAGE: 'cat:manage',
  COMMENTS_MANAGE: 'comments:manage',
  ROLES_MANAGE: 'roles:manage',

  // General Access
  ACCESS_ADMIN: 'access:admin',
} as const;

export type Permission = (typeof PERMISSIONS)[keyof typeof PERMISSIONS];
