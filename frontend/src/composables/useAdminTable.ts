import { ref, computed, hasInjectionContext, type ComputedRef, type Ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { apiV1 } from '@/utils/api';
import { useToast } from '@/composables/useToast';

interface UseAdminTableOptions<T> {
  endpoint: string;
  limit?: number;
  exportMaxRows?: number;
  exportBatchSize?: number;
  exportConcurrentBatches?: number;
  exportHeaders: string[];
  formatExportRow: (item: T) => string[];
  exportFileNamePrefix: string;
  defaultSortBy?: string;
  defaultSortOrder?: 'asc' | 'desc';
  syncWithRouter?: boolean;
}

export function useAdminTable<T extends { id: string }>(
  options: UseAdminTableOptions<T>
): {
  items: Ref<T[]>;
  totalItems: Ref<number>;
  page: Ref<number>;
  limit: number;
  isLoading: Ref<boolean>;
  selectedIds: Ref<string[]>;
  isAllSelected: ComputedRef<boolean>;
  sortBy: Ref<string>;
  sortOrder: Ref<'asc' | 'desc'>;
  toggleSelection: (id: string) => void;
  toggleSelectAll: () => void;
  loadData: (
    newPage?: number,
    extraParams?: Record<string, string | null | undefined>
  ) => Promise<void>;
  exportData: (extraParams?: Record<string, string | null | undefined>) => Promise<void>;
} {
  const { toast } = useToast();
  const route = (options.syncWithRouter !== false && hasInjectionContext()) ? useRoute() : null;
  const router = (options.syncWithRouter !== false && hasInjectionContext()) ? useRouter() : null;

  const items = ref<T[]>([]) as unknown as Ref<T[]>;
  const totalItems = ref(0);
  const page = ref(1);
  const limit = options.limit || 20;
  const isLoading = ref(false);
  const selectedIds = ref<string[]>([]);

  const initialSortBy = (route?.query?.sortBy as string) || options.defaultSortBy || 'created_at';
  const initialSortOrder = (route?.query?.sortOrder as 'asc' | 'desc') || options.defaultSortOrder || 'desc';

  const sortBy = ref(initialSortBy);
  const sortOrder = ref<'asc' | 'desc'>(initialSortOrder);

  const isAllSelected = computed(() => {
    return items.value.length > 0 && items.value.every((item) => selectedIds.value.includes(item.id));
  });

  const toggleSelection = (id: string): void => {
    if (selectedIds.value.includes(id)) {
      selectedIds.value = selectedIds.value.filter((item) => item !== id);
    } else {
      selectedIds.value.push(id);
    }
  };

  const toggleSelectAll = (): void => {
    if (isAllSelected.value) {
      const pageIds = items.value.map((i) => i.id);
      selectedIds.value = selectedIds.value.filter((id) => !pageIds.includes(id));
    } else {
      const pageIds = items.value.map((i) => i.id);
      const newIds = new Set([...selectedIds.value, ...pageIds]);
      selectedIds.value = Array.from(newIds);
    }
  };

  let activeAbortController: AbortController | null = null;

  const loadData = async (
    newPage: number = 1,
    extraParams: Record<string, string | null | undefined> = {}
  ): Promise<void> => {
    if (activeAbortController) {
      activeAbortController.abort();
    }
    activeAbortController = new AbortController();
    const currentSignal = activeAbortController.signal;

    isLoading.value = true;
    try {
      if (router && route) {
        void router.replace({
          query: {
            ...route.query,
            page: newPage > 1 ? newPage.toString() : undefined,
            sortBy: sortBy.value !== (options.defaultSortBy || 'created_at') ? sortBy.value : undefined,
            sortOrder: sortOrder.value !== (options.defaultSortOrder || 'desc') ? sortOrder.value : undefined,
          },
        });
      }

      const offset = (newPage - 1) * limit;
      const params = new URLSearchParams({
        limit: limit.toString(),
        offset: offset.toString(),
        sort: sortBy.value,
        order: sortOrder.value,
      });

      Object.entries(extraParams).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });

      const response = await apiV1.get<{ data?: T[]; items?: T[]; total?: number }>(
        `${options.endpoint}?${params.toString()}`,
        { signal: currentSignal }
      );
      items.value = response.data || response.items || [];
      totalItems.value = response.total || items.value.length;
      page.value = newPage;
    } catch (e: unknown) {
      if ((e as { name?: string })?.name === 'CanceledError' || (e as { name?: string })?.name === 'AbortError') {
        return;
      }
      console.error({
        message: 'Failed to load admin table data',
        endpoint: options.endpoint,
        error: e,
      });
    } finally {
      if (activeAbortController?.signal === currentSignal) {
        isLoading.value = false;
      }
    }
  };

  const exportData = async (
    extraParams: Record<string, string | null | undefined> = {}
  ): Promise<void> => {
    isLoading.value = true;
    const exportController = new AbortController();
    const signal = exportController.signal;

    try {
      const MAX_BATCH_SIZE = options.exportBatchSize ?? 100;
      const MAX_CONCURRENT_BATCHES = options.exportConcurrentBatches ?? 3;
      const EXPORT_MAX_ROWS = options.exportMaxRows ?? 2000;
      let total = 0;
      let offset = 0;

      const escapeCSV = (val: unknown): string => {
        if (val === null || val === undefined) return '';
        const s = String(val);
        if (s.includes(',') || s.includes('"') || s.includes('\n')) {
          return `"${s.replace(/"/g, '""')}"`;
        }
        return s;
      };

      const csvChunks: string[] = [options.exportHeaders.join(',') + '\n'];

      // Initial fetch
      const params = new URLSearchParams({
        limit: MAX_BATCH_SIZE.toString(),
        offset: offset.toString(),
        sort: sortBy.value,
        order: sortOrder.value,
      });

      Object.entries(extraParams).forEach(([key, value]) => {
        if (value !== undefined && value !== null) params.append(key, value);
      });

      const firstResponse = await apiV1.get<{ data?: T[]; items?: T[]; total?: number }>(
        `${options.endpoint}?${params.toString()}`,
        { signal }
      );

      const firstBatch = firstResponse.data || firstResponse.items || [];
      if (firstBatch.length === 0) {
        toast({ description: 'No data to export', variant: 'default' });
        return;
      }

      total = firstResponse.total || firstBatch.length;
      const cappedTotal = Math.min(total, EXPORT_MAX_ROWS);

      const formattedFirstBatch = firstBatch.slice(0, EXPORT_MAX_ROWS).map((item) =>
        options.formatExportRow(item).map(escapeCSV).join(',')
      );
      if (formattedFirstBatch.length > 0) {
        csvChunks.push(formattedFirstBatch.join('\n') + '\n');
      }

      if (total > EXPORT_MAX_ROWS) {
        toast({
          title: 'Large export limited',
          description: `Exported first ${EXPORT_MAX_ROWS.toLocaleString()} rows to keep admin responsive.`,
          variant: 'default',
        });
      }

      const remainingOffsets: number[] = [];
      for (offset = MAX_BATCH_SIZE; offset < cappedTotal; offset += MAX_BATCH_SIZE) {
        remainingOffsets.push(offset);
      }

      for (let i = 0; i < remainingOffsets.length; i += MAX_CONCURRENT_BATCHES) {
        const chunk = remainingOffsets.slice(i, i + MAX_CONCURRENT_BATCHES);
        const responses = await Promise.all(
          chunk.map(async (chunkOffset) => {
            const nextParams = new URLSearchParams({
              limit: MAX_BATCH_SIZE.toString(),
              offset: chunkOffset.toString(),
              sort: sortBy.value,
              order: sortOrder.value,
            });

            Object.entries(extraParams).forEach(([key, value]) => {
              if (value !== undefined && value !== null) nextParams.append(key, value);
            });

            return apiV1.get<{ data?: T[]; items?: T[]; total?: number }>(
              `${options.endpoint}?${nextParams.toString()}`,
              { signal }
            );
          })
        );

        responses.forEach((response) => {
          const batch = response.data || response.items || [];
          const rows = batch.map((item) => options.formatExportRow(item).map(escapeCSV).join(','));
          if (rows.length > 0) {
            csvChunks.push(rows.join('\n') + '\n');
          }
        });
      }

      // Use BOM for UTF-8 visibility in Excel
      const fullCsvContent = csvChunks.join('');
      const blob = new Blob([new Uint8Array([0xef, 0xbb, 0xbf]), fullCsvContent], {
        type: 'text/csv;charset=utf-8;',
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.setAttribute('href', url);
      link.setAttribute(
        'download',
        `${options.exportFileNamePrefix}_${new Date().toISOString().split('T')[0]}.csv`
      );
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      toast({ description: 'Data exported successfully', variant: 'success' });
    } catch (e: unknown) {
      if ((e as { name?: string })?.name === 'CanceledError' || (e as { name?: string })?.name === 'AbortError') {
        return;
      }
      console.error({
        message: 'Failed to export admin table data',
        endpoint: options.endpoint,
        error: e,
      });
      toast({
        title: 'Error',
        description: 'Failed to export data',
        variant: 'destructive',
      });
    } finally {
      isLoading.value = false;
    }
  };

  return {
    items,
    totalItems,
    page,
    limit,
    isLoading,
    selectedIds,
    isAllSelected,
    sortBy,
    sortOrder,
    toggleSelection,
    toggleSelectAll,
    loadData,
    exportData,
  };
}
