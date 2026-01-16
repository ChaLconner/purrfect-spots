import { createRouter, createWebHistory } from "vue-router";
import MapView from "@/views/MapView.vue";
import UploadView from "@/views/UploadView.vue";
import GalleryView from "@/views/GalleryView.vue";
import AuthView from "@/views/AuthView.vue";
import ProfileView from "@/views/ProfileView.vue";
import AuthCallback from "@/components/AuthCallback.vue";
import { useAuthStore } from "@/store/authStore";

const routes = [
  {
    path: "/",
    name: "Home",
    component: MapView,
  },
  {
    path: "/map",
    name: "Map",
    component: MapView,
  },
  {
    path: "/upload",
    name: "Upload",
    component: UploadView,
    meta: { requiresAuth: false },
  },
  {
    path: "/gallery/:id?",
    name: "Gallery",
    component: GalleryView,
    props: true,
  },
  {
    path: "/profile",
    name: "Profile",
    component: ProfileView,
    meta: { requiresAuth: true },
  },
  {
    path: "/login",
    name: "Login",
    component: AuthView,
    props: { mode: "login" },
  },
  {
    path: "/register",
    name: "Register",
    component: AuthView,
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
    path: "/auth/callback",
    name: "AuthCallback",
    component: AuthCallback,
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
