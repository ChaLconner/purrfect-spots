<template>
  <div
    class="subscription-view min-h-screen pt-24 pb-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden"
  >
    <GhibliBackground />

    <div class="max-w-6xl mx-auto relative z-10">
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
          class="text-3xl font-heading font-bold text-brown mb-8 text-center flex items-center justify-center gap-3"
        >
          <span class="h-1 w-12 bg-terracotta/30 rounded-full"></span>
          {{ $t('subscription.monthlyMembership') }}
          <span class="h-1 w-12 bg-terracotta/30 rounded-full"></span>
        </h2>

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
            :price="formatCurrency(175)"
            :period="$t('subscription.proPlan.period')"
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
                  @click="handleManageSubscription"
                  :disabled="isLoading"
                >
                  {{ $t('subscription.proPlan.manage') }}
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
              class="h-16 mb-4 flex items-center justify-center transition-transform group-hover:scale-110"
            >
              <img src="/give-treat.png" alt="Treat" loading="lazy" class="h-full object-contain" />
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
import { config } from '@/config';

const { t, locale } = useI18n();
const subscriptionStore = useSubscriptionStore();
const toastStore = useToastStore();
const route = useRoute();
const router = useRouter();
const isLoading = ref(false);
const purchasingPackage = ref<string | null>(null);
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

function formatCurrency(amount: number) {
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
    // Force refresh to get updated balance after purchase
    subscriptionStore.refreshAll();

    // Clean URL
    router.replace('/subscription');
  }

  // Handle Return from Stripe (Cancel)
  if (route.path.includes('/cancel') || route.query.purchase === 'cancel') {
    // Clean URL
    router.replace('/subscription');
  }

  // Parallel fetch: status + packages
  await Promise.all([subscriptionStore.fetchStatus(), subscriptionStore.fetchPackages()]);
});

async function handleSubscribe(): Promise<void> {
  if (isLoading.value) return;
  isLoading.value = true;
  try {
    const priceId = config.stripe.proPriceId;
    if (!priceId) throw new Error('Price ID not configured');

    const { checkout_url } = await SubscriptionService.createCheckout(priceId);
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
    // Use clean URL for return to avoid stale query params
    const returnUrl = `${window.location.origin}/subscription`;
    const { url } = await SubscriptionService.createPortalSession(returnUrl);
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
.font-heading {
  font-family: 'Outfit', sans-serif;
}
.font-body {
  font-family: 'Inter', sans-serif;
}
/* Reused simplified utilities */
.text-terracotta {
  color: #c97b49;
}
.bg-terracotta {
  background-color: #c97b49;
}
.bg-terracotta-dark {
  background-color: #a66136;
}
.text-sage-dark {
  color: #5c755e;
}
.bg-sage {
  background-color: #8da18e;
}
.bg-sage-dark {
  background-color: #5c755e;
}
.border-sage {
  border-color: #8da18e;
}
.bg-glass {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(10px);
}
</style>

<style>
/* Global utility for hiding scrollbar but allowing scroll */
.hide-scrollbar {
  -ms-overflow-style: none; /* IE and Edge */
  scrollbar-width: none; /* Firefox */
}
.hide-scrollbar::-webkit-scrollbar {
  display: none;
  width: 0;
  height: 0;
}
</style>
