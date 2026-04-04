<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '@/store/authStore';
import { apiV1 } from '@/utils/api';
import { showSuccess, showError } from '@/store/toast';
import { PERMISSIONS } from '@/constants/permissions';
import BaseButton from '@/components/ui/BaseButton.vue';
import SkeletonLoader from '@/components/ui/SkeletonLoader.vue';
import TableSkeleton from '@/components/ui/TableSkeleton.vue';

interface SecuritySummary {
  alerts: {
    total: number;
    critical: number;
    warnings: number;
  };
  sessions: {
    active: number;
    concurrent_users: number;
    peak_today: number;
  };
  recent?: Array<{
    type: string;
    level: 'critical' | 'warning' | 'info';
    timestamp: string;
    details: string;
  }>;
}

const { t } = useI18n();
const authStore = useAuthStore();
const summary = ref<SecuritySummary | null>(null);
const loading = ref(true);
const resetting = ref(false);

const fetchSummary = async (): Promise<void> => {
  loading.value = true;
  try {
    const data = await apiV1.get<SecuritySummary>('/admin/security/summary');
    summary.value = data;
  } catch (error) {
    console.error('Failed to fetch security summary:', error);
    showError(t('admin.security.errorLoad'));
  } finally {
    loading.value = false;
  }
};

const resetAlerts = async (): Promise<void> => {
  resetting.value = true;
  try {
    await apiV1.post('/admin/security/alerts/reset', {});
    showSuccess(t('admin.security.alertsReset'));
    await fetchSummary();
  } catch (error) {
    console.error('Failed to reset alerts:', error);
    showError(t('admin.security.errorReset'));
  } finally {
    resetting.value = false;
  }
};

const resetSessions = async (): Promise<void> => {
  resetting.value = true;
  try {
    await apiV1.post('/admin/security/sessions/reset', {});
    showSuccess(t('admin.security.sessionsReset'));
    await fetchSummary();
  } catch (error) {
    console.error('Failed to reset sessions:', error);
    showError(t('admin.security.errorReset'));
  } finally {
    resetting.value = false;
  }
};

onMounted(fetchSummary);

const getStatusColor = (level: string): string => {
  switch (level) {
    case 'critical': return 'text-terracotta-600 bg-terracotta-50 border-terracotta-100';
    case 'warning': return 'text-amber-600 bg-amber-50 border-amber-100';
    default: return 'text-sage-600 bg-sage-50 border-sage-100';
  }
};

