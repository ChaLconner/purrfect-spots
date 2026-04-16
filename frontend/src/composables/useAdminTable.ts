import { ref, computed } from 'vue';
import { apiV1 } from '@/utils/api';
import { useToast } from '@/components/toast/use-toast';

interface UseAdminTableOptions<T> {
  endpoint: string;
  limit?: number;
  exportHeaders: string[];
  formatExportRow: (item: T) => string[];
  exportFileNamePrefix: string;
  defaultSortBy?: string;
  defaultSortOrder?: 'asc' | 'desc';
}

export function useAdminTable<T extends { id: string }>(
  options: UseAdminTableOptions<T>
): {
  items: ReturnType<typeof ref<T[]>>;
  totalItems: ReturnType<typeof ref<number>>;
  page: ReturnType<typeof ref<number>>;
  limit: number;
  isLoading: ReturnType<typeof ref<boolean>>;
  selectedIds: ReturnType<typeof ref<string[]>>;
  isAllSelected: ReturnType<typeof computed<boolean>>;
  sortBy: ReturnType<typeof ref<string>>;
  sortOrder: ReturnType<typeof ref<'asc' | 'desc'>>;
  toggleSelection: (id: string) => void;
  toggleSelectAll: () => void;
  loadData: (
    newPage?: number,
    extraParams?: Record<string, string | null | undefined>
  ) => Promise<void>;
  exportData: (extraParams?: Record<string, string | null | undefined>) => Promise<void>;
} {
  const { toast } = useToast();

  const items = ref<T[]>([]);
  const totalItems = ref(0);
  const page = ref(1);
  const limit = options.limit || 20;
  const isLoading = ref(false);
  const selectedIds = ref<string[]>([]);

  const sortBy = ref(options.defaultSortBy || 'created_at');
  const sortOrder = ref<'asc' | 'desc'>(options.defaultSortOrder || 'desc');

  const isAllSelected = computed(() => {
    return items.value.length > 0 && selectedIds.value.length === items.value.length;
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
      selectedIds.value = [];
    } else {
      selectedIds.value = items.value.map((item) => item.id);
    }
  };

  const loadData = async (
    newPage: number = 1,
    extraParams: Record<string, string | null | undefined> = {}
  ): Promise<void> => {
    isLoading.value = true;
    try {
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
        `${options.endpoint}?${params.toString()}`
      );
      items.value = response.data || response.items || [];
      totalItems.value = response.total || items.value.length;
      selectedIds.value = [];
      page.value = newPage;
    } catch (e) {
      console.error({
        message: 'Failed to load admin table data',
        endpoint: options.endpoint,
        error: e,
      });
    } finally {
      isLoading.value = false;
    }
  };

  const exportData = async (
    extraParams: Record<string, string | null | undefined> = {}
  ): Promise<void> => {
    isLoading.value = true;
    try {
      const MAX_BATCH_SIZE = 100;
      const MAX_CONCURRENT_BATCHES = 5;
      let allData: T[] = [];
      let total = 0;
      let offset = 0;

      // Initial fetch to get total and first batch
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
        `${options.endpoint}?${params.toString()}`
      );

      const firstBatch = firstResponse.data || firstResponse.items || [];
      allData = [...firstBatch];
      total = firstResponse.total || firstBatch.length;

      // Fetch subsequent batches in small parallel groups to reduce total export time
      const remainingOffsets: number[] = [];
      for (offset = MAX_BATCH_SIZE; offset < total; offset += MAX_BATCH_SIZE) {
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
              `${options.endpoint}?${nextParams.toString()}`
            );
          })
        );

        responses.forEach((response) => {
          const nextBatch = response.data || response.items || [];
          allData.push(...nextBatch);
        });
      }

      if (allData.length === 0) {
        toast({ description: 'No data to export', variant: 'default' });
        return;
      }

      // Helper to escape CSV values
      const escapeCSV = (val: unknown): string => {
        if (val === null || val === undefined) return '';
        const s = String(val);
        if (s.includes(',') || s.includes('"') || s.includes('\n')) {
          return `"${s.replace(/"/g, '""')}"`;
        }
        return s;
      };

      const csvContent = [
        options.exportHeaders.join(','),
        ...allData.map((item) => options.formatExportRow(item).map(escapeCSV).join(',')),
      ].join('\n');

      // Use BOM for UTF-8 visibility in Excel
      const blob = new Blob([new Uint8Array([0xef, 0xbb, 0xbf]), csvContent], {
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
    } catch (e) {
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
