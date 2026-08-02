import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { shallowMount } from '@vue/test-utils';
import SubscriptionView from '@/views/SubscriptionView.vue';

vi.mock('/give-treat.webp', () => ({
  default: '/give-treat.webp',
}));

const mockReplace = vi.fn().mockResolvedValue(undefined);
const mockPush = vi.fn();
const mockRoute = {
  path: '/subscription',
  query: {} as Record<string, string>,
};

const mockFetchStatus = vi.fn().mockResolvedValue(undefined);
const mockFetchPackages = vi.fn().mockResolvedValue(undefined);
const mockRefreshAll = vi.fn().mockResolvedValue(undefined);
const mockAddToast = vi.fn();
const mockSubscriptionStore = {
  isPro: false,
  treatBalance: 0,
  cancelAtPeriodEnd: false,
  subscriptionEndDate: null as string | null,
  sortedPackages: [] as unknown[],
  fetchStatus: mockFetchStatus,
  fetchPackages: mockFetchPackages,
  refreshAll: mockRefreshAll,
};

vi.mock('vue-router', () => ({
  useRoute: () => mockRoute,
  useRouter: () => ({
    replace: mockReplace,
    push: mockPush,
  }),
}));

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => key,
    locale: { value: 'en' },
  }),
}));

import type * as PiniaModule from 'pinia';

vi.mock('pinia', async (importOriginal) => {
  const actual = await importOriginal<typeof PiniaModule>();
  return {
    ...actual,
    storeToRefs: (store: { sortedPackages: unknown }) => ({
      sortedPackages: { value: store.sortedPackages },
    }),
  };
});

vi.mock('@/stores/subscriptionStore', () => ({
  useSubscriptionStore: () => mockSubscriptionStore,
}));

vi.mock('@/stores/toastStore', () => ({
  useToastStore: () => ({
    addToast: mockAddToast,
  }),
}));

vi.mock('@/services/subscriptionService', () => ({
  SubscriptionService: {
    createCheckout: vi.fn(),
    getPlans: vi.fn().mockRejectedValue(new Error('plans unavailable')),
    cancel: vi.fn(),
    createPortalSession: vi.fn(),
  },
}));

vi.mock('@/services/treatsService', () => ({
  TreatsService: {
    purchaseCheckout: vi.fn(),
  },
}));

vi.mock('@/composables/useSeo', () => ({
  useSeo: () => ({
    setMetaTags: vi.fn(),
  }),
}));

vi.mock('@/config', () => ({
  config: {
    app: {
      currency: 'USD',
    },
  },
}));

vi.mock('@/components/ui/GhibliBackground.vue', () => ({
  default: { template: '<div />' },
}));
vi.mock('@/components/subscription/PlanCard.vue', () => ({
  default: { template: '<div><slot name="actions" /></div>' },
}));
vi.mock('@/components/ui', () => ({
  BaseConfirmModal: { template: '<div />' },
}));

describe('SubscriptionView.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    mockRoute.path = '/subscription';
    mockRoute.query = {};
    mockSubscriptionStore.isPro = false;
    mockSubscriptionStore.treatBalance = 0;
    mockSubscriptionStore.cancelAtPeriodEnd = false;
    mockSubscriptionStore.subscriptionEndDate = null;
    mockSubscriptionStore.sortedPackages = [];
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('loads status and packages once on the default route', async () => {
    shallowMount(SubscriptionView);
    await Promise.resolve();
    await Promise.resolve();

    expect(mockFetchStatus).toHaveBeenCalledTimes(1);
    expect(mockFetchPackages).toHaveBeenCalledTimes(1);
    expect(mockReplace).not.toHaveBeenCalled();
  });

  it('normalizes the success route, polls until Pro entitlement, and avoids default-state false positives', async () => {
    mockRoute.path = '/subscription/success';
    mockFetchStatus.mockImplementationOnce(async () => {
      mockSubscriptionStore.isPro = true;
    });

    shallowMount(SubscriptionView);
    await Promise.resolve();
    await Promise.resolve();

    expect(mockReplace).toHaveBeenCalledWith('/subscription');
    expect(mockAddToast).toHaveBeenCalledWith(
      expect.objectContaining({ type: 'success' })
    );

    await vi.advanceTimersByTimeAsync(2000);
    await Promise.resolve();
    await Promise.resolve();

    expect(mockFetchStatus).toHaveBeenCalledTimes(2);
    expect(mockFetchPackages).toHaveBeenCalledTimes(1);
  });

  it('normalizes the cancel route and refreshes current subscription data once', async () => {
    mockRoute.query = { purchase: 'cancel' };

    shallowMount(SubscriptionView);
    await Promise.resolve();
    await Promise.resolve();

    expect(mockReplace).toHaveBeenCalledWith('/subscription');
    expect(mockFetchStatus).toHaveBeenCalledTimes(1);
    expect(mockFetchPackages).toHaveBeenCalledTimes(1);
  });
});
