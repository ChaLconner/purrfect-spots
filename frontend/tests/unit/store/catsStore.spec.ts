import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import {
  useCatsStore,
  extractTags,
  getCleanDescription,
  hasTag,
  catStore,
  catCount,
  setLocations,
  setError,
  setSearchQuery,
  clearSearch,
  type CatLocation,
} from '@/store/catsStore';

describe('Cats Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.useFakeTimers();

    // Mock localStorage
    const storageMock = (() => {
      let store: Record<string, string> = {};
      return {
        getItem: vi.fn((key: string) => store[key] || null),
        setItem: vi.fn((key: string, value: string) => {
          store[key] = value.toString();
        }),
        removeItem: vi.fn((key: string) => {
          delete store[key];
        }),
        clear: vi.fn(() => {
          store = {};
        }),
        key: vi.fn(),
        length: 0,
      };
    })();

    Object.defineProperty(globalThis, 'localStorage', {
      value: storageMock,
      writable: true,
    });

    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  // ========== Initial State Tests ==========
  describe('Initial State', () => {
    it('should initialize with empty locations', () => {
      const store = useCatsStore();
      expect(store.locations).toEqual([]);
      expect(store.catCount).toBe(0);
    });

    it('should initialize with default pagination', () => {
      const store = useCatsStore();
      expect(store.pagination.page).toBe(1);
      expect(store.pagination.limit).toBe(20);
      expect(store.pagination.offset).toBe(0);
      expect(store.pagination.has_more).toBe(false);
    });

    it('should initialize with empty search queries', () => {
      const store = useCatsStore();
      expect(store.searchQuery).toBe('');
      expect(store.gallerySearchQuery).toBe('');
    });

    it('should restore from localStorage on initialization', () => {
      const cachedLocations = [{ id: 'cached-1', location_name: 'Cached' }];
      localStorage.setItem('cats_store_cache', JSON.stringify({ locations: cachedLocations }));
      
      const store = useCatsStore();
      expect(store.locations).toEqual(cachedLocations);
    });

    it('should handle invalid localStorage data gracefully', () => {
      localStorage.setItem('cats_store_cache', 'invalid-json');
      const store = useCatsStore();
      expect(store.locations).toEqual([]);
    });
  });

  // ========== Location Actions ==========
  describe('Location Actions', () => {
    const mockLocations: CatLocation[] = [
      {
        id: '1',
        user_id: 'user1',
        latitude: 13.7563,
        longitude: 100.5018,
        location_name: 'Bangkok Park',
        description: 'A cute cat #cute #friendly',
        image_url: 'https://example.com/cat1.jpg',
        uploaded_at: '2024-01-01T00:00:00Z',
        tags: ['cute', 'friendly'],
      },
      {
        id: '2',
        user_id: 'user2',
        latitude: 13.8,
        longitude: 100.6,
        location_name: 'Cafe Cat',
        description: 'Sleeping cat #sleepy',
        image_url: 'https://example.com/cat2.jpg',
        uploaded_at: '2024-01-02T00:00:00Z',
        tags: ['sleepy'],
      },
    ];

    it('should set locations', () => {
      const store = useCatsStore();
      store.setLocations(mockLocations);
      expect(store.locations).toEqual(mockLocations);
      expect(store.catCount).toBe(2);
    });

    it('should set locations with pagination', () => {
      const store = useCatsStore();
      const paginationData = {
        total: 100,
        limit: 20,
        offset: 0,
        has_more: true,
        page: 1,
        total_pages: 5,
      };

      store.setLocations(mockLocations, paginationData);
      expect(store.pagination).toEqual(paginationData);
      expect(store.totalCount).toBe(100);
      expect(store.hasMore).toBe(true);
      expect(store.totalPages).toBe(5);
    });

    it('should append locations', () => {
      const store = useCatsStore();
      store.setLocations([mockLocations[0]]);
      store.appendLocations([mockLocations[1]]);
      expect(store.locations).toHaveLength(2);
    });
  });

  // ========== Search & Filtering ==========
  describe('Search & Filtering', () => {
    const mockLocations: CatLocation[] = [
      {
        id: '1',
        user_id: 'user1',
        latitude: 13.7563,
        longitude: 100.5018,
        location_name: 'Bangkok Park',
        description: 'Orange tabby cat #cute',
        image_url: 'https://example.com/cat1.jpg',
        uploaded_at: '2024-01-01T00:00:00Z',
        tags: ['cute'],
      },
      {
        id: '2',
        user_id: 'user2',
        latitude: 13.8,
        longitude: 100.6,
        location_name: 'Coffee Shop',
        description: 'Black cat sleeping',
        image_url: 'https://example.com/cat2.jpg',
        uploaded_at: '2024-01-02T00:00:00Z',
        tags: ['black', 'sleepy'],
      },
    ];

    it('should filter by location name', () => {
      const store = useCatsStore();
      store.setLocations(mockLocations);
      store.setSearchQuery('Bangkok');

      expect(store.filteredLocations).toHaveLength(1);
      expect(store.filteredLocations[0].location_name).toBe('Bangkok Park');
    });

    it('should filter by hashtag', () => {
      const store = useCatsStore();
      store.setLocations([
        { id: '1', location_name: 'A', description: '#cute cat', tags: ['cute'] },
        { id: '2', location_name: 'B', description: 'just a cat', tags: [] },
      ] as any);

      store.setSearchQuery('#cute');
      expect(store.filteredLocations).toHaveLength(1);
      expect(store.filteredLocations[0].id).toBe('1');
    });

    it('should filter by description', () => {
      const store = useCatsStore();
      store.setLocations(mockLocations);
      store.setSearchQuery('tabby');

      expect(store.filteredLocations).toHaveLength(1);
      expect(store.filteredLocations[0].id).toBe('1');
    });

    it('should filter by tag', () => {
      const store = useCatsStore();
      store.setLocations(mockLocations);
      store.setSearchQuery('sleepy');

      expect(store.filteredLocations).toHaveLength(1);
      expect(store.filteredLocations[0].id).toBe('2');
    });

    it('should filter by hashtag with # prefix', () => {
      const store = useCatsStore();
      store.setLocations(mockLocations);
      store.setSearchQuery('#cute');

      expect(store.filteredLocations).toHaveLength(1);
      expect(store.filteredLocations[0].id).toBe('1');
    });

    it('should return all when search is empty', () => {
      const store = useCatsStore();
      store.setLocations(mockLocations);
      store.setSearchQuery('');

      expect(store.filteredLocations).toHaveLength(2);
    });

    it('should clear search', () => {
      const store = useCatsStore();
      store.setSearchQuery('test');
      store.clearSearch();
      expect(store.searchQuery).toBe('');
    });
  });

  // ========== Tag Management ==========
  describe('Tag Management', () => {
    it('should get all unique tags', () => {
      const store = useCatsStore();
      store.setLocations([
        {
          id: '1',
          user_id: 'u1',
          latitude: 0,
          longitude: 0,
          location_name: 'Test',
          description: '',
          image_url: '',
          uploaded_at: '',
          tags: ['cute', 'orange'],
        },
        {
          id: '2',
          user_id: 'u2',
          latitude: 0,
          longitude: 0,
          location_name: 'Test2',
          description: '#friendly',
          image_url: '',
          uploaded_at: '',
          tags: ['cute', 'friendly'],
        },
      ]);

      expect(store.allTags).toContain('cute');
      expect(store.allTags).toContain('orange');
      expect(store.allTags).toContain('friendly');
    });

    it('should toggle tag selection', () => {
      const store = useCatsStore();
      store.toggleTag('cute');
      expect(store.selectedTags).toContain('cute');

      store.toggleTag('cute');
      expect(store.selectedTags).not.toContain('cute');
    });

    it('should set popular tags', () => {
      const store = useCatsStore();
      const tags = [
        { tag: 'cute', count: 10 },
        { tag: 'sleepy', count: 5 },
      ];
      store.setPopularTags(tags);
      expect(store.popularTags).toEqual(tags);
    });
  });

  // ========== Pagination ==========
  describe('Pagination', () => {
    it('should go to next page when has more', () => {
      const store = useCatsStore();
      store.setLocations(
        [],
        {
          total: 100,
          limit: 20,
          offset: 0,
          has_more: true,
          page: 1,
          total_pages: 5,
        }
      );

      store.nextPage();
      expect(store.currentPage).toBe(2);
      expect(store.pagination.offset).toBe(20);
    });

    it('should not go to next page when no more', () => {
      const store = useCatsStore();
      store.setLocations(
        [],
        {
          total: 20,
          limit: 20,
          offset: 0,
          has_more: false,
          page: 1,
          total_pages: 1,
        }
      );

      store.nextPage();
      expect(store.currentPage).toBe(1);
    });

    it('should go to previous page', () => {
      const store = useCatsStore();
      store.setLocations(
        [],
        {
          total: 100,
          limit: 20,
          offset: 20,
          has_more: true,
          page: 2,
          total_pages: 5,
        }
      );

      store.prevPage();
      expect(store.currentPage).toBe(1);
      expect(store.pagination.offset).toBe(0);
    });

    it('should not go below page 1', () => {
      const store = useCatsStore();
      store.prevPage();
      expect(store.currentPage).toBe(1);
    });

    it('should go to specific page', () => {
      const store = useCatsStore();
      store.setLocations(
        [],
        {
          total: 100,
          limit: 20,
          offset: 0,
          has_more: true,
          page: 1,
          total_pages: 5,
        }
      );

      store.goToPage(3);
      expect(store.currentPage).toBe(3);
      expect(store.pagination.offset).toBe(40);
    });

    it('should reset pagination', () => {
      const store = useCatsStore();
      store.setLocations(
        [],
        {
          total: 100,
          limit: 20,
          offset: 40,
          has_more: true,
          page: 3,
          total_pages: 5,
        }
      );

      store.resetPagination();
      expect(store.currentPage).toBe(1);
      expect(store.pagination.offset).toBe(0);
    });
  });

  // ========== Loading & Error States ==========
  // ========== Loading & Error States ==========
  describe('Loading & Error States', () => {
    it('should set loading state', () => {
      const store = useCatsStore();
      store.setLoading(true);
      expect(store.isLoading).toBe(true);
      
      store.setLoading(false);
      expect(store.isLoading).toBe(false);
    });

    it('should set error state', () => {
      const store = useCatsStore();
      store.setError('Network error');
      expect(store.error).toBe('Network error');

      store.setError(null);
      expect(store.error).toBeNull();
    });
  });

  // ========== Persistence & Side Effects ==========
  describe('Persistence & Side Effects', () => {
    it('should debounce localStorage writes', async () => {
      const store = useCatsStore();
      
      // Update locations and wait for watch microtask
      store.locations = [{ id: '1' } as any];
      
      // watch callback is scheduled. Advance timers to trigger the debounced function.
      await vi.advanceTimersByTimeAsync(2000);
      
      expect(localStorage.setItem).toHaveBeenCalledWith(
        'cats_store_cache', 
        expect.stringContaining('"id":"1"')
      );
    });

    it('should limit cache size to 100 on write', async () => {
      const store = useCatsStore();
      const largeList = Array.from({ length: 150 }, (_, i) => ({ id: i.toString() } as any));
      
      store.locations = largeList;
      await vi.advanceTimersByTimeAsync(2000);
      
      const setItemCalls = (localStorage.setItem as any).mock.calls;
      expect(setItemCalls.length).toBeGreaterThan(0);
      const saved = JSON.parse(setItemCalls[0][1]);
      expect(saved.locations).toHaveLength(100);
    });

    it('should handle localStorage write errors gracefully', async () => {
      const store = useCatsStore();
      vi.mocked(localStorage.setItem).mockImplementation(() => { 
        throw new Error('Quota exceeded'); 
      });
      
      store.locations = [{ id: 'error' } as any];
      await vi.advanceTimersByTimeAsync(2000);
      // Should not throw
    });
  });

  // ========== Additional Getters ==========
  describe('Additional Getters', () => {
    it('popularTagsComputed should calculate correctly', () => {
      const store = useCatsStore();
      store.setLocations([
        { id: '1', tags: ['cute', 'small'], description: '' } as any,
        { id: '2', tags: ['cute'], description: '' } as any,
        // tags must be undefined/null to trigger extractTags
        { id: '3', description: '#small #cat' } as any,
      ]);

      const popular = store.popularTagsComputed;
      expect(popular).toHaveLength(3);
      expect(popular[0]).toEqual({ tag: 'cute', count: 2 });
      expect(popular.find(p => p.tag === 'small')?.count).toBe(2);
      expect(popular.find(p => p.tag === 'cat')?.count).toBe(1);
    });

    it('allTags should sort alphabetically', () => {
      const store = useCatsStore();
      store.setLocations([
        { id: '1', tags: ['zebra', 'apple'], description: '' } as any,
      ]);
      expect(store.allTags).toEqual(['apple', 'zebra']);
    });
  });

  // ========== Edge Cases ==========
  describe('Edge Cases', () => {
    it('clearGallerySearch should clear gallerySearchQuery', () => {
      const store = useCatsStore();
      store.setGallerySearchQuery('test');
      store.clearGallerySearch();
      expect(store.gallerySearchQuery).toBe('');
    });

    it('nextPage should not exceed total pages if known', () => {
      const store = useCatsStore();
      store.setLocations([], { total: 40, limit: 20, offset: 20, has_more: false, page: 2, total_pages: 2 });
      store.nextPage();
      expect(store.currentPage).toBe(2);
    });

    it('goToPage should validate page range', () => {
      const store = useCatsStore();
      store.setLocations([], { total: 40, limit: 20, offset: 0, has_more: true, page: 1, total_pages: 2 });
      
      store.goToPage(3);
      expect(store.currentPage).toBe(1);
      
      store.goToPage(0);
      expect(store.currentPage).toBe(1);
      
      store.goToPage(2);
      expect(store.currentPage).toBe(2);
    });
  });

  // ========== Legacy Exports ==========
  describe('Legacy Exports', () => {
    it('legacy object and exports should work together', () => {
      // We test them in one block to avoid issues with the module-level singleton _store
      const store = useCatsStore();
      
      // Test catStore object
      catStore.locations = [{ id: 'legacy' } as any];
      expect(store.locations).toHaveLength(1);
      expect(catStore.locations).toEqual(store.locations);
      
      catStore.isLoading = true;
      expect(store.isLoading).toBe(true);
      expect(catStore.isLoading).toBe(true);

      catStore.error = 'Oops';
      expect(store.error).toBe('Oops');
      expect(catStore.error).toBe('Oops');

      // Test action exports
      setLocations([{ id: 'action-1' } as any]);
      expect(store.locations).toHaveLength(1);
      expect(store.locations[0].id).toBe('action-1');
      
      setError('legacy error');
      expect(store.error).toBe('legacy error');
      
      setSearchQuery('legacy search');
      expect(store.searchQuery).toBe('legacy search');

      clearSearch();
      expect(store.searchQuery).toBe('');
      
      // Test computed exports
      expect(catCount.value).toEqual(1);
    });
  });
});

