import { describe, it, expect } from 'vitest';

import { PERMISSIONS } from '@/constants/permissions';
import {
  canAccessAdminShell,
  getDefaultAdminPath,
  hasAdminBypass,
  hasAdminPermission,
} from '@/utils/adminAccess';

describe('adminAccess', () => {
  it('treats admin role as bypass access', () => {
    const user = { role: 'admin', permissions: [] };

    expect(hasAdminBypass(user)).toBe(true);
    expect(canAccessAdminShell(user)).toBe(true);
    expect(getDefaultAdminPath(user)).toBe('/admin');
  });

  it('treats access:admin permission as bypass access', () => {
    const user = { role: 'user', permissions: [PERMISSIONS.ACCESS_ADMIN] };

    expect(hasAdminBypass(user)).toBe(true);
    expect(hasAdminPermission(user, PERMISSIONS.SYSTEM_SETTINGS)).toBe(true);
    expect(getDefaultAdminPath(user)).toBe('/admin');
  });

  it('normalizes legacy admin permissions before checking access', () => {
    const user = { role: 'user', permissions: ['admin_access', 'system:config'] };

    expect(hasAdminBypass(user)).toBe(true);
    expect(hasAdminPermission(user, PERMISSIONS.SYSTEM_SETTINGS)).toBe(true);
  });

  it('routes scoped admins to their first allowed section', () => {
    const user = { role: 'user', permissions: [PERMISSIONS.COMMENTS_MANAGE] };

    expect(hasAdminBypass(user)).toBe(false);
    expect(canAccessAdminShell(user)).toBe(true);
    expect(hasAdminPermission(user, PERMISSIONS.COMMENTS_MANAGE)).toBe(true);
    expect(hasAdminPermission(user, PERMISSIONS.SYSTEM_STATS)).toBe(false);
    expect(getDefaultAdminPath(user)).toBe('/admin/comments');
  });

  it('returns null when user has no admin access', () => {
    const user = { role: 'user', permissions: [] };

    expect(canAccessAdminShell(user)).toBe(false);
    expect(getDefaultAdminPath(user)).toBeNull();
  });
});
