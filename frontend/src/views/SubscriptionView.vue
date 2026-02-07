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
              <button
                class="w-full bg-stone-100 text-stone-500 py-3 rounded-2xl hover:bg-stone-200 transition-colors font-bold text-sm"
                @click="handleCancel"
              >
                Cancel Subscription
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
          Show some love to your favorite cats! 🍬 Treats let you tip creators and earn a spot on
          the leaderboard.
        </p>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <!-- Tier 1: Small -->
          <div
            class="bg-glass p-6 rounded-3xl border border-white/60 shadow-md hover:shadow-lg transition-all text-center flex flex-col group"
          >
            <div
              class="h-16 mb-4 flex items-center justify-center transition-transform group-hover:scale-110"
            >
              <img src="/give-treat.png" alt="Treat" class="h-full object-contain" />
            </div>
            <h4 class="text-lg font-bold text-brown mb-1">Tiny Snack</h4>
            <p class="text-3xl font-extrabold text-brown mb-4">
              10 <span class="text-sm font-normal text-stone-400">Treats</span>
            </p>
            <div class="mt-auto">
              <button
                class="w-full py-2.5 bg-white text-brown border-2 border-stone-100 hover:border-terracotta hover:text-terracotta rounded-xl font-bold transition-all text-sm mb-2"
                @click="buyTreats('small')"
              >
                ฿49
              </button>
              <p class="text-[10px] text-stone-400 uppercase tracking-tighter">฿4.90 per treat</p>
            </div>
          </div>

          <!-- Tier 2: Medium (Target) -->
          <div
            class="bg-white p-6 rounded-3xl border-2 border-sage shadow-xl hover:shadow-2xl transition-all text-center flex flex-col relative transform scale-105 group"
          >
            <div
              class="absolute -top-3 left-1/2 -translate-x-1/2 bg-sage text-white text-[10px] font-bold px-3 py-1 rounded-full uppercase tracking-wider shadow-sm"
            >
              Best Value
            </div>
            <div
              class="h-16 mb-4 flex items-center justify-center transition-transform group-hover:scale-110"
            >
              <img src="/give-treat.png" alt="Treat" class="h-full object-contain" />
            </div>
            <h4 class="text-lg font-bold text-brown mb-1">Fishy Feast</h4>
            <p class="text-3xl font-extrabold text-brown mb-1">
              35 <span class="text-sm font-normal text-stone-400">Treats</span>
            </p>
            <p class="text-sage-dark font-bold text-xs mb-4">30 + 5 FREE!</p>
            <div class="mt-auto">
              <button
                class="w-full py-3 bg-sage hover:bg-sage-dark text-white rounded-xl font-bold shadow-lg shadow-sage/20 transition-all text-sm mb-2"
                @click="buyTreats('medium')"
              >
                ฿129
              </button>
              <p class="text-[10px] text-stone-400 uppercase tracking-tighter line-through mb-0.5">
                ฿171 VALUE
              </p>
              <p class="text-[10px] text-sage-dark font-bold uppercase tracking-tighter">
                ฿3.68 per treat
              </p>
            </div>
          </div>

          <!-- Tier 3: Large -->
          <div
            class="bg-glass p-6 rounded-3xl border border-white/60 shadow-md hover:shadow-lg transition-all text-center flex flex-col group"
          >
            <div
              class="h-16 mb-4 flex items-center justify-center transition-transform group-hover:scale-110"
            >
              <img src="/give-treat.png" alt="Treat" class="h-full object-contain" />
            </div>
            <h4 class="text-lg font-bold text-brown mb-1">Meaty Banquet</h4>
            <p class="text-3xl font-extrabold text-brown mb-1">
              125 <span class="text-sm font-normal text-stone-400">Treats</span>
            </p>
            <p class="text-terracotta font-bold text-xs mb-4">100 + 25 FREE!</p>
            <div class="mt-auto">
              <button
                class="w-full py-2.5 bg-white text-brown border-2 border-stone-100 hover:border-terracotta hover:text-terracotta rounded-xl font-bold transition-all text-sm mb-2"
                @click="buyTreats('large')"
              >
                ฿399
              </button>
              <p class="text-[10px] text-stone-400 uppercase tracking-tighter line-through mb-0.5">
                ฿612 VALUE
              </p>
              <p class="text-[10px] text-terracotta font-bold uppercase tracking-tighter">
                ฿3.19 per treat
              </p>
            </div>
          </div>

          <!-- Tier 4: Legendary -->
          <div
            class="bg-glass p-6 rounded-3xl border border-white/60 shadow-md hover:shadow-lg transition-all text-center flex flex-col group"
          >
            <div
              class="h-16 mb-4 flex items-center justify-center transition-transform group-hover:scale-110"
            >
              <img src="/give-treat.png" alt="Treat" class="h-full object-contain" />
            </div>
            <h4 class="text-lg font-bold text-brown mb-1">Royal Buffet</h4>
            <p class="text-3xl font-extrabold text-brown mb-1">
              650 <span class="text-sm font-normal text-stone-400">Treats</span>
            </p>
            <p class="text-orange-500 font-bold text-xs mb-4">500 + 150 FREE!</p>
            <div class="mt-auto">
              <button
                class="w-full py-2.5 bg-white text-brown border-2 border-stone-100 hover:border-terracotta hover:text-terracotta rounded-xl font-bold transition-all text-sm mb-2"
                @click="buyTreats('legendary')"
              >
                ฿1,499
              </button>
              <p class="text-[10px] text-stone-400 uppercase tracking-tighter line-through mb-0.5">
                ฿3,185 VALUE
              </p>
              <p class="text-[10px] text-orange-500 font-bold uppercase tracking-tighter">
                ฿3.57 per treat
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
import { useSubscriptionStore } from '../store/subscriptionStore';
import { SubscriptionService } from '../services/subscriptionService';
import { TreatsService } from '../services/treatsService';
import { useToastStore } from '../store/toastStore';
import GhibliBackground from '@/components/ui/GhibliBackground.vue';
import { useSeo } from '@/composables/useSeo';

const subscriptionStore = useSubscriptionStore();
const toastStore = useToastStore();
const isLoading = ref(false);
const { setMetaTags } = useSeo();

onMounted(() => {
  subscriptionStore.fetchStatus();
  setMetaTags({
    title: 'Subscription & Treats | Purrfect Spots',
    description: 'Upgrade your account and support the community with treats.',
  });
});

async function handleSubscribe() {
  isLoading.value = true;
  try {
    const priceId = import.meta.env.VITE_STRIPE_PRO_PRICE_ID;
    if (!priceId) throw new Error('Price ID not configured');

    const { checkout_url } = await SubscriptionService.createCheckout(priceId);
    window.location.href = checkout_url;
  } catch (e: any) {
    console.error(e);
    toastStore.addToast({
      title: 'Error',
      message: e.message || 'Failed to start checkout',
      type: 'error',
    });
  } finally {
    isLoading.value = false;
  }
}

async function handleCancel() {
  if (
    !window.confirm(
      'Are you sure you want to cancel your subscription? You will lose Pro features at the end of the billing period.'
    )
  )
    return;
  try {
    await SubscriptionService.cancel();
    toastStore.addToast({ title: 'Success', message: 'Subscription cancelled', type: 'success' });
    await subscriptionStore.fetchStatus();
  } catch (e) {
    console.error(e);
    toastStore.addToast({ title: 'Error', message: 'Failed to cancel', type: 'error' });
  }
}

async function buyTreats(packageType: 'small' | 'medium' | 'large' | 'legendary') {
  isLoading.value = true;
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
    isLoading.value = false;
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