const formatTime = (timestamp: string): string => {
  return new Date(timestamp).toLocaleString();
};
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
      <div class="flex flex-col gap-1">
        <h1 class="text-2xl sm:text-3xl font-bold text-brown-900 font-display tracking-tight">
          {{ t('admin.security.title') }}
        </h1>
        <p class="text-sm sm:text-base text-brown-500 font-medium">{{ t('admin.security.subtitle') }}</p>
      </div>

      <div class="flex justify-start sm:justify-end gap-2">
        <BaseButton 
          variant="sage" 
          size="sm" 
          :loading="loading" 
          class="w-full sm:w-auto shadow-sm"
          @click="fetchSummary"
        >
          <div class="flex items-center justify-center gap-2">
            <svg v-if="!loading" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8" /><path d="M21 3v5h-5" /></svg>
            {{ t('common.refresh') }}
          </div>
        </BaseButton>
      </div>
    </div>

    <!-- Perceived Performance Skeleton State -->
    <div v-if="loading && !summary" class="space-y-8">
      <!-- Stats Grid Skeleton -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        <div
          v-for="n in 4"
          :key="n"
          class="bg-white p-4 sm:p-6 rounded-2xl shadow-sm border border-sand-100 flex flex-col justify-between"
        >
          <div class="flex justify-between items-start mb-4">
            <SkeletonLoader width="48px" height="48px" border-radius="1rem" />
            <SkeletonLoader v-if="n === 1" width="36px" height="18px" border-radius="1rem" />
          </div>
          <div class="space-y-2">
            <SkeletonLoader width="60%" height="0.875rem" />
            <SkeletonLoader width="40%" height="2rem" />
          </div>
          <div class="mt-6 pt-4 border-t border-sand-50/50 flex flex-wrap gap-3">
            <SkeletonLoader width="35%" height="0.75rem" />
            <SkeletonLoader width="35%" height="0.75rem" />
          </div>
        </div>
      </div>

      <!-- Action Area Skeleton -->
      <div 
        v-if="authStore.hasPermission(PERMISSIONS.SYSTEM_SETTINGS)" 
        class="flex flex-col sm:flex-row gap-3 mt-4 sm:mt-8"
      >
        <SkeletonLoader width="100%" height="42px" border-radius="1rem" class="sm:max-w-[160px]" />
        <SkeletonLoader width="100%" height="42px" border-radius="1rem" class="sm:max-w-[160px]" />
      </div>

      <!-- Recent Alerts Skeleton -->
      <div class="bg-white rounded-2xl sm:rounded-3xl p-4 sm:p-8 border border-sand-200 shadow-sm">
        <div class="flex items-center justify-between mb-8">
          <SkeletonLoader width="250px" height="2rem" border-radius="0.75rem" />
          <SkeletonLoader width="150px" height="1rem" border-radius="0.5rem" />
        </div>
        <div class="overflow-x-auto rounded-2xl border border-brown-50">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-brown-50/50">
                <th v-for="i in 4" :key="i" class="p-4">
                  <SkeletonLoader width="40%" height="0.75rem" />
                </th>
              </tr>
            </thead>
            <tbody>
              <TableSkeleton :rows="5" :columns="4" />
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div v-else-if="summary" class="space-y-8">
      <!-- Top Stats Grid -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        <!-- Alerts Card -->
        <div class="group bg-white p-5 sm:p-6 rounded-2xl shadow-sm border border-sand-100 transition-all hover:shadow-md hover:border-terracotta-100 flex flex-col">
          <div class="flex justify-between items-start mb-4">
            <div class="p-3 bg-terracotta-50 rounded-2xl group-hover:scale-110 transition-transform">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-terracotta-600"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" /><path d="M12 9v4" /><path d="M12 17h.01" /></svg>
            </div>
            <span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-terracotta-100 text-terracotta-700 uppercase tracking-widest animate-pulse">Live</span>
          </div>
          <h3 class="text-brown-500 font-bold text-xs mb-1 uppercase tracking-widest group-hover:text-brown-700 transition-colors">{{ t('admin.security.totalAlerts') }}</h3>
          <div class="text-3xl font-bold text-brown-900 group-hover:text-terracotta-600 transition-colors">{{ summary.alerts.total }}</div>
          <div class="mt-auto pt-4 border-t border-sand-50 flex flex-wrap gap-x-4 gap-y-2 text-[10px] font-bold uppercase tracking-wide">
            <div class="text-terracotta-600 flex items-center gap-1.5 min-w-fit">
              <span class="w-1.5 h-1.5 rounded-full bg-terracotta-500 flex-shrink-0"></span>
              {{ summary.alerts.critical }} {{ t('admin.security.criticalAlerts') }}
            </div>
            <div class="text-amber-600 flex items-center gap-1.5 min-w-fit">
              <span class="w-1.5 h-1.5 rounded-full bg-amber-500 flex-shrink-0"></span>
              {{ summary.alerts.warnings }} {{ t('admin.security.warnings') }}
            </div>
          </div>
        </div>

        <!-- Sessions Card -->
        <div class="group bg-white p-5 sm:p-6 rounded-2xl shadow-sm border border-sand-100 transition-all hover:shadow-md hover:border-sage-100 flex flex-col">
          <div class="flex justify-between items-start mb-4">
            <div class="p-3 bg-sage-50 rounded-2xl group-hover:scale-110 transition-transform">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-sage-600"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M22 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" /></svg>
            </div>
          </div>
          <h3 class="text-brown-500 font-bold text-xs mb-1 uppercase tracking-widest group-hover:text-brown-700 transition-colors">{{ t('admin.security.activeSessions') }}</h3>
          <div class="text-3xl font-bold text-brown-900 group-hover:text-sage-600 transition-colors">{{ summary.sessions.active }}</div>
          <div class="mt-auto pt-4 border-t border-sand-50 text-[10px] font-bold uppercase tracking-widest text-sage-600 flex flex-wrap items-center gap-1.5">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="flex-shrink-0"><path d="M22 12h-4l-3 9L9 3l-3 9H2" /></svg>
            <span class="min-w-fit">{{ summary.sessions.concurrent_users }} {{ t('admin.security.concurrent' ) || 'Users' }}</span>
          </div>
        </div>

        <!-- Peak Activity -->
        <div class="group bg-white p-5 sm:p-6 rounded-2xl shadow-sm border border-sand-100 transition-all hover:shadow-md hover:border-brown-100 flex flex-col">
          <div class="flex justify-between items-start mb-4">
            <div class="p-3 bg-brown-50 rounded-2xl group-hover:scale-110 transition-transform">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-brown-600"><path d="M12 20v-6M6 20V10M18 20V4" /><path d="m8 6 4-4 4 4" /></svg>
            </div>
          </div>
          <h3 class="text-brown-500 font-bold text-xs mb-1 uppercase tracking-widest group-hover:text-brown-700 transition-colors">{{ t('admin.security.peakToday') }}</h3>
          <div class="text-3xl font-bold text-brown-900">{{ summary.sessions.peak_today }}</div>
          <p class="mt-auto pt-4 border-t border-sand-50 text-[10px] font-bold text-brown-400 group-hover:text-brown-600 transition-colors uppercase tracking-wider">{{ t('admin.security.dailyRecord') }}</p>
        </div>

        <!-- Protection Level -->
        <div class="group bg-white p-5 sm:p-6 rounded-2xl shadow-sm border border-sand-100 transition-all hover:shadow-md hover:border-sage-100 relative overflow-hidden flex flex-col">
          <div class="absolute -right-4 -bottom-4 opacity-10 transform rotate-12 group-hover:scale-125 transition-transform duration-700">
            <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" class="text-sage-600"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>
          </div>
          <div class="flex justify-between items-start mb-4 relative z-10">
            <div class="p-3 bg-sage-50 rounded-2xl group-hover:scale-110 transition-transform">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-sage-600"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>
            </div>
          </div>
          <h3 class="text-brown-500 font-bold text-xs mb-1 uppercase tracking-widest group-hover:text-brown-700 transition-colors relative z-10">{{ t('admin.security.protectionStatus') }}</h3>
          <div class="text-3xl font-bold text-sage-600 relative z-10">{{ t('admin.security.protected') }}</div>
          <div class="flex items-center flex-wrap gap-2 mt-auto pt-4 border-t border-sand-50 text-sage-600 relative z-10 font-bold text-[10px] uppercase tracking-wider">
            <span class="flex h-2 w-2 relative flex-shrink-0">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-sage-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2 w-2 bg-sage-500"></span>
            </span>
            <span class="min-w-fit">{{ t('admin.security.activeMonitoring') }}</span>
          </div>
        </div>
      </div>

      <!-- Action Area -->
      <div v-if="authStore.hasPermission(PERMISSIONS.SYSTEM_SETTINGS)" class="flex flex-col sm:flex-row gap-3 mt-4 sm:mt-8">
        <BaseButton variant="terracotta" size="sm" :loading="resetting" class="w-full sm:w-auto shadow-sm font-bold text-[11px] px-6" @click="resetAlerts">
          <div class="flex items-center justify-center gap-2 uppercase tracking-widest">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" /><path d="M3 3v5h5" /></svg>
            {{ t('admin.security.resetAlerts') }}
          </div>
        </BaseButton>
        <BaseButton variant="brown" size="sm" :loading="resetting" class="w-full sm:w-auto shadow-sm font-bold text-[11px] px-6" @click="resetSessions">
          <div class="flex items-center justify-center gap-2 uppercase tracking-widest">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M22 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" /></svg>
            {{ t('admin.security.resetSessions') }}
          </div>
        </BaseButton>
      </div>

      <!-- Recent Alerts Table -->
      <div class="bg-white rounded-2xl sm:rounded-3xl p-4 sm:p-8 border border-sand-200 shadow-sm transition-all ghibli-fade-in">
        <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-8 gap-4">
          <div>
            <h2 class="text-xl font-bold text-brown-900 font-display flex items-center gap-3">
              <span class="p-2 bg-brown-50 rounded-lg group-hover:bg-brown-100 transition-colors">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-brown-600"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /><path d="M12 7v4" /><path d="M12 15h.01" /></svg>
              </span>
              {{ t('admin.security.recentAlertsTitle') }}
            </h2>
            <p class="text-xs text-brown-500 font-medium italic mt-1 ml-1">
              {{ t('admin.security.lastUpdated') }}: {{ new Date().toLocaleTimeString() }}
            </p>
          </div>
        </div>

        <div v-if="!summary.recent || summary.recent.length === 0" class="text-center py-16 bg-sand-50/30 rounded-2xl border border-dashed border-sand-200">
           <div class="mb-4 text-brown-200/60">
              <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" class="mx-auto"><path d="M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z" /><path d="m9 12 2 2 4-4" /></svg>
           </div>
           <p class="text-brown-500 text-sm font-medium">{{ t('admin.security.noRecentAlerts') }}</p>
        </div>

        <div v-else class="overflow-x-auto rounded-2xl border border-sand-100 ghibli-soft-scroll">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-sand-50/50">
                <th class="p-3 sm:p-4 text-[10px] font-bold uppercase tracking-widest text-brown-400">{{ t('admin.security.table.type') }}</th>
                <th class="p-3 sm:p-4 text-[10px] font-bold uppercase tracking-widest text-brown-400">{{ t('admin.security.table.status') }}</th>
                <th class="p-3 sm:p-4 text-[10px] font-bold uppercase tracking-widest text-brown-400">{{ t('admin.security.table.time') }}</th>
                <th class="p-3 sm:p-4 text-[10px] font-bold uppercase tracking-widest text-brown-400">{{ t('admin.security.table.details') }}</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-sand-100">
              <tr v-for="(alert, index) in summary.recent" :key="index" class="hover:bg-sand-50/50 transition-colors group">
                <td class="p-3 sm:p-4">
                  <div class="font-bold text-brown-900 group-hover:text-terracotta-600 transition-colors uppercase tracking-tight text-sm">{{ alert.type }}</div>
                </td>
                <td class="p-3 sm:p-4">
                  <span 
                    class="px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border shadow-sm"
                    :class="getStatusColor(alert.level)"
                  >
                    {{ t(`admin.security.status.${alert.level}`) }}
                  </span>
                </td>
                <td class="p-3 sm:p-4 text-xs text-brown-500 font-bold whitespace-nowrap italic">
                  {{ formatTime(alert.timestamp) }}
                </td>
                <td class="p-3 sm:p-4">
                   <p class="text-xs text-brown-600 font-medium max-w-md line-clamp-2 md:line-clamp-none">{{ alert.details }}</p>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.font-display {
  font-family: 'Outfit', sans-serif;
}

.ghibli-fade-in {
  animation: fadeIn 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.ghibli-soft-scroll::-webkit-scrollbar {
  height: 6px;
  width: 6px;
}
.ghibli-soft-scroll::-webkit-scrollbar-track {
  background: transparent;
}
.ghibli-soft-scroll::-webkit-scrollbar-thumb {
  background: #e7e5e4;
  border-radius: 10px;
}
.ghibli-soft-scroll::-webkit-scrollbar-thumb:hover {
  background: #d6d3d1;
}
</style>
