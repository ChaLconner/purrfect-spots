<template>
  <div class="min-h-screen bg-sand-50 pb-12 pt-24 px-4 sm:px-6 lg:px-8">
    <div class="max-w-7xl mx-auto space-y-8">
      <!-- Header -->
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 class="text-3xl font-bold text-brown-900 font-display">Admin Dashboard</h1>
          <p class="mt-1 text-brown-600">Manage users and content.</p>
        </div>
        <div class="flex gap-4">
          <!-- Stats Cards will go here -->
        </div>
      </div>

      <!-- Stats Grid -->
      <div v-if="stats" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="bg-white p-6 rounded-2xl shadow-sm border border-sand-100">
          <h3 class="text-sm font-medium text-brown-500 uppercase tracking-wider">Total Users</h3>
          <p class="mt-2 text-3xl font-bold text-brown-900">{{ stats.total_users }}</p>
        </div>
        <div class="bg-white p-6 rounded-2xl shadow-sm border border-sand-100">
          <h3 class="text-sm font-medium text-brown-500 uppercase tracking-wider">Total Photos</h3>
          <p class="mt-2 text-3xl font-bold text-terracotta-600">{{ stats.total_photos }}</p>
        </div>
      </div>

      <!-- User Management -->
      <div class="bg-white rounded-2xl shadow-sm border border-sand-100 overflow-hidden">
        <div
          class="p-6 border-b border-sand-100 flex flex-col sm:flex-row justify-between items-center gap-4"
        >
          <h2 class="text-xl font-bold text-brown-900">Users</h2>
          <div class="relative max-w-xs w-full">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search users..."
              class="w-full pl-10 pr-4 py-2 border border-sand-300 rounded-lg focus:ring-2 focus:ring-terracotta-500 focus:border-terracotta-500 transition-colors"
              @input="handleSearch"
            />
            <div class="absolute left-3 top-1/2 -translate-y-1/2 text-brown-400">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </div>
          </div>
        </div>

        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-sand-200">
            <thead class="bg-sand-50">
              <tr>
                <th
                  scope="col"
                  class="px-6 py-3 text-left text-xs font-medium text-brown-500 uppercase tracking-wider"
                >
                  User
                </th>
                <th
                  scope="col"
                  class="px-6 py-3 text-left text-xs font-medium text-brown-500 uppercase tracking-wider"
                >
                  Role
                </th>
                <th
                  scope="col"
                  class="px-6 py-3 text-left text-xs font-medium text-brown-500 uppercase tracking-wider"
                >
                  Joined
                </th>
                <th
                  scope="col"
                  class="px-6 py-3 text-right text-xs font-medium text-brown-500 uppercase tracking-wider"
                >
                  Actions
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-sand-200">
              <tr v-for="user in users" :key="user.id" class="hover:bg-sand-50 transition-colors">
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex items-center">
                    <div class="h-10 w-10 flex-shrink-0">
                      <img
                        class="h-10 w-10 rounded-full object-cover"
                        :src="
                          user.picture ||
                            `https://ui-avatars.com/api/?name=${user.name}&background=random`
                        "
                        :alt="user.name"
                      />
                    </div>
                    <div class="ml-4">
                      <div class="text-sm font-medium text-brown-900">{{ user.name }}</div>
                      <div class="text-sm text-brown-500">{{ user.email }}</div>
                    </div>
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span
                    class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full"
                    :class="
                      user.role === 'admin'
                        ? 'bg-terracotta-100 text-terracotta-800'
                        : 'bg-green-100 text-green-800'
                    "
                  >
                    {{ user.role }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-brown-500">
                  {{ new Date(user.created_at).toLocaleDateString() }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <button
                    v-if="user.role !== 'admin'"
                    class="text-red-600 hover:text-red-900 font-medium transition-colors"
                    @click="confirmDelete(user)"
                  >
                    Delete/Ban
                  </button>
                </td>
              </tr>
              <tr v-if="users.length === 0">
                <td colspan="4" class="px-6 py-12 text-center text-brown-500">No users found.</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div
          v-if="users.length > 0"
          class="px-6 py-4 border-t border-sand-200 flex items-center justify-between"
        >
          <button
            :disabled="page === 1"
            class="px-4 py-2 border border-sand-300 rounded-md text-sm font-medium text-brown-700 bg-white hover:bg-sand-50 disabled:opacity-50 disabled:cursor-not-allowed"
            @click="page > 1 && loadUsers(page - 1)"
          >
            Previous
          </button>
          <span class="text-sm text-brown-600">Page {{ page }}</span>
          <button
            :disabled="users.length < limit"
            class="px-4 py-2 border border-sand-300 rounded-md text-sm font-medium text-brown-700 bg-white hover:bg-sand-50 disabled:opacity-50 disabled:cursor-not-allowed"
            @click="loadUsers(page + 1)"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { apiV1 } from '@/utils/api';
import type { User } from '@/types/auth'; // Ensure this type is updated with 'role'

interface Stats {
  total_users: number;
  total_photos: number;
  generated_at: string;
}

const users = ref<User[]>([]);
const stats = ref<Stats | null>(null);
const searchQuery = ref('');
const page = ref(1);
const limit = 20;
const isLoading = ref(false);

const loadStats = async () => {
  try {
    stats.value = await apiV1.get<Stats>('/admin/stats');
  } catch (e) {
    console.error('Failed to load stats', e);
  }
};

const loadUsers = async (newPage: number = 1) => {
  isLoading.value = true;
  try {
    const offset = (newPage - 1) * limit;
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });
    if (searchQuery.value) {
      params.append('search', searchQuery.value);
    }

    const data = await apiV1.get<User[]>(`/admin/users?${params.toString()}`);
    users.value = data;
    page.value = newPage;
  } catch (e) {
    console.error('Failed to load users', e);
  } finally {
    isLoading.value = false;
  }
};

const handleSearch = () => {
  // Simple debounce could be added here
  loadUsers(1);
};

const confirmDelete = async (user: User) => {
  if (
    // eslint-disable-next-line no-alert
    window.confirm(
      `Are you sure you want to ban/delete user ${user.name}? This action cannot be undone.`
    )
  ) {
    try {
      await apiV1.delete(`/admin/users/${user.id}`);
      // Refresh list
      loadUsers(page.value);
      // Refresh stats
      loadStats();
    } catch (e) {
      // eslint-disable-next-line no-alert
      window.alert('Failed to delete user');
      console.error(e);
    }
  }
};

onMounted(() => {
  loadStats();
  loadUsers();
});
</script>
