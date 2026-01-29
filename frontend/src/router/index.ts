import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/store/authStore";

const routes = [
  {
    path: "/",
    name: "Home",
    component: () => import("@/views/MapView.vue"),
  },
  {
    path: "/map",
    name: "Map",
    component: () => import("@/views/MapView.vue"),
  },
  {
    path: "/upload",
    name: "Upload",
    component: () => import("@/views/UploadView.vue"),

  },
  {
    path: "/gallery/:id?",
    name: "Gallery",
    component: () => import("@/views/GalleryView.vue"),
    props: true,
  },
  {
    path: "/profile",
    name: "Profile",
    component: () => import("@/views/ProfileView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/login",
    name: "Login",
    component: () => import("@/views/AuthView.vue"),
    props: { mode: "login" },
  },
  {
    path: "/register",
    name: "Register",
    component: () => import("@/views/AuthView.vue"),
    props: { mode: "register" },
  },
  {
    path: "/forgot-password",
    name: "ForgotPassword",
    component: () => import("@/views/ForgotPasswordView.vue"),
  },
  {
    path: "/reset-password",
    name: "ResetPassword",
    component: () => import("@/views/ResetPasswordView.vue"),
  },
  {
    path: "/verify-email",
    name: "VerifyEmail",
    component: () => import("@/views/VerifyEmailView.vue"),
    meta: { requiresGuest: true },
  },

  {
    path: "/auth/callback",
    name: "AuthCallback",
    component: () => import("@/components/AuthCallback.vue"),
    meta: { isAuthCallback: true },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// Initialize auth state before navigation
// Initialize auth state is handled by Pinia store automatically on first use

// Global navigation guard
router.beforeEach((to, _from, next) => {
  // 1. Handle Supabase Auth Redirects (e.g. Email Verification links landing on root)
  // If we see a hash with access_token, redirect to AuthCallback to process it
  if (to.hash && to.hash.includes('access_token=') && to.name !== 'AuthCallback') {
    next({ name: 'AuthCallback', query: to.query, hash: to.hash });
    return;
  }

  // 2. Auth Protection Guard
  if (to.meta.requiresAuth) {
    const auth = useAuthStore();
    if (!auth.isUserReady) {
      // Store the intended destination
      sessionStorage.setItem("redirectAfterAuth", to.fullPath);
      next({ name: "Login" });
    } else {
      next();
    }
  } else if (
    (to.name === "Login" || to.name === "Register" || to.name === "Auth") &&
    useAuthStore().isUserReady
  ) {
    // If user is already logged in and has complete profile, redirect to upload
    next({ name: "Upload" });
  } else {
    next();
  }
});

export default router;
