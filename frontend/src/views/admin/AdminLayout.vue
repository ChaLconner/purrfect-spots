<template>
  <div
    class="min-h-screen bg-[#faf9f6] text-[#2f231f] font-body flex pt-0 md:pt-16 selection:bg-terracotta-100 selection:text-terracotta-900"
  >
    <!-- Mobile Sidebar Toggle -->
    <div class="md:hidden fixed top-4 left-4 z-[60]">
      <button
        ref="toggleButtonRef"
        class="w-11 h-11 grid place-items-center p-0 rounded-[0.875rem] bg-white border border-[#ddd5ce] text-terracotta-700 shadow-[0_5px_16px_rgba(66,33,16,0.08)] focus:outline-none focus:ring-2 focus:ring-terracotta-500"
        aria-label="Toggle Menu"
        :aria-expanded="isSidebarOpen"
        aria-controls="admin-sidebar"
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
      class="fixed inset-0 bg-[rgba(47,35,31,0.24)] backdrop-blur-[2px] z-30 md:hidden"
      @click="isSidebarOpen = false"
    ></div>

    <!-- Sidebar -->
    <aside
      id="admin-sidebar"
      ref="sidebarRef"
      class="w-64 bg-white border-r border-sand-200 fixed inset-y-0 left-0 pt-16 z-[55] transition-all duration-500 ease-in-out md:translate-x-0 shadow-[8px_0_28px_rgba(66,33,16,0.025)]"
      :class="isSidebarOpen ? 'translate-x-0' : '-translate-x-full'"
      tabindex="-1"
      @keydown.esc="isSidebarOpen = false"
    >
      <div class="h-full flex flex-col overflow-y-auto overscroll-contain [scrollbar-gutter:stable]">
        <nav class="flex flex-col flex-1 min-h-full gap-1 px-4 pb-6 mt-6">
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
            <AdminNavIcon />
            {{ t('admin.nav.roleManagement') }}
          </router-link>

          <router-link
            v-if="canAccess(PERMISSIONS.SYSTEM_STATS)"
            to="/admin/security"
            class="flex items-center px-4 py-2 rounded-lg text-brown-600 hover:bg-sand-50 hover:text-brown-900 transition-colors group"
            active-class="bg-terracotta-50 text-terracotta-700 font-medium"
            @click="isSidebarOpen = false"
          >
            <AdminNavIcon />
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
      <main class="flex-1 pt-20 pb-6 px-4 sm:px-6 lg:px-8 mt-4 md:pt-6 md:mt-0 max-w-7xl mx-auto w-full">
        <!-- Dashboard Content Container with subtle fade-in and Error Boundary fallback -->
        <div class="w-full max-w-[100rem] mx-auto animate-[fade-in-up_0.7s_ease-out_forwards]">
          <div v-if="hasViewError" class="rounded-xl border border-red-200 bg-red-50 p-6 text-red-700">
            <h3 class="text-lg font-bold mb-2">View Load Error</h3>
            <p class="text-sm mb-4">{{ viewErrorMessage || 'An unexpected error occurred in this view.' }}</p>
            <button
              class="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700"
              @click="resetViewError"
            >
              Retry View
            </button>
          </div>
          <router-view v-else />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted, watch, onErrorCaptured } from 'vue';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '@/stores/authStore';
import { useAdminStore } from '@/stores/adminStore';
import { PERMISSIONS } from '@/constants/permissions';
import AdminNavIcon from '@/components/admin/AdminNavIcon.vue';

const { t } = useI18n();
const authStore = useAuthStore();
const adminStore = useAdminStore();
const isSidebarOpen = ref(false);
const sidebarRef = ref<HTMLElement | null>(null);
const toggleButtonRef = ref<HTMLButtonElement | null>(null);

const hasViewError = ref(false);
const viewErrorMessage = ref('');

onErrorCaptured((err: unknown) => {
  hasViewError.value = true;
  viewErrorMessage.value = err instanceof Error ? err.message : String(err);
  return false;
});

function resetViewError(): void {
  hasViewError.value = false;
  viewErrorMessage.value = '';
}

const pendingReportsCount = computed(() => adminStore.stats.pending_reports);

function canAccess(permission: string): boolean {
  return authStore.isAdmin || authStore.hasPermission(permission);
}

function handleKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape' && isSidebarOpen.value) {
    isSidebarOpen.value = false;
    toggleButtonRef.value?.focus();
  }
}

watch(isSidebarOpen, (open) => {
  if (open) {
    window.addEventListener('keydown', handleKeydown);
    sidebarRef.value?.focus();
  } else {
    window.removeEventListener('keydown', handleKeydown);
  }
});

onMounted(() => {
  adminStore.subscribeToReports(canAccess(PERMISSIONS.REPORTS_READ));
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown);
  adminStore.unsubscribeReports();
});
</script>

