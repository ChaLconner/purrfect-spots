import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { SubscriptionService } from '../services/subscriptionService';
import { TreatsService } from '../services/treatsService';
import { useAuthStore } from './authStore';
import type { TreatPackage } from '@/types/subscription';

export const useSubscriptionStore = defineStore('subscription', () => {
  const isPro = ref(false);
  const subscriptionEndDate = ref<string | null>(null);
  const cancelAtPeriodEnd = ref(false);
  const treatBalance = ref(0);
  const authStore = useAuthStore();

  // ── Fetch cooldown ──────────────────────────────────────────────
  const lastFetched = ref(0);
  const FETCH_COOLDOWN = 60_000; // 1 minute

  // ── Loading states ──────────────────────────────────────────────
  const isLoadingStatus = ref(false);
  const isLoadingBalance = ref(false);

  // ── Packages cache ──────────────────────────────────────────────
  const treatPackages = ref<Record<string, TreatPackage>>({});
  const packagesLoaded = ref(false);

  const sortedPackages = computed(() =>
    Object.entries(treatPackages.value)
      .map(([key, pkg]) => ({ ...pkg, key }))
      .sort((a, b) => a.amount - b.amount)
  );

  // ── Fetch subscription status ──────────────────────────────────

  async function fetchStatus(force = false): Promise<void> {
    if (!authStore.isAuthenticated) return;

    const now = Date.now();
    if (!force && now - lastFetched.value < FETCH_COOLDOWN && isPro.value !== undefined) {
      return;
    }

    if (isLoadingStatus.value) return; // prevent concurrent fetches
    isLoadingStatus.value = true;

    try {
      const status = await SubscriptionService.getStatus();
      isPro.value = status.is_pro;
      subscriptionEndDate.value = status.subscription_end_date;
      cancelAtPeriodEnd.value = status.cancel_at_period_end || false;

      // Update treat balance if included in response
      if (status.treat_balance !== undefined) {
        treatBalance.value = status.treat_balance;
      }

      lastFetched.value = now;

      // Sync with auth store
      if (authStore.user) {
        authStore.user.is_pro = status.is_pro;
        authStore.user.stripe_customer_id = status.stripe_customer_id;
        if (status.treat_balance !== undefined) {
          authStore.user.treat_balance = status.treat_balance;
        }
      }
    } catch (e) {
      console.error('Failed to fetch subscription status:', e);
    } finally {
      isLoadingStatus.value = false;
    }
  }

  // ── Fetch treat balance ────────────────────────────────────────

  async function fetchTreatBalance(): Promise<void> {
    if (!authStore.isAuthenticated) return;

    if (isLoadingBalance.value) return;
    isLoadingBalance.value = true;

    try {
      const { balance } = await TreatsService.getBalance();
      treatBalance.value = balance;

      if (authStore.user) {
        authStore.user.treat_balance = balance;
      }
    } catch (e) {
      console.error('Failed to fetch treat balance:', e);
    } finally {
      isLoadingBalance.value = false;
    }
  }

  // ── Fetch packages (cached) ────────────────────────────────────

  async function fetchPackages(force = false): Promise<Record<string, TreatPackage>> {
    if (packagesLoaded.value && !force) return treatPackages.value;

    try {
      const pkgs = await TreatsService.getPackages();
      treatPackages.value = pkgs;
      packagesLoaded.value = true;
      return pkgs;
    } catch (e) {
      console.error('Failed to fetch packages:', e);
      return treatPackages.value;
    }
  }

  // ── Refresh all ────────────────────────────────────────────────

  async function refreshAll(): Promise<void> {
    await Promise.all([fetchStatus(true), fetchTreatBalance()]);
  }

  // ── Give treat (optimistic update) ────────────────────────────

  async function giveTreat(photoId: string, amount: number): Promise<unknown> {
    if (!authStore.isAuthenticated) throw new Error('Not authenticated');

    // Optimistic update
    const previousBalance = treatBalance.value;
    const previousUserBalance = authStore.user?.treat_balance;

    if (treatBalance.value >= amount) {
      treatBalance.value -= amount;
      if (authStore.user) {
        authStore.user.treat_balance = treatBalance.value;
      }
    }

    try {
      const res = await TreatsService.giveTreat(photoId, amount);
      if (res.new_balance !== undefined) {
        treatBalance.value = res.new_balance;
        if (authStore.user) {
          authStore.user.treat_balance = res.new_balance;
        }
      }
      return res;
    } catch (e) {
      // Rollback on error
      treatBalance.value = previousBalance;
      if (authStore.user) {
        authStore.user.treat_balance = previousUserBalance;
      }
      throw e;
    }
  }

  return {
    isPro,
    subscriptionEndDate,
    cancelAtPeriodEnd,
    treatBalance,
    isLoadingStatus,
    isLoadingBalance,
    treatPackages,
    packagesLoaded,
    sortedPackages,
    fetchStatus,
    fetchTreatBalance,
    fetchPackages,
    refreshAll,
    giveTreat,
  };
});
