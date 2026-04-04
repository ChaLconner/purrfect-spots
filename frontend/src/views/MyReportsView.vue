<template>
  <div class="min-h-screen pt-24 pb-12 px-4 sm:px-6 lg:px-8 bg-stone-50">
    <GhibliBackground />
    <div class="max-w-3xl mx-auto relative z-10">
      <div class="text-center mb-8">
        <h1 class="text-3xl font-heading font-black text-brown mb-2">
          {{ $t('myReports.title') }}
        </h1>
        <p class="text-brown-light font-body">
          {{ $t('myReports.subtitle') }}
        </p>
      </div>

      <div
        class="bg-white/80 backdrop-blur-md rounded-3xl shadow-xl overflow-hidden border border-white/50"
      >
        <div v-if="loading" class="p-12 flex justify-center">
          <GhibliLoader :text="$t('myReports.loading')" />
        </div>

        <div v-else-if="reports.length === 0" class="p-12 text-center text-stone-500">
          {{ $t('myReports.empty') }}
        </div>

        <div v-else class="divide-y divide-stone-100">
          <div
            v-for="report in reports"
            :key="report.id"
            class="p-5 hover:bg-stone-50/50 transition-colors"
          >
            <div class="flex items-start justify-between gap-4">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-3 mb-1">
                  <span
                    :class="[
                      'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                      statusClass(report.status),
                    ]"
                  >
                    {{ $t(`myReports.status.${report.status}`) }}
                  </span>
                  <span class="text-xs text-stone-400">
                    {{ formatDate(report.created_at) }}
                  </span>
                </div>
                <p class="text-sm font-medium text-brown mt-1">
                  {{ $t(`myReports.reasons.${report.reason}`, report.reason) }}
                </p>
                <p v-if="report.details" class="text-sm text-stone-500 mt-1 truncate">
                  {{ report.details }}
                </p>
                <p
                  v-if="report.resolution_notes"
                  class="text-xs text-stone-400 mt-2 italic"
                >
                  {{ $t('myReports.resolutionNotes') }}: {{ report.resolution_notes }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { ReportService, type Report } from '@/services/reportService';
import { showError } from '@/store/toast';
import GhibliBackground from '@/components/ui/GhibliBackground.vue';
import GhibliLoader from '@/components/ui/GhibliLoader.vue';
import { useSeo } from '@/composables/useSeo';

const { t } = useI18n();
const { setMetaTags } = useSeo();
const loading = ref(true);
const reports = ref<Report[]>([]);

const statusClass = (status: string): string => {
  switch (status) {
    case 'pending':
      return 'bg-amber-100 text-amber-800';
    case 'resolved':
      return 'bg-green-100 text-green-800';
    case 'dismissed':
      return 'bg-stone-100 text-stone-600';
    default:
      return 'bg-stone-100 text-stone-600';
  }
};

const formatDate = (dateStr: string): string => {
  return new Date(dateStr).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

const fetchReports = async (): Promise<void> => {
  loading.value = true;
  try {
    reports.value = await ReportService.getMyReports();
  } catch {
    showError(t('myReports.errorLoad'));
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  setMetaTags({
    title: `${t('myReports.title')} | Purrfect Spots`,
    description: t('myReports.subtitle'),
  });
  fetchReports();
});
</script>
