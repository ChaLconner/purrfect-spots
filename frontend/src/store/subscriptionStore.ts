import { defineStore } from 'pinia';
import { ref } from 'vue';
import { SubscriptionService } from '../services/subscriptionService';
import { TreatsService } from '../services/treatsService';
import { useAuthStore } from './authStore';

export const useSubscriptionStore = defineStore('subscription', () => {
  const isPro = ref(false);
  const subscriptionEndDate = ref<string | null>(null);
  const treatBalance = ref(0);
  const authStore = useAuthStore();

  async function fetchStatus() {
    if (!authStore.isAuthenticated) return;
    try {
      const status = await SubscriptionService.getStatus();
      isPro.value = status.is_pro;
      subscriptionEndDate.value = status.subscription_end_date;
      
      // Update auth store user object too if needed
      if (authStore.user) {
        authStore.user.is_pro = status.is_pro;
      }
    } catch (e) {
      console.error('Failed to fetch subscription status:', e);
    }
  }

  async function fetchTreatBalance() {
    if (!authStore.isAuthenticated) return;
    try {
      const { balance } = await TreatsService.getBalance();
      treatBalance.value = balance;
      
      if (authStore.user) {
        authStore.user.treat_balance = balance;
      }
    } catch (e) {
      console.error('Failed to fetch treat balance:', e);
    }
  }
  
  async function refreshAll() {
    await Promise.all([fetchStatus(), fetchTreatBalance()]);
  }

  async function giveTreat(photoId: string, amount: number) {
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
      // Rollback
      treatBalance.value = previousBalance;
      if (authStore.user) {
        authStore.user.treat_balance = previousUserBalance;
      }
      throw e;
    }
  }

  return { isPro, subscriptionEndDate, treatBalance, fetchStatus, fetchTreatBalance, refreshAll, giveTreat };
});