// ========== Utility Function Tests ==========
describe('Utility Functions', () => {
  describe('extractTags', () => {
    it('should extract hashtags from description', () => {
      const tags = extractTags('A cute cat #cute #friendly');
      expect(tags).toContain('cute');
      expect(tags).toContain('friendly');
    });

    it('should handle Thai hashtags', () => {
      const tags = extractTags('แมวน่ารัก #แมว #น่ารัก');
      expect(tags).toContain('แมว');
      expect(tags).toContain('น่ารัก');
    });

    it('should return empty array for null/undefined', () => {
      expect(extractTags(null)).toEqual([]);
      expect(extractTags(undefined)).toEqual([]);
    });

    it('should return unique lowercase tags', () => {
      const tags = extractTags('#Cute #cute #CUTE');
      expect(tags).toEqual(['cute']);
    });
  });

  describe('getCleanDescription', () => {
    it('should remove hashtag section', () => {
      const clean = getCleanDescription('A cute cat in the park\n\n#cute #park #cat');
      expect(clean).toBe('A cute cat in the park');
    });

    it('should handle empty description', () => {
      expect(getCleanDescription(null)).toBe('');
      expect(getCleanDescription('')).toBe('');
    });
  });

  describe('hasTag', () => {
    it('should find tag in location tags', () => {
      const location: CatLocation = {
        id: '1',
        user_id: 'u1',
        latitude: 0,
        longitude: 0,
        location_name: 'Test',
        description: '',
        image_url: '',
        uploaded_at: '',
        tags: ['cute', 'orange'],
      };

      expect(hasTag(location, 'cute')).toBe(true);
      expect(hasTag(location, '#cute')).toBe(true);
      expect(hasTag(location, 'sleepy')).toBe(false);
    });

    it('should extract from description if no tags', () => {
      const location: CatLocation = {
        id: '1',
        user_id: 'u1',
        latitude: 0,
        longitude: 0,
        location_name: 'Test',
        description: '#fluffy cat',
        image_url: '',
        uploaded_at: '',
        tags: [],
      };

      expect(hasTag(location, 'fluffy')).toBe(true);
    });
  });
});
