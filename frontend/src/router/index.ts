import { createRouter, createWebHistory, type RouteLocationRaw } from 'vue-router';
import { PERMISSIONS } from '@/constants/permissions';
import { useAuthStore } from '@/store/authStore';
import { getDefaultAdminPath, hasAdminPermission } from '@/utils/adminAccess';

// Lazy-loaded route components (extracted for Vite code-splitting and to avoid duplication)
const MapView = (): Promise<unknown> => import('@/views/MapView.vue');
const UploadView = (): Promise<unknown> => import('@/views/UploadView.vue');
const GalleryView = (): Promise<unknown> => import('@/views/GalleryView.vue');
const ProfileView = (): Promise<unknown> => import('@/views/ProfileView.vue');
const AuthView = (): Promise<unknown> => import('@/views/AuthView.vue');
const ForgotPasswordView = (): Promise<unknown> => import('@/views/ForgotPasswordView.vue');
const ResetPasswordView = (): Promise<unknown> => import('@/views/ResetPasswordView.vue');
const VerifyEmailView = (): Promise<unknown> => import('@/views/VerifyEmailView.vue');
const LeaderboardView = (): Promise<unknown> => import('@/views/LeaderboardView.vue');
const MyReportsView = (): Promise<unknown> => import('@/views/MyReportsView.vue');
const SubscriptionView = (): Promise<unknown> => import('@/views/SubscriptionView.vue');
const AuthCallback = (): Promise<unknown> => import('@/components/AuthCallback.vue');
const AdminLayout = (): Promise<unknown> => import('@/views/admin/AdminLayout.vue');
const AdminDashboard = (): Promise<unknown> => import('@/views/admin/AdminDashboard.vue');
const AdminUsers = (): Promise<unknown> => import('@/views/admin/AdminUsers.vue');
const AdminPhotos = (): Promise<unknown> => import('@/views/admin/AdminPhotos.vue');
const AdminReports = (): Promise<unknown> => import('@/views/admin/AdminReports.vue');
const AdminAuditLogs = (): Promise<unknown> => import('@/views/admin/AdminAuditLogs.vue');
const AdminSettings = (): Promise<unknown> => import('@/views/admin/AdminSettings.vue');
const AdminTreats = (): Promise<unknown> => import('@/views/admin/AdminTreats.vue');
const AdminRoles = (): Promise<unknown> => import('@/views/admin/AdminRoles.vue');
const AdminComments = (): Promise<unknown> => import('@/views/admin/AdminComments.vue');
const AdminSecurity = (): Promise<unknown> => import('@/views/admin/AdminSecurity.vue');
const PrivacyPolicyView = (): Promise<unknown> => import('@/views/PrivacyPolicyView.vue');
const TermsOfServiceView = (): Promise<unknown> => import('@/views/TermsOfServiceView.vue');
const NotFoundView = (): Promise<unknown> => import('@/views/NotFoundView.vue');

const routes = [
  {
    path: '/',
    name: 'Home',
    component: MapView,
    alias: '/map', // Allow /map to work but serve same content
  },
  {
    path: '/upload',
    name: 'Upload',
    component: UploadView,
  },
  {
    path: '/gallery/:id?',
    name: 'Gallery',
    component: GalleryView,
    props: true,
  },
  {
    path: '/profile/:id?',
    name: 'Profile',
    component: ProfileView,
    // meta: { requiresAuth: true }, // We'll handle auth logic inside for public profiles
  },
  {
    path: '/login',
    name: 'Login',
    component: AuthView,
    props: { mode: 'login' },
  },
  {
    path: '/register',
    name: 'Register',
    component: AuthView,
    props: { mode: 'register' },
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: ForgotPasswordView,
  },
  {
    path: '/reset-password',
    name: 'ResetPassword',
    component: ResetPasswordView,
  },
  {
    path: '/verify-email',
    name: 'VerifyEmail',
    component: VerifyEmailView,
    meta: { requiresGuest: true },
  },
  {
    path: '/leaderboard',
    name: 'Leaderboard',
    component: LeaderboardView,
  },
  {
    path: '/my-reports',
    name: 'MyReports',
    component: MyReportsView,
    meta: { requiresAuth: true },
  },
  {
    path: '/subscription',
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Subscription',
        component: SubscriptionView,
      },
      {
        path: 'success',
        name: 'SubscriptionSuccess',
        component: SubscriptionView,
      },
      {
        path: 'cancel',
        name: 'SubscriptionCancel',
        component: SubscriptionView,
      },
    ],
  },
  {
    path: '/auth/callback',
    name: 'AuthCallback',
    component: AuthCallback,
    meta: { isAuthCallback: true },
  },
  {
    path: '/admin',
    component: AdminLayout,
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      {
        path: '',
        name: 'AdminDashboard',
        component: AdminDashboard,
        meta: { adminPermission: PERMISSIONS.SYSTEM_STATS },
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: AdminUsers,
        meta: { adminPermission: PERMISSIONS.USERS_READ },
      },
      {
        path: 'photos',
        name: 'AdminPhotos',
        component: AdminPhotos,
        meta: { adminPermission: PERMISSIONS.CONTENT_READ },
      },
      {
        path: 'reports',
        name: 'AdminReports',
        component: AdminReports,
        meta: { adminPermission: PERMISSIONS.REPORTS_READ },
      },
      {
        path: 'audit-logs',
        name: 'AdminAuditLogs',
        component: AdminAuditLogs,
        meta: { adminPermission: PERMISSIONS.AUDIT_READ },
      },
      {
        path: 'settings',
        name: 'AdminSettings',
        component: AdminSettings,
        meta: { adminPermission: PERMISSIONS.SYSTEM_SETTINGS },
      },
      {
        path: 'treats',
        name: 'AdminTreats',
        component: AdminTreats,
        meta: { adminPermission: PERMISSIONS.TREATS_MANAGE },
      },
      {
        path: 'roles',
        name: 'AdminRoles',
        component: AdminRoles,
        meta: { adminPermission: PERMISSIONS.ROLES_MANAGE },
      },
      {
        path: 'comments',
        name: 'AdminComments',
        component: AdminComments,
        meta: { adminPermission: PERMISSIONS.COMMENTS_MANAGE },
      },
      {
        path: 'security',
        name: 'AdminSecurity',
        component: AdminSecurity,
        meta: { adminPermission: PERMISSIONS.SYSTEM_STATS },
      },
    ],
  },
  {
    path: '/privacy-policy',
    name: 'PrivacyPolicy',
    component: PrivacyPolicyView,
  },
  {
    path: '/terms-of-service',
    name: 'TermsOfService',
    component: TermsOfServiceView,
  },
  // Catch-all 404 - Should always be the last route
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: NotFoundView,
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// Initialize auth state before navigation
// Initialize auth state is handled by Pinia store automatically on first use

