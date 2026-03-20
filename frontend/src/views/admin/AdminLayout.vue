<template>
  <div class="min-h-screen bg-sand-50 flex pt-16">
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
      class="w-64 bg-white border-r border-sand-200 fixed inset-y-0 left-0 pt-16 z-40 transition-transform duration-300 md:translate-x-0"
      :class="isSidebarOpen ? 'translate-x-0' : '-translate-x-full'"
    >
      <div class="h-full flex flex-col">
        <nav class="flex-1 px-4 space-y-2 mt-6">
          <router-link
            to="/admin"
            class="flex items-center px-4 py-2 rounded-lg text-brown-600 hover:bg-sand-50 hover:text-brown-900 transition-colors group"
            active-class=""
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
            Dashboard
          </router-link>

          <router-link
            v-if="authStore.hasPermission(PERMISSIONS.USERS_READ)"
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
            Users
          </router-link>

          <router-link
            v-if="authStore.hasPermission(PERMISSIONS.CONTENT_READ)"
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
            Content
          </router-link>

          <router-link
            v-if="
              authStore.hasPermission(PERMISSIONS.REPORTS_READ) ||
              authStore.hasPermission(PERMISSIONS.CONTENT_READ)
            "
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
            <span class="flex-1">Reports</span>
            <span
              v-if="pendingReportsCount > 0"
              class="ml-2 bg-red-500 text-white text-xs font-bold px-2 py-0.5 rounded-full shadow-sm tabular-nums flex-shrink-0"
            >
              {{ pendingReportsCount > 99 ? '99+' : pendingReportsCount }}
            </span>
          </router-link>

          <router-link
            v-if="authStore.hasPermission(PERMISSIONS.AUDIT_READ)"
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
            Audit Logs
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
              Back to Site
            </router-link>
          </div>
        </nav>
      </div>
    </aside>

    <!-- Main Content -->
    <div class="flex-1 flex flex-col md:pl-64 min-w-0 transition-all duration-300">
      <main class="flex-1 py-12 px-4 sm:px-6 lg:px-8 mt-8 md:mt-0">
        <!-- Added mt-8 for mobile toggle spacing -->
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useAuthStore } from '@/store/authStore';
import { useAdminStore } from '@/store/adminStore';
import { PERMISSIONS } from '@/constants/permissions';

const authStore = useAuthStore();
const adminStore = useAdminStore();
const isSidebarOpen = ref(false);

const pendingReportsCount = computed(() => adminStore.stats.pending_reports);

onMounted(() => {
  adminStore.fetchStats();
});
</script>
