<template>
  <div
    class="min-h-screen bg-sand-50/50 flex pt-16 selection:bg-terracotta-100 selection:text-terracotta-900"
  >
    <!-- Mobile Sidebar Toggle -->
    <div class="md:hidden fixed top-20 left-4 z-40">
      <button
        class="bg-white p-2 rounded-lg shadow-md border border-sand-200 text-brown-600 focus:outline-none"
        aria-label="Toggle Menu"
        @click="isSidebarOpen = !isSidebarOpen"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-6 w-6"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M4 6h16M4 12h16M4 18h16"
          />
        </svg>
      </button>
    </div>

    <!-- Mobile Sidebar Overlay -->
    <div
      v-if="isSidebarOpen"
      class="fixed inset-0 bg-black bg-opacity-50 z-30 md:hidden"
      @click="isSidebarOpen = false"
    ></div>

    <!-- Sidebar -->
    <aside
      class="w-64 bg-white border-r border-sand-200 fixed inset-y-0 left-0 pt-16 z-40 transition-all duration-500 ease-in-out md:translate-x-0 shadow-[4px_0_24px_rgba(0,0,0,0.02)]"
      :class="isSidebarOpen ? 'translate-x-0' : '-translate-x-full'"
    >
      <div class="h-full flex flex-col">
        <nav class="flex-1 px-4 space-y-2 mt-6">
          <router-link
            to="/admin"
            class="flex items-center px-4 py-2 rounded-lg text-brown-600 hover:bg-sand-50 hover:text-brown-900 transition-colors group"
            active-class="bg-terracotta-50 text-terracotta-700 font-medium"
            exact-active-class="bg-terracotta-50 text-terracotta-700 font-medium"
            @click="isSidebarOpen = false"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-5 w-5 mr-3 text-brown-400 group-hover:text-brown-500 group-[.router-link-active]:text-terracotta-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
              />
            </svg>
            {{ t('admin.nav.dashboard') }}
          </router-link>

          <router-link
            v-if="canAccess(PERMISSIONS.USERS_READ)"
            to="/admin/users"
            class="flex items-center px-4 py-2 rounded-lg text-brown-600 hover:bg-sand-50 hover:text-brown-900 transition-colors group"
            active-class="bg-terracotta-50 text-terracotta-700 font-medium"
            @click="isSidebarOpen = false"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-5 w-5 mr-3 text-brown-400 group-hover:text-brown-500 group-[.router-link-active]:text-terracotta-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
              />
            </svg>
            {{ t('admin.nav.users') }}
          </router-link>

          <router-link
            v-if="canAccess(PERMISSIONS.CONTENT_READ)"
            to="/admin/photos"
            class="flex items-center px-4 py-2 rounded-lg text-brown-600 hover:bg-sand-50 hover:text-brown-900 transition-colors group"
            active-class="bg-terracotta-50 text-terracotta-700 font-medium"
            @click="isSidebarOpen = false"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-5 w-5 mr-3 text-brown-400 group-hover:text-brown-500 group-[.router-link-active]:text-terracotta-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            {{ t('admin.nav.content') }}
          </router-link>

          <router-link
            v-if="canAccess(PERMISSIONS.REPORTS_READ)"
            to="/admin/reports"
            class="flex items-center px-4 py-2 rounded-lg text-brown-600 hover:bg-sand-50 hover:text-brown-900 transition-colors group relative"
            active-class="bg-terracotta-50 text-terracotta-700 font-medium"
            @click="isSidebarOpen = false"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-5 w-5 mr-3 text-brown-400 group-hover:text-brown-500 group-[.router-link-active]:text-terracotta-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <span class="flex-1">{{ t('admin.nav.reports') }}</span>
            <span
              v-if="pendingReportsCount > 0"
              class="ml-2 bg-red-500 text-white text-xs font-bold px-2 py-0.5 rounded-full shadow-sm tabular-nums flex-shrink-0"
            >
              {{ pendingReportsCount > 99 ? '99+' : pendingReportsCount }}
            </span>
          </router-link>

          <router-link
            v-if="canAccess(PERMISSIONS.AUDIT_READ)"
            to="/admin/audit-logs"
            class="flex items-center px-4 py-2 rounded-lg text-brown-600 hover:bg-sand-50 hover:text-brown-900 transition-colors group"
            active-class="bg-terracotta-50 text-terracotta-700 font-medium"
            @click="isSidebarOpen = false"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-5 w-5 mr-3 text-brown-400 group-hover:text-brown-500 group-[.router-link-active]:text-terracotta-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            {{ t('admin.nav.auditLogs') }}
          </router-link>

          <router-link
            v-if="canAccess(PERMISSIONS.SYSTEM_SETTINGS)"
            to="/admin/settings"
            class="flex items-center px-4 py-2 rounded-lg text-brown-600 hover:bg-sand-50 hover:text-brown-900 transition-colors group"
            active-class="bg-terracotta-50 text-terracotta-700 font-medium"
            @click="isSidebarOpen = false"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-5 w-5 mr-3 text-brown-400 group-hover:text-brown-500 group-[.router-link-active]:text-terracotta-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
              />
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
            {{ t('admin.nav.systemSettings') }}
          </router-link>

          <router-link
            v-if="canAccess(PERMISSIONS.TREATS_MANAGE)"
            to="/admin/treats"
            class="flex items-center px-4 py-2 rounded-lg text-brown-600 hover:bg-sand-50 hover:text-brown-900 transition-colors group"
            active-class="bg-terracotta-50 text-terracotta-700 font-medium"
            @click="isSidebarOpen = false"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-5 w-5 mr-3 text-brown-400 group-hover:text-brown-500 group-[.router-link-active]:text-terracotta-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            {{ t('admin.nav.treatManagement') }}
          </router-link>

          <router-link
            v-if="canAccess(PERMISSIONS.ROLES_MANAGE)"
            to="/admin/roles"
            class="flex items-center px-4 py-2 rounded-lg text-brown-600 hover:bg-sand-50 hover:text-brown-900 transition-colors group"
            active-class="bg-terracotta-50 text-terracotta-700 font-medium"
            @click="isSidebarOpen = false"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-5 w-5 mr-3 text-brown-400 group-hover:text-brown-500 group-[.router-link-active]:text-terracotta-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
              />
            </svg>
            {{ t('admin.nav.roleManagement') }}
          </router-link>

          <router-link
            v-if="canAccess(PERMISSIONS.SYSTEM_STATS)"
            to="/admin/security"
            class="flex items-center px-4 py-2 rounded-lg text-brown-600 hover:bg-sand-50 hover:text-brown-900 transition-colors group"
            active-class="bg-terracotta-50 text-terracotta-700 font-medium"
            @click="isSidebarOpen = false"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-5 w-5 mr-3 text-brown-400 group-hover:text-brown-500 group-[.router-link-active]:text-terracotta-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
              />
            </svg>
            {{ t('admin.nav.security') }}
          </router-link>

          <router-link
            v-if="canAccess(PERMISSIONS.COMMENTS_MANAGE)"
            to="/admin/comments"
            class="flex items-center px-4 py-2 rounded-lg text-brown-600 hover:bg-sand-50 hover:text-brown-900 transition-colors group"
            active-class="bg-terracotta-50 text-terracotta-700 font-medium"
            @click="isSidebarOpen = false"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-5 w-5 mr-3 text-brown-400 group-hover:text-brown-500 group-[.router-link-active]:text-terracotta-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z"
              />
            </svg>
            {{ t('admin.nav.commentModeration') }}
          </router-link>

          <div class="pt-4 mt-4 border-t border-sand-200">
            <router-link
              to="/"
              class="flex items-center px-4 py-2 rounded-lg text-brown-600 hover:bg-sand-50 hover:text-brown-900 transition-colors group"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-5 w-5 mr-3 text-brown-400 group-hover:text-brown-500"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
                />
              </svg>
              {{ t('admin.nav.backToSite') }}
            </router-link>
          </div>
        </nav>
      </div>
    </aside>

    <!-- Main Content -->
    <div class="flex-1 flex flex-col md:pl-64 min-w-0 transition-all duration-500 ease-in-out">
      <main class="flex-1 py-6 px-4 sm:px-6 lg:px-8 mt-4 md:mt-0 max-w-7xl mx-auto w-full">
        <!-- Dashboard Content Container with subtle fade-in -->
        <div class="animate-in fade-in slide-in-from-bottom-4 duration-700">
          <router-view />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '@/store/authStore';
import { useAdminStore } from '@/store/adminStore';
import { PERMISSIONS } from '@/constants/permissions';

const { t } = useI18n();
const authStore = useAuthStore();
const adminStore = useAdminStore();
const isSidebarOpen = ref(false);

const pendingReportsCount = computed(() => adminStore.stats.pending_reports);

function canAccess(permission: string): boolean {
  return authStore.isAdmin || authStore.hasPermission(permission);
}

onMounted(() => {
  // NOTE: fetchStats() removed — AdminDashboard.vue handles its own data via fetchSummary().
  // Calling fetchStats() here caused a double /admin/summary request on every page load.
  // Start real-time subscription for reports (sidebar badge needs pending count)
  adminStore.subscribeToReports(canAccess(PERMISSIONS.REPORTS_READ));
});

onUnmounted(() => {
  // Clean up subscription
  adminStore.unsubscribeReports();
});
</script>
