<template>
  <div
    class="subscription-view min-h-screen pt-24 pb-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden"
  >
    <GhibliBackground />

    <div class="max-w-6xl mx-auto relative z-10">
      <!-- Webhook Confirmation Banner (shown while polling after Stripe redirect) -->
      <Transition name="fade">
        <div
          v-if="isPolling"
          class="mb-8 flex items-center justify-center gap-3 bg-amber-50 border border-amber-200 text-amber-700 rounded-2xl py-3 px-5 text-sm font-medium shadow-sm"
        >
          <!-- Spinner -->
          <svg class="animate-spin h-4 w-4 text-amber-500" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
          {{ $t('subscription.toast.confirmingPayment') }}
        </div>
      </Transition>

      <!-- Header Section -->
      <div class="text-center mb-16">
        <h1 class="text-5xl font-heading font-extrabold text-brown mb-4 tracking-tight">
          {{ $t('subscription.title') }}
        </h1>
        <p class="text-xl text-brown-light max-w-2xl mx-auto font-body">
          {{ $t('subscription.subtitle') }}
        </p>
      </div>

      <!-- Main Subscription Plan -->
      <div class="mb-20">
        <h2
          class="text-3xl font-heading font-bold text-brown mb-6 text-center flex items-center justify-center gap-3"
        >
          <span class="h-1 w-12 bg-terracotta/30 rounded-full"></span>
          {{ $t('subscription.title') }}
          <span class="h-1 w-12 bg-terracotta/30 rounded-full"></span>
        </h2>

        <!-- Billing Toggle -->
        <div class="flex justify-center items-center gap-4 mb-8">
          <span 
            class="font-medium cursor-pointer transition-colors"
            :class="selectedPlan === 'monthly' ? 'text-terracotta' : 'text-stone-400'"
            @click="selectedPlan = 'monthly'"
          >
            {{ $t('subscription.proPlan.billedMonthly') }}
          </span>
          <button 
            class="relative inline-flex h-7 w-14 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-terracotta focus:ring-offset-2"
            :class="selectedPlan === 'annual' ? 'bg-terracotta' : 'bg-stone-300'"
            @click="selectedPlan = selectedPlan === 'monthly' ? 'annual' : 'monthly'"
          >
            <span
              class="inline-block h-5 w-5 transform rounded-full bg-white transition-transform"
              :class="selectedPlan === 'annual' ? 'translate-x-8' : 'translate-x-1'"
            ></span>
          </button>
          <div 
            class="flex items-center gap-2 cursor-pointer"
            @click="selectedPlan = 'annual'"
          >
            <span 
              class="font-medium transition-colors"
              :class="selectedPlan === 'annual' ? 'text-terracotta' : 'text-stone-400'"
            >
              {{ $t('subscription.proPlan.billedAnnually') }}
            </span>
            <span class="bg-green-100 text-green-700 text-[10px] uppercase tracking-wider font-bold px-2 py-0.5 rounded-full">
              {{ $t('subscription.proPlan.savePercent') }}
            </span>
          </div>
        </div>

        <div class="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          <!-- Free Plan -->
          <PlanCard
            :title="$t('subscription.freePlan.title')"
            :subtitle="$t('subscription.freePlan.subtitle')"
            :price="formatCurrency(0)"
            :period="$t('subscription.freePlan.period')"
            :features="freeFeatures"
          >
            <template #actions>
              <div class="text-center pt-6 border-t border-stone-100">
                <span class="text-stone-400 text-sm font-medium">{{
                  $t('subscription.freePlan.action')
                }}</span>
              </div>
            </template>
          </PlanCard>

          <!-- Pro Plan -->
          <PlanCard
            :title="$t('subscription.proPlan.title')"
            :subtitle="$t('subscription.proPlan.subtitle')"
            :price="selectedPlan === 'annual' ? formatCurrency(1750) : formatCurrency(175)"
            :period="selectedPlan === 'annual' ? $t('subscription.proPlan.periodAnnual') : $t('subscription.proPlan.period')"
            :features="proFeatures"
            is-premium
            :badge="$t('subscription.proPlan.badge')"
          >
            <template #actions>
              <div v-if="subscriptionStore.isPro">
                <div
                  class="flex items-center justify-center gap-2 text-green-600 font-bold mb-4 bg-green-50 py-2 rounded-xl"
                >
                  <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fill-rule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clip-rule="evenodd"
                    />
                  </svg>
                  {{ $t('subscription.proPlan.active') }}
                </div>
                <div
                  v-if="
                    subscriptionStore.cancelAtPeriodEnd && subscriptionStore.subscriptionEndDate
                  "
                  class="text-center mb-4 text-amber-600 font-medium text-sm"
                >
                  {{ $t('subscription.proPlan.cancelsOn') }}
                  {{ new Date(subscriptionStore.subscriptionEndDate).toLocaleDateString() }}
                </div>
                <button
                  class="w-full bg-stone-100 text-stone-500 py-3 rounded-2xl hover:bg-stone-200 transition-colors font-bold text-sm"
                  :disabled="isLoading"
                  @click="handleManageSubscription"
                >
                  {{ $t('subscription.proPlan.manage') }}
                </button>
                <button
                  v-if="!subscriptionStore.cancelAtPeriodEnd"
                  class="w-full mt-2 bg-transparent text-red-500/70 hover:text-red-600 hover:bg-red-50 py-2 rounded-2xl transition-colors font-bold text-xs"
                  :disabled="isLoading || isCanceling"
                  @click="showCancelModal = true"
                >
                  {{ $t('common.cancel') }} {{ $t('nav.subscription') }}
                </button>
              </div>
              <button
                v-else
                class="w-full bg-terracotta text-white font-bold py-4 rounded-2xl shadow-xl shadow-terracotta/20 hover:bg-terracotta-dark transition-all transform hover:-translate-y-1 block text-center text-lg disabled:opacity-50 disabled:cursor-not-allowed"
                :disabled="isLoading"
                @click="handleSubscribe"
              >
                {{
                  isLoading
                    ? $t('subscription.proPlan.processing')
                    : $t('subscription.proPlan.upgrade')
                }}
              </button>
            </template>
          </PlanCard>
        </div>
      </div>

      <!-- Treat Packages Section -->
      <div>
        <h2 class="text-3xl font-heading font-bold text-brown mb-4 text-center">
          {{ $t('subscription.treats.title') }}
        </h2>
        <p class="text-center text-brown-light mb-12 max-w-xl mx-auto font-body">
          {{ $t('subscription.treats.subtitle') }}
        </p>

        <div
          class="flex overflow-x-auto snap-x snap-mandatory sm:grid sm:grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-6 pt-8 pb-12 sm:pb-0 -mx-4 px-4 sm:mx-0 sm:px-0 sm:overflow-visible hide-scrollbar"
        >
          <div
            v-for="pkg in sortedPackages"
            :key="pkg.key"
            class="min-w-[80vw] sm:min-w-0 snap-center bg-glass p-6 rounded-3xl border border-white/60 shadow-md hover:shadow-lg transition-all text-center flex flex-col group relative"
            :class="{ 'border-2 border-sage shadow-xl scale-105': pkg.key === 'medium' }"
          >
            <div
              v-if="pkg.bonus > 0"
              class="absolute -top-3 left-1/2 -translate-x-1/2 text-white text-[10px] font-bold px-3 py-1 rounded-full uppercase tracking-wider shadow-sm"
              :class="
                pkg.key === 'medium'
                  ? 'bg-sage'
                  : pkg.key === 'legendary'
                    ? 'bg-orange-500'
                    : 'bg-terracotta'
              "
            >
              {{
                pkg.key === 'medium'
                  ? $t('subscription.treats.bestValue')
                  : pkg.bonus + ' ' + $t('subscription.treats.free')
              }}
            </div>

            <div
              class="h-20 mb-4 flex items-center justify-center transition-transform group-hover:scale-110 overflow-hidden"
            >
              <img
                src="/give-treat.png"
                alt="Treat"
                loading="lazy"
                class="h-full object-contain scale-[1.05] [image-rendering:high-quality] [clip-path:inset(2px)] will-change-transform"
              />
            </div>
            <h4 class="text-lg font-bold text-brown mb-1">{{ pkg.name }}</h4>
            <p class="text-3xl font-extrabold text-brown mb-1">
              {{ pkg.amount }}
              <span class="text-sm font-normal text-stone-400">{{
                $t('subscription.treats.unit')
              }}</span>
            </p>
            <p
              v-if="pkg.bonus > 0"
              class="font-bold text-xs mb-4"
              :class="
                pkg.key === 'medium'
                  ? 'text-sage-dark'
                  : pkg.key === 'legendary'
                    ? 'text-orange-500'
                    : 'text-terracotta'
              "
            >
              {{ pkg.amount - pkg.bonus }} + {{ pkg.bonus }} {{ $t('subscription.treats.free') }}
            </p>
            <p v-else class="text-transparent font-bold text-xs mb-4 select-none">
              {{ $t('subscription.treats.noBonus') }}
            </p>

            <div class="mt-auto">
              <button
                class="w-full py-2.5 rounded-xl font-bold transition-all text-sm mb-2"
                :class="
                  pkg.key === 'medium'
                    ? 'bg-sage hover:bg-sage-dark text-white shadow-lg shadow-sage/20 py-3'
                    : 'bg-white text-brown border-2 border-stone-100 hover:border-terracotta hover:text-terracotta'
                "
                @click="buyTreats(pkg.key!)"
              >
                {{ formatCurrency(pkg.price) }}
              </button>
              <p
                class="text-[10px] text-stone-400 uppercase tracking-tighter"
                :class="{ 'line-through mb-0.5': pkg.bonus > 0 }"
              >
                {{ pkg.bonus > 0 ? $t('subscription.treats.value') : '' }}
              </p>
              <p
                class="text-[10px] uppercase tracking-tighter"
                :class="pkg.key === 'medium' ? 'text-sage-dark font-bold' : 'text-stone-400'"
              >
                {{ formatCurrency(pkg.price_per_treat) }} {{ $t('subscription.treats.perTreat') }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Confirm Cancel Modal -->
    <BaseConfirmModal
      :is-open="showCancelModal"
      title="Cancel Subscription"
      message="Are you sure you want to cancel your PRO subscription? You will keep your premium benefits until the end of this billing period."
      :confirm-text="$t('common.cancel') + ' PRO'"
      :cancel-text="$t('common.cancel')"
      :is-loading="isCanceling"
      variant="danger"
      @close="showCancelModal = false"
      @confirm="confirmCancel"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { storeToRefs } from 'pinia';
import { useRoute, useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useSubscriptionStore } from '../store/subscriptionStore';
import { SubscriptionService } from '../services/subscriptionService';
import { TreatsService } from '../services/treatsService';
import { useToastStore } from '../store/toastStore';
import GhibliBackground from '@/components/ui/GhibliBackground.vue';
import { useSeo } from '@/composables/useSeo';
import PlanCard from '@/components/subscription/PlanCard.vue';
import { BaseConfirmModal } from '@/components/ui';
import { config } from '@/config';

const { t, locale } = useI18n();
const subscriptionStore = useSubscriptionStore();
const toastStore = useToastStore();
const route = useRoute();
const router = useRouter();
const isLoading = ref(false);
const selectedPlan = ref<'monthly' | 'annual'>('annual');
const purchasingPackage = ref<string | null>(null);
const isPolling = ref(false);
const showCancelModal = ref(false);
const isCanceling = ref(false);
const { setMetaTags } = useSeo();
const { sortedPackages } = storeToRefs(subscriptionStore);

const freeFeatures = computed(() => [
  t('subscription.freePlan.features.0'),
  t('subscription.freePlan.features.1'),
  t('subscription.freePlan.features.2'),
  t('subscription.freePlan.features.3'),
]);

const proFeatures = computed(() => [
  t('subscription.proPlan.features.0'),
  t('subscription.proPlan.features.1'),
  t('subscription.proPlan.features.2'),
  t('subscription.proPlan.features.3'),
  t('subscription.proPlan.features.4'),
]);

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat(locale.value === 'th' ? 'th-TH' : 'en-US', {
    style: 'currency',
    currency: config.app.currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(amount);
}

onMounted(async () => {
  setMetaTags({
    title: t('subscription.meta.title') + ' | Purrfect Spots',
    description: t('subscription.meta.description'),
  });

  // Handle Return from Stripe (Success)
  if (route.path.includes('/success') || route.query.purchase === 'success') {
    toastStore.addToast({
      title: t('subscription.toast.successTitle'),
      message: t('subscription.toast.successMessage'),
      type: 'success',
    });

    // Clean URL first so a hard-refresh doesn’t re-trigger polling
    router.replace('/subscription');

    // Stripe webhooks can take 1–5 s to reach our server.
    // Poll fetchStatus until Pro status or treat balance changes, then stop.
    await pollForStatusChange();
  }

  // Handle Return from Stripe (Cancel)
  if (route.path.includes('/cancel') || route.query.purchase === 'cancel') {
    router.replace('/subscription');
  }

  // Parallel fetch: status + packages
  await Promise.all([subscriptionStore.fetchStatus(), subscriptionStore.fetchPackages()]);
});

/**
 * Poll the backend for subscription status changes after returning from Stripe.
 *
 * Stripe webhooks can take anywhere from 1 s to ~15 s to arrive and be
 * processed.  We snapshot the current Pro status + treat balance before the
 * poll and stop as soon as either one changes, or after MAX_ATTEMPTS tries.
 */
async function pollForStatusChange(): Promise<void> {
  const MAX_ATTEMPTS = 8;
  const INTERVAL_MS = 2000; // 2 s between polls

  const initialIsPro = subscriptionStore.isPro;
  const initialBalance = subscriptionStore.treatBalance;

  isPolling.value = true;

  for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
    await new Promise((resolve) => setTimeout(resolve, INTERVAL_MS));

    try {
      await subscriptionStore.fetchStatus(true);

      const statusChanged = subscriptionStore.isPro !== initialIsPro;
      const balanceChanged = subscriptionStore.treatBalance !== initialBalance;

      if (statusChanged || balanceChanged) {
        // Webhook processed — stop polling
        break;
      }
    } catch {
      // Non-fatal — keep retrying
    }
  }

  isPolling.value = false;
}

async function handleSubscribe(): Promise<void> {
  if (isLoading.value) return;
  isLoading.value = true;
  try {
    const { checkout_url } = await SubscriptionService.createCheckout(selectedPlan.value);
    window.location.href = checkout_url;
  } catch (e: unknown) {
    console.error(e);
    toastStore.addToast({
      title: t('subscription.toast.errorTitle'),
      message: (e as Error).message || t('subscription.toast.checkoutFailed'),
      type: 'error',
    });
  } finally {
    isLoading.value = false;
  }
}

async function handleManageSubscription(): Promise<void> {
  if (isLoading.value) return;
  isLoading.value = true;
  try {
    const { url } = await SubscriptionService.createPortalSession('/subscription');
    window.location.href = url;
  } catch (e) {
    console.error(e);
    toastStore.addToast({
      title: t('subscription.toast.errorTitle'),
      message: t('subscription.toast.portalFailed'),
      type: 'error',
    });
  } finally {
    isLoading.value = false;
  }
}

async function confirmCancel(): Promise<void> {
  if (isCanceling.value) return;
  isCanceling.value = true;
  try {
    await SubscriptionService.cancel();
    await subscriptionStore.refreshAll();
    toastStore.addToast({
      title: t('toast.success'),
      message: 'Subscription successfully canceled.',
      type: 'success',
    });
  } catch (e) {
    console.error(e);
    toastStore.addToast({
      title: t('toast.error'),
      message: 'Failed to cancel subscription.',
      type: 'error',
    });
  } finally {
    isCanceling.value = false;
    showCancelModal.value = false;
  }
}

async function buyTreats(packageType: string): Promise<void> {
  if (purchasingPackage.value) return; // prevent double-click
  purchasingPackage.value = packageType;
  try {
    const { checkout_url } = await TreatsService.purchaseCheckout(packageType);
    window.location.href = checkout_url;
  } catch (e) {
    console.error(e);
    toastStore.addToast({
      title: t('subscription.toast.errorTitle'),
      message: t('subscription.toast.purchaseFailed'),
      type: 'error',
    });
  } finally {
    purchasingPackage.value = null;
  }
}
</script>

<style scoped>
/* Smooth fade for the webhook-confirmation banner */
.fade-enter-active,
.fade-leave-active {
  transition:
    opacity 0.3s ease,
    transform 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
