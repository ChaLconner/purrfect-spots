import { createRouter, createWebHistory } from "vue-router";
import Map from "../components/Map.vue";
import Upload from "../components/Upload.vue";
import Gallery from "../components/Gallery.vue";
import AuthView from "../views/AuthView.vue";
import ProfileView from "../views/ProfileView.vue";
import AuthCallback from "../components/AuthCallback.vue";
import { initializeAuth, isUserReady } from "../store/auth";

const routes = [
  {
    path: "/",
    name: "Home",
    component: Map,
  },
  {
    path: "/upload",
    name: "Upload",
    component: Upload,
  },
  {
    path: "/gallery",
    name: "Gallery",
    component: Gallery,
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
initializeAuth();

// Global navigation guard
router.beforeEach((to, _from, next) => {
  if (to.meta.requiresAuth) {
    if (!isUserReady()) {
      // Store the intended destination
      sessionStorage.setItem("redirectAfterAuth", to.fullPath);
      next({ name: "Login" });
    } else {
      next();
    }
  } else if (
    (to.name === "Login" || to.name === "Register" || to.name === "Auth") &&
    isUserReady()
  ) {
    // If user is already logged in and has complete profile, redirect to home
    next({ name: "Home" });
  } else {
    next();
  }
});

export default router;
