<template>
  <div
    class="subscription-view min-h-screen pt-24 pb-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden"
  >
    <GhibliBackground />

    <div class="max-w-6xl mx-auto relative z-10">
      <!-- Header Section -->
      <div class="text-center mb-16">
        <h1 class="text-5xl font-heading font-extrabold text-brown mb-4 tracking-tight">
          Support the <span class="text-terracotta">Purrfect</span> Community
        </h1>
        <p class="text-xl text-brown-light max-w-2xl mx-auto font-body">
          Choose a way to support our furry friends and unlock exclusive features.
        </p>
      </div>

      <!-- Main Subscription Plan -->
      <div class="mb-20">
        <h2
          class="text-3xl font-heading font-bold text-brown mb-8 text-center flex items-center justify-center gap-3"
        >
          <span class="h-1 w-12 bg-terracotta/30 rounded-full"></span>
          Monthly Membership
          <span class="h-1 w-12 bg-terracotta/30 rounded-full"></span>
        </h2>

        <div class="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          <!-- Free Plan -->
          <div class="bg-glass rounded-3xl shadow-lg p-8 border border-white/40 flex flex-col">
            <h3 class="text-2xl font-semibold mb-2 text-brown">Free Spotter</h3>
            <p class="text-stone-500 mb-6 text-sm">Everything you need to start spotting cats.</p>
            <ul class="space-y-4 mb-8 text-brown-light flex-grow">
              <li class="flex items-start">
                <svg
                  class="h-5 w-5 text-sage-dark mr-3 mt-0.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M5 13l4 4L19 7"
                  />
                </svg>
                Upload cat photos
              </li>
              <li class="flex items-start">
                <svg
                  class="h-5 w-5 text-sage-dark mr-3 mt-0.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M5 13l4 4L19 7"
                  />
                </svg>
                View map locations
              </li>
              <li class="flex items-start">
                <svg
                  class="h-5 w-5 text-sage-dark mr-3 mt-0.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M5 13l4 4L19 7"
                  />
                </svg>
                Basic markers
              </li>
            </ul>
            <div class="text-center pt-6 border-t border-stone-100">
              <span class="block text-4xl font-extrabold text-brown mb-1">฿0</span>
              <span class="text-stone-400 text-sm font-medium">Forever Free</span>
            </div>
          </div>

          <!-- Pro Plan -->
          <div
            class="bg-white rounded-3xl shadow-2xl p-8 border-2 border-terracotta relative transform hover:scale-[1.02] transition-all duration-300 flex flex-col"
          >
            <div
              class="absolute -top-4 right-8 bg-terracotta text-white text-xs font-bold px-4 py-1.5 rounded-full shadow-lg tracking-widest uppercase"
            >
              Most Popular
            </div>
            <h3 class="text-2xl font-bold mb-2 text-terracotta">Purrfect Plus</h3>
            <p class="text-stone-500 mb-6 text-sm">Professional tools for cat enthusiasts.</p>
            <ul class="space-y-4 mb-8 text-brown flex-grow">
              <li class="flex items-start">
                <svg
                  class="h-5 w-5 text-terracotta mr-3 mt-0.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M5 13l4 4L19 7"
                  />
                </svg>
                Advanced Coat Color Filters
              </li>
              <li class="flex items-start">
                <svg
                  class="h-5 w-5 text-terracotta mr-3 mt-0.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M5 13l4 4L19 7"
                  />
                </svg>
                "Golden Spots" Access (Verified)
              </li>
              <li class="flex items-start">
                <svg
                  class="h-5 w-5 text-terracotta mr-3 mt-0.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M5 13l4 4L19 7"
                  />
                </svg>
                Ad-Free & Pro Badge
              </li>
              <li class="flex items-start">
                <svg
                  class="h-5 w-5 text-terracotta mr-3 mt-0.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M5 13l4 4L19 7"
                  />
                </svg>
                Priority Support
              </li>
            </ul>

            <div class="text-center pt-6 border-t border-stone-100 mb-8">
              <span class="block text-4xl font-extrabold text-brown mb-1">฿175</span>
              <span class="text-stone-400 text-sm font-medium">per month ($4.99)</span>
            </div>

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
                ACTIVE PLAN
              </div>
              <div
                v-if="subscriptionStore.cancelAtPeriodEnd && subscriptionStore.subscriptionEndDate"
                class="text-center mb-4 text-amber-600 font-medium text-sm"
              >
                Cancels on
                {{ new Date(subscriptionStore.subscriptionEndDate).toLocaleDateString() }}
              </div>
              <button
                class="w-full bg-stone-100 text-stone-500 py-3 rounded-2xl hover:bg-stone-200 transition-colors font-bold text-sm"
                @click="handleManageSubscription"
              >
                Manage Subscription
              </button>
            </div>
            <button
              v-else
              class="w-full bg-terracotta text-white font-bold py-4 rounded-2xl shadow-xl shadow-terracotta/20 hover:bg-terracotta-dark transition-all transform hover:-translate-y-1 block text-center text-lg"
              :disabled="isLoading"
              @click="handleSubscribe"
            >
              {{ isLoading ? 'Processing...' : 'Upgrade Now' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Treat Packages Section -->
      <div>
        <h2 class="text-3xl font-heading font-bold text-brown mb-4 text-center">Buy Treats</h2>
        <p class="text-center text-brown-light mb-12 max-w-xl mx-auto font-body">
          Show some love to your favorite cats! Treats let you tip creators and earn a spot on the
          leaderboard.
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
              {{ pkg.key === 'medium' ? 'Best Value' : pkg.bonus + ' FREE!' }}
            </div>

            <div
              class="h-16 mb-4 flex items-center justify-center transition-transform group-hover:scale-110"
            >
              <img src="/give-treat.png" alt="Treat" loading="lazy" class="h-full object-contain" />
            </div>
            <h4 class="text-lg font-bold text-brown mb-1">{{ pkg.name }}</h4>
            <p class="text-3xl font-extrabold text-brown mb-1">
              {{ pkg.amount }} <span class="text-sm font-normal text-stone-400">Treats</span>
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
              {{ pkg.amount - pkg.bonus }} + {{ pkg.bonus }} FREE!
            </p>
            <p v-else class="text-transparent font-bold text-xs mb-4 select-none">No Bonus</p>

            <div class="mt-auto">
              <button
                class="w-full py-2.5 rounded-xl font-bold transition-all text-sm mb-2"
                :class="
                  pkg.key === 'medium'
                    ? 'bg-sage hover:bg-sage-dark text-white shadow-lg shadow-sage/20 py-3'
                    : 'bg-white text-brown border-2 border-stone-100 hover:border-terracotta hover:text-terracotta'
                "
                @click="buyTreats(pkg.key)"
              >
                ฿{{ pkg.price }}
              </button>
              <p
                class="text-[10px] text-stone-400 uppercase tracking-tighter"
                :class="{ 'line-through mb-0.5': pkg.bonus > 0 }"
              >
                <!-- Value calculation logic or just hide value if simpler -->
                {{ pkg.bonus > 0 ? 'VALUE' : '' }}
              </p>
              <p
                class="text-[10px] uppercase tracking-tighter"
                :class="pkg.key === 'medium' ? 'text-sage-dark font-bold' : 'text-stone-400'"
              >
                ฿{{ pkg.price_per_treat }} per treat
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useSubscriptionStore } from '../store/subscriptionStore';
import { SubscriptionService } from '../services/subscriptionService';
import { TreatsService } from '../services/treatsService';
import { useToastStore } from '../store/toastStore';
import GhibliBackground from '@/components/ui/GhibliBackground.vue';
import { useSeo } from '@/composables/useSeo';

const subscriptionStore = useSubscriptionStore();
const toastStore = useToastStore();
const route = useRoute();
const router = useRouter();
const isLoading = ref(false);
const purchasingPackage = ref<string | null>(null);
const { setMetaTags } = useSeo();

// Use store's cached sortedPackages directly
const sortedPackages = subscriptionStore.sortedPackages;

onMounted(async () => {
  setMetaTags({
    title: 'Subscription & Treats | Purrfect Spots',
    description: 'Upgrade your account and support the community with treats.',
  });

  // Handle Return from Stripe (Success)
  if (route.path.includes('/success') || route.query.purchase === 'success') {
    toastStore.addToast({
      title: 'Purchase Successful',
      message: 'Thank you for your support! Your balance has been updated.',
      type: 'success',
    });
    // Force refresh to get updated balance after purchase
    subscriptionStore.refreshAll();

    // Clean URL
    router.replace('/subscription');
  }

  // Handle Return from Stripe (Cancel)
  if (route.path.includes('/cancel') || route.query.purchase === 'cancel') {
    toastStore.addToast({
      title: 'Action Cancelled',
      message: 'No charges were made.',
      type: 'info',
    });

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
    const priceId = import.meta.env.VITE_STRIPE_PRO_PRICE_ID;
    if (!priceId) throw new Error('Price ID not configured');

    const { checkout_url } = await SubscriptionService.createCheckout(priceId);
    window.location.href = checkout_url;
  } catch (e: unknown) {
    console.error(e);
    toastStore.addToast({
      title: 'Error',
      message: (e as Error).message || 'Failed to start checkout',
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
      title: 'Error',
      message: 'Failed to access subscription portal',
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
      title: 'Error',
      message: 'Failed to initiate purchase',
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
.bg-glass {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(10px);
}
.text-terracotta {
  color: #c97b49;
}
.bg-terracotta {
  background-color: #c97b49;
}
.bg-terracotta-dark {
  background-color: #a66136;
}
.border-terracotta {
  border-color: #c97b49;
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
