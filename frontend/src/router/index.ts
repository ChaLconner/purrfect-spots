import { createRouter, createWebHistory, type RouteLocationRaw } from 'vue-router';
import { useAuthStore } from '@/store/authStore';

const routes = [
  {
    path: '/',
    name: 'Home',
    component: (): Promise<unknown> => import('@/views/MapView.vue'),
    alias: '/map', // Allow /map to work but serve same content
  },
  {
    path: '/upload',
    name: 'Upload',
    component: (): Promise<unknown> => import('@/views/UploadView.vue'),
  },
  {
    path: '/gallery/:id?',
    name: 'Gallery',
    component: (): Promise<unknown> => import('@/views/GalleryView.vue'),
    props: true,
  },
  {
    path: '/profile/:id?',
    name: 'Profile',
    component: (): Promise<unknown> => import('@/views/ProfileView.vue'),
    // meta: { requiresAuth: true }, // We'll handle auth logic inside for public profiles
  },
  {
    path: '/login',
    name: 'Login',
    component: (): Promise<unknown> => import('@/views/AuthView.vue'),
    props: { mode: 'login' },
  },
  {
    path: '/register',
    name: 'Register',
    component: (): Promise<unknown> => import('@/views/AuthView.vue'),
    props: { mode: 'register' },
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: (): Promise<unknown> => import('@/views/ForgotPasswordView.vue'),
  },
  {
    path: '/reset-password',
    name: 'ResetPassword',
    component: (): Promise<unknown> => import('@/views/ResetPasswordView.vue'),
  },
  {
    path: '/verify-email',
    name: 'VerifyEmail',
    component: (): Promise<unknown> => import('@/views/VerifyEmailView.vue'),
    meta: { requiresGuest: true },
  },
  {
    path: '/leaderboard',
    name: 'Leaderboard',
    component: (): Promise<unknown> => import('@/views/LeaderboardView.vue'),
  },
  {
    path: '/subscription',
    name: 'Subscription',
    component: (): Promise<unknown> => import('@/views/SubscriptionView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/subscription/success',
    name: 'SubscriptionSuccess',
    component: (): Promise<unknown> => import('@/views/SubscriptionView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/subscription/cancel',
    name: 'SubscriptionCancel',
    component: (): Promise<unknown> => import('@/views/SubscriptionView.vue'),
    meta: { requiresAuth: true },
  },

  {
    path: '/auth/callback',
    name: 'AuthCallback',
    component: (): Promise<unknown> => import('@/components/AuthCallback.vue'),
    meta: { isAuthCallback: true },
  },
  {
    path: '/admin',
    component: (): Promise<unknown> => import('@/views/admin/AdminLayout.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      {
        path: '',
        name: 'AdminDashboard',
        component: (): Promise<unknown> => import('@/views/admin/AdminDashboard.vue'),
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: (): Promise<unknown> => import('@/views/admin/AdminUsers.vue'),
      },
      {
        path: 'photos',
        name: 'AdminPhotos',
        component: (): Promise<unknown> => import('@/views/admin/AdminPhotos.vue'),
      },
      {
        path: 'reports',
        name: 'AdminReports',
        component: (): Promise<unknown> => import('@/views/admin/AdminReports.vue'),
      },
      {
        path: 'audit-logs',
        name: 'AdminAuditLogs',
        component: (): Promise<unknown> => import('@/views/admin/AdminAuditLogs.vue'),
      },
    ],
  },
  {
    path: '/privacy-policy',
    name: 'PrivacyPolicy',
    component: (): Promise<unknown> => import('@/views/PrivacyPolicyView.vue'),
  },
  {
    path: '/terms-of-service',
    name: 'TermsOfService',
    component: (): Promise<unknown> => import('@/views/TermsOfServiceView.vue'),
  },
  // Catch-all 404 - Should always be the last route
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: (): Promise<unknown> => import('@/views/NotFoundView.vue'),
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
  // 1. Handle Supabase Auth Redirects (e.g. Email Verification links landing on root)
  // If we see a hash with access_token, redirect to AuthCallback to process it
  if (to.hash && to.hash.includes('access_token=') && to.name !== 'AuthCallback') {
    return { name: 'AuthCallback', query: to.query, hash: to.hash };
  }

  // 2. Auth Protection Guard
  if (to.meta.requiresAuth) {
    const auth = useAuthStore();

    // Wait for auth initialization if needed
    if (!auth.isInitialized) {
      await auth.initializeAuth();
    }

    if (!auth.isUserReady) {
      // Store the intended destination
      sessionStorage.setItem('redirectAfterAuth', to.fullPath);
      return { name: 'Login' };
    }

    // 3. Admin Access Guard
    if (to.meta.requiresAdmin && !auth.isAdmin) {
      // Security: Redirect users without admin access to 404
      return {
        name: 'NotFound',
        params: { pathMatch: to.path.substring(1).split('/') },
        query: to.query,
        hash: to.hash,
      };
    }
  } else {
    // Check if user is already logged in and trying to access auth pages
    const authStore = useAuthStore();
    if (
      (to.name === 'Login' || to.name === 'Register' || to.name === 'Auth') &&
      authStore.isUserReady
    ) {
      if (authStore.isAdmin) {
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
