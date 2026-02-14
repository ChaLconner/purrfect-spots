import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/store/authStore';

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/MapView.vue'),
    alias: '/map', // Allow /map to work but serve same content
  },
  {
    path: '/upload',
    name: 'Upload',
    component: () => import('@/views/UploadView.vue'),
  },
  {
    path: '/gallery/:id?',
    name: 'Gallery',
    component: () => import('@/views/GalleryView.vue'),
    props: true,
  },
  {
    path: '/profile/:id?',
    name: 'Profile',
    component: () => import('@/views/ProfileView.vue'),
    // meta: { requiresAuth: true }, // We'll handle auth logic inside for public profiles
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/AuthView.vue'),
    props: { mode: 'login' },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/AuthView.vue'),
    props: { mode: 'register' },
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: () => import('@/views/ForgotPasswordView.vue'),
  },
  {
    path: '/reset-password',
    name: 'ResetPassword',
    component: () => import('@/views/ResetPasswordView.vue'),
  },
  {
    path: '/verify-email',
    name: 'VerifyEmail',
    component: () => import('@/views/VerifyEmailView.vue'),
    meta: { requiresGuest: true },
  },
  {
    path: '/leaderboard',
    name: 'Leaderboard',
    component: () => import('@/views/LeaderboardView.vue'),
  },
  {
    path: '/subscription',
    name: 'Subscription',
    component: () => import('@/views/SubscriptionView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/subscription/success',
    name: 'SubscriptionSuccess',
    component: () => import('@/views/SubscriptionView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/subscription/cancel',
    name: 'SubscriptionCancel',
    component: () => import('@/views/SubscriptionView.vue'),
    meta: { requiresAuth: true },
  },

  {
    path: '/auth/callback',
    name: 'AuthCallback',
    component: () => import('@/components/AuthCallback.vue'),
    meta: { isAuthCallback: true },
  },
  {
    path: '/admin',
    name: 'AdminDashboard',
    component: () => import('@/views/AdminDashboard.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/privacy-policy',
    name: 'PrivacyPolicy',
    component: () => import('@/views/PrivacyPolicyView.vue'),
  },
  {
    path: '/terms-of-service',
    name: 'TermsOfService',
    component: () => import('@/views/TermsOfServiceView.vue'),
  },
  // Catch-all 404 - Should always be the last route
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFoundView.vue'),
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// Initialize auth state before navigation
// Initialize auth state is handled by Pinia store automatically on first use

// Global navigation guard
router.beforeEach(async (to) => {
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

    // 3. Admin Role Check
    if (to.meta.requiresAdmin && auth.user?.role !== 'admin') {
      // Redirect non-admins to home or 403 page
      return { name: 'Home' };
    }
  } else if (
    (to.name === 'Login' || to.name === 'Register' || to.name === 'Auth') &&
    useAuthStore().isUserReady
  ) {
    // If user is already logged in and has complete profile, redirect to upload
    return { name: 'Upload' };
  }

  return true;
});

// Dynamic Title Management
router.afterEach((to) => {
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