// Global navigation guard
router.beforeEach(async (to): Promise<RouteLocationRaw | boolean | void> => {
  const authStore = useAuthStore();

  // 1. Handle Supabase Auth Redirects (e.g. Email Verification links landing on root)
  // If we see a hash with access_token, redirect to AuthCallback to process it
  if (to.hash && to.hash.includes('access_token=') && to.name !== 'AuthCallback') {
    return { name: 'AuthCallback', query: to.query, hash: to.hash };
  }

  // 2. Auth Protection Guard
  if (to.meta.requiresAuth) {
    // Wait for auth initialization if needed
    if (!authStore.isInitialized) {
      await authStore.initializeAuth();
    }

    // If auth was restored from cache during a hard refresh, verify the
    // real session before granting access to protected routes.
    if (authStore.isAuthenticated && !authStore.token) {
      const hasActiveSession = await authStore.refreshToken();
      if (!hasActiveSession) {
        sessionStorage.setItem('redirectAfterAuth', to.fullPath);
        return { name: 'Login' };
      }
    }

    if (!authStore.isUserReady) {
      // Store the intended destination
      sessionStorage.setItem('redirectAfterAuth', to.fullPath);
      return { name: 'Login' };
    }

    // 3. Admin Access Guard
    if (to.meta.requiresAdmin && !authStore.canAccessAdmin) {
      // Security: Redirect users without admin access to 404
      return {
        name: 'NotFound',
        params: { pathMatch: to.path.substring(1).split('/') },
        query: to.query,
        hash: to.hash,
      };
    }

    const requiredAdminPermission =
      typeof to.meta.adminPermission === 'string' ? to.meta.adminPermission : null;

    if (
      to.meta.requiresAdmin &&
      requiredAdminPermission &&
      !hasAdminPermission(authStore.user, requiredAdminPermission)
    ) {
      const redirectPath = getDefaultAdminPath(authStore.user);
      if (redirectPath && redirectPath !== to.path) {
        return { path: redirectPath };
      }

      return {
        name: 'NotFound',
        params: { pathMatch: to.path.substring(1).split('/') },
        query: to.query,
        hash: to.hash,
      };
    }
  } else {
    // Check if user is already logged in and trying to access auth pages
    if (
      (to.name === 'Login' || to.name === 'Register' || to.name === 'Auth') &&
      authStore.isUserReady
    ) {
      if (authStore.canAccessAdmin) {
        return { path: '/admin' };
      }
      return { path: '/' };
    }
  }

  return true;
});

// Dynamic Title Management
router.afterEach((to): void => {
  const baseTitle = 'Purrfect Spots';
  if (to.meta.title) {
    document.title = `${to.meta.title} | ${baseTitle}`;
  } else if (to.name) {
    // Fallback to route name if no meta title
    // e.g. "UserProfile" -> "User Profile"
    const readableName = String(to.name)
      .replace(/([A-Z])/g, ' $1')
      .trim();
    document.title = `${readableName} | ${baseTitle}`;
  } else {
    document.title = baseTitle;
  }
});

export default router;
