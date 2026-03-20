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

      const response = await apiV1.get<{ data: T[]; total: number }>(
        `${options.endpoint}?${params.toString()}`
      );
      items.value = response.data;
      totalItems.value = response.total;
      selectedIds.value = [];
      page.value = newPage;
    } catch (e) {
      console.error(`Failed to load data from ${options.endpoint}`, e);
    } finally {
      isLoading.value = false;
    }
  };

  const exportData = async (
    extraParams: Record<string, string | null | undefined> = {}
  ): Promise<void> => {
    try {
      const params = new URLSearchParams({ limit: '5000', offset: '0' });
      Object.entries(extraParams).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });

      const response = await apiV1.get<{ data: T[]; total: number }>(
        `${options.endpoint}?${params.toString()}`
      );
      const data = response.data;

      if (!data || data.length === 0) {
        toast({ description: 'No data to export', variant: 'default' });
        return;
      }

      const csvContent = [
        options.exportHeaders.join(','),
        ...data.map((item) => options.formatExportRow(item).join(',')),
      ].join('\n');

      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
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

      toast({ description: 'Data exported successfully', variant: 'success' });
    } catch (e) {
      console.error(`Failed to export data from ${options.endpoint}`, e);
      toast({
        title: 'Error',
        description: 'Failed to export data',
        variant: 'destructive',
      });
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
