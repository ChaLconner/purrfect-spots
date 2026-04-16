import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useAdminTable } from '@/composables/useAdminTable';
import { apiV1 } from '@/utils/api';

const toastMock = vi.fn();

// Mock apiV1
vi.mock('@/utils/api', () => ({
  apiV1: {
    get: vi.fn(),
  },
}));

// Mock useToast
vi.mock('@/components/toast/use-toast', () => ({
  useToast: () => ({
    toast: toastMock,
  }),
}));

describe('useAdminTable', () => {
  const options = {
    endpoint: '/test-endpoint',
    exportHeaders: ['ID', 'Name'],
    formatExportRow: (item: { id: string; name: string }) => [item.id, item.name],
    exportFileNamePrefix: 'test_export',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    toastMock.mockReset();
    // Reset global document/window mocks if any
    document.body.innerHTML = '';
  });

  it('should initialize with default values', () => {
    const table = useAdminTable(options);
    expect(table.items.value).toEqual([]);
    expect(table.totalItems.value).toBe(0);
    expect(table.page.value).toBe(1);
    expect(table.limit).toBe(20);
    expect(table.isLoading.value).toBe(false);
    expect(table.selectedIds.value).toEqual([]);
    expect(table.sortBy.value).toBe('created_at');
    expect(table.sortOrder.value).toBe('desc');
  });

  it('should initialize with custom options', () => {
    const table = useAdminTable({
      ...options,
      limit: 50,
      defaultSortBy: 'name',
      defaultSortOrder: 'asc',
    });
    expect(table.limit).toBe(50);
    expect(table.sortBy.value).toBe('name');
    expect(table.sortOrder.value).toBe('asc');
  });

  it('should toggle selection', () => {
    const table = useAdminTable(options);
    table.toggleSelection('1');
    expect(table.selectedIds.value).toEqual(['1']);
    table.toggleSelection('1');
    expect(table.selectedIds.value).toEqual([]);
  });

  it('should toggle select all', () => {
    const table = useAdminTable(options);
    table.items.value = [{ id: '1' }, { id: '2' }] as any;
    
    table.toggleSelectAll();
    expect(table.selectedIds.value).toEqual(['1', '2']);
    expect(table.isAllSelected.value).toBe(true);
    
    table.toggleSelectAll();
    expect(table.selectedIds.value).toEqual([]);
    expect(table.isAllSelected.value).toBe(false);
  });

  describe('loadData', () => {
    it('should load data successfully using response.data', async () => {
      const mockResponse = {
        data: [{ id: '1', name: 'Item 1' }],
        total: 1,
      };
      (apiV1.get as any).mockResolvedValue(mockResponse);

      const table = useAdminTable(options);
      await table.loadData(1);

      expect(table.isLoading.value).toBe(false);
      expect(table.items.value).toEqual(mockResponse.data);
      expect(table.totalItems.value).toBe(1);
      expect(table.page.value).toBe(1);
    });

    it('should load data successfully using response.items', async () => {
      const mockResponse = {
        items: [{ id: '1', name: 'Item 1' }],
      };
      (apiV1.get as any).mockResolvedValue(mockResponse);

      const table = useAdminTable(options);
      await table.loadData(2);

      expect(table.items.value).toEqual(mockResponse.items);
      expect(table.totalItems.value).toBe(1);
      expect(table.page.value).toBe(2);
    });

    it('should handle load data error', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      (apiV1.get as any).mockRejectedValue(new Error('Network Error'));

      const table = useAdminTable(options);
      await table.loadData(1);

      expect(table.isLoading.value).toBe(false);
      expect(consoleSpy).toHaveBeenCalled();
      consoleSpy.mockRestore();
    });

    it('should append extra params to loadData', async () => {
      (apiV1.get as any).mockResolvedValue({ data: [], total: 0 });

      const table = useAdminTable(options);
      await table.loadData(1, { search: 'test', filter: null, undefined_param: undefined });

      expect(apiV1.get).toHaveBeenCalledWith(expect.stringContaining('search=test'));
      expect(apiV1.get).not.toHaveBeenCalledWith(expect.stringContaining('filter='));
    });
  });

  describe('exportData', () => {
    const createDownloadElement = () => ({
      setAttribute: vi.fn(),
      style: { visibility: '' },
      click: vi.fn(),
    });

    it('should handle empty data for export', async () => {
      (apiV1.get as any).mockResolvedValue({ data: [], total: 0 });
      const table = useAdminTable(options);
      
      await table.exportData();
      
      expect(table.isLoading.value).toBe(false);
      expect(toastMock).toHaveBeenCalledWith({
        description: 'No data to export',
        variant: 'default',
      });
    });

    it('should export data successfully with multiple batches and response fallbacks', async () => {
      const blobSpy = vi.spyOn(global, 'Blob').mockImplementation(function() {
        return {} as Blob;
      } as any);
      const mockElement = createDownloadElement();

      global.URL.createObjectURL = vi.fn().mockReturnValue('blob:url');
      global.URL.revokeObjectURL = vi.fn();
      vi.spyOn(document, 'createElement').mockReturnValue(mockElement as any);
      vi.spyOn(document.body, 'appendChild').mockImplementation(() => mockElement as any);
      vi.spyOn(document.body, 'removeChild').mockImplementation(() => mockElement as any);

      (apiV1.get as any)
        .mockResolvedValueOnce({
          items: Array.from({ length: 100 }, (_, i) => ({ id: `id-${i}`, name: `Name ${i}` })),
          total: 230,
        })
        .mockResolvedValueOnce({
          data: Array.from({ length: 100 }, (_, i) => ({
            id: `id-${i + 100}`,
            name: `Name ${i + 100}`,
          })),
        })
        .mockResolvedValueOnce({
          items: Array.from({ length: 30 }, (_, i) => ({
            id: `id-${i + 200}`,
            name: `Name ${i + 200}`,
          })),
        });

      const table = useAdminTable(options);
      await table.exportData({ search: 'test', filter: null, empty: undefined });

      expect(apiV1.get).toHaveBeenCalledTimes(3);
      expect((apiV1.get as any).mock.calls[0][0]).toContain('search=test');
      expect((apiV1.get as any).mock.calls[0][0]).not.toContain('filter=');
      expect((apiV1.get as any).mock.calls[1][0]).toContain('offset=100');
      expect((apiV1.get as any).mock.calls[2][0]).toContain('offset=200');
      expect(mockElement.setAttribute).toHaveBeenCalledWith('href', 'blob:url');
      expect(mockElement.setAttribute).toHaveBeenCalledWith(
        'download',
        expect.stringMatching(/^test_export_\d{4}-\d{2}-\d{2}\.csv$/)
      );
      expect(mockElement.click).toHaveBeenCalledTimes(1);
      expect(global.URL.revokeObjectURL).toHaveBeenCalledWith('blob:url');
      expect(toastMock).toHaveBeenCalledWith({
        description: 'Data exported successfully',
        variant: 'success',
      });

      const csvContent = blobSpy.mock.calls[0][0][1] as string;
      expect(csvContent).toContain('ID,Name');
      expect(csvContent).toContain('id-229,Name 229');

      blobSpy.mockRestore();
    });

    it('should fall back to first batch length when export total is missing', async () => {
      const blobSpy = vi.spyOn(global, 'Blob').mockImplementation(function() {
        return {} as Blob;
      } as any);
      const mockElement = createDownloadElement();

      global.URL.createObjectURL = vi.fn().mockReturnValue('blob:url');
      global.URL.revokeObjectURL = vi.fn();
      vi.spyOn(document, 'createElement').mockReturnValue(mockElement as any);
      vi.spyOn(document.body, 'appendChild').mockImplementation(() => mockElement as any);
      vi.spyOn(document.body, 'removeChild').mockImplementation(() => mockElement as any);

      (apiV1.get as any).mockResolvedValue({
        items: [{ id: '1', name: 'Only item' }],
      });

      const table = useAdminTable(options);
      await table.exportData();

      expect(apiV1.get).toHaveBeenCalledTimes(1);
      expect(mockElement.click).toHaveBeenCalledTimes(1);
      expect(toastMock).toHaveBeenCalledWith({
        description: 'Data exported successfully',
        variant: 'success',
      });

      blobSpy.mockRestore();
    });

    it('should handle export error', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      (apiV1.get as any).mockRejectedValue(new Error('Export Failed'));

      const table = useAdminTable(options);
      await table.exportData();

      expect(table.isLoading.value).toBe(false);
      expect(consoleSpy).toHaveBeenCalled();
      expect(toastMock).toHaveBeenCalledWith({
        title: 'Error',
        description: 'Failed to export data',
        variant: 'destructive',
      });
      consoleSpy.mockRestore();
    });

    it('should correctly escape CSV values', async () => {
      const blobSpy = vi.spyOn(global, 'Blob').mockImplementation(function() {
        return {} as Blob;
      } as any);
      global.URL.createObjectURL = vi.fn().mockReturnValue('blob:url');
      
      const mockElement = createDownloadElement();
      vi.spyOn(document, 'createElement').mockReturnValue(mockElement as any);
      vi.spyOn(document.body, 'appendChild').mockImplementation(() => ({} as any));
      vi.spyOn(document.body, 'removeChild').mockImplementation(() => ({} as any));

      (apiV1.get as any).mockResolvedValue({
        data: [
          { id: '1', name: 'Simple' },
          { id: '2', name: 'With,Comma' },
          { id: '3', name: 'With"Quotes"' },
          { id: '4', name: 'With\nNewline' },
          { id: '5', name: null as any },
        ],
        total: 5
      });

      const table = useAdminTable(options);
      await table.exportData();

      const blobArg = blobSpy.mock.calls[0][0][1]; // The csvContent part
      expect(blobArg).toContain('Simple');
      expect(blobArg).toContain('"With,Comma"');
      expect(blobArg).toContain('"With""Quotes"""');
      expect(blobArg).toContain('"With\nNewline"');
      
      blobSpy.mockRestore();
    });
  });
});
