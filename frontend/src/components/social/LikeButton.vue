<template>
  <button
    class="like-button flex items-center gap-2 transition-all duration-300 group"
    :class="[liked ? 'text-terracotta' : 'text-brown-light']"
    :aria-label="liked ? 'Unlike' : 'Like'"
    @click="handleClick"
  >
    <div
      class="p-2 rounded-full transition-all duration-300"
      :class="{ 'bg-terracotta/10': liked }"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="h-6 w-6 transition-transform"
        :class="[liked ? 'fill-current' : 'stroke-current', { 'like-animation': animating }]"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        stroke-width="2.5"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
        />
      </svg>
    </div>
    <span class="font-bold text-base font-heading">{{ count }}</span>
  </button>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue';
import { SocialService } from '@/services/socialService';
import { useAuthStore } from '@/store';
import { useToastStore } from '@/store';
import { supabase } from '@/lib/supabase';

const props = defineProps<{
  photoId: string;
  initialLiked?: boolean;
  initialCount?: number;
}>();

const emit = defineEmits<{
  (e: 'update:count', count: number): void;
  (e: 'update:liked', liked: boolean): void;
}>();

const authStore = useAuthStore();
const toastStore = useToastStore();

// State
const liked = ref(props.initialLiked ?? false);
const count = ref(props.initialCount ?? 0);
const isProcessing = ref(false); // Used to show loading state or suppress realtime, NOT to block user
const animating = ref(false);

// Debounce timer for coalescing rapid clicks
let debounceTimer: ReturnType<typeof setTimeout> | null = null;

// Track the confirmed server state for rollback and skip-if-same
let serverLiked = props.initialLiked ?? false;
let serverCount = props.initialCount ?? 0;

// Request tracking to handle out-of-order responses
let lastRequestId = 0;
let activeRequests = 0;

let realtimeChannel: ReturnType<typeof supabase.channel> | null = null;

onMounted(() => {
  // Subscribe to real-time updates for this specific photo
  realtimeChannel = supabase
    .channel(`photo_likes_${props.photoId}`)
    .on(
      'postgres_changes',
      {
        event: 'UPDATE',
        schema: 'public',
        table: 'cat_photos',
        filter: `id=eq.${props.photoId}`,
      },
      (payload) => {
        // Skip updates if we have active requests or a pending debounce
        // This prevents the UI from jittering while the user is interacting
        if (activeRequests > 0 || debounceTimer) {
          return;
        }

        if (payload.new && typeof payload.new.likes_count === 'number') {
          // If the server update matches our current state, just update the server baseline
          // preventing rollback to an old state if a race occurred
          if (payload.new.likes_count === count.value) {
            serverCount = payload.new.likes_count;
            // We can't know 'liked' status from this payload easily without user context,
            // so we generally trust our local 'liked' state unless count drastically changes.
            return;
          }

          count.value = payload.new.likes_count;
          serverCount = payload.new.likes_count;
          emit('update:count', payload.new.likes_count);
        }
      }
    )
    .subscribe();
});

onUnmounted(() => {
  if (realtimeChannel) {
    supabase.removeChannel(realtimeChannel);
  }
  if (debounceTimer) {
    clearTimeout(debounceTimer);
  }
});

watch(
  () => props.initialLiked,
  (val) => {
    // Only update from props if we're not interacting
    if (activeRequests === 0 && !debounceTimer) {
      const v = val ?? false;
      liked.value = v;
      serverLiked = v;
    }
  }
);

watch(
  () => props.initialCount,
  (val) => {
    if (activeRequests === 0 && !debounceTimer) {
      const v = val ?? 0;
      count.value = v;
      serverCount = v;
    }
  }
);

/**
 * Handle click with INSTANT optimistic update + debounced API call.
 */
function handleClick() {
  // Check authentication first
  if (!authStore.isAuthenticated) {
    toastStore.addToast({
      title: 'Want to like this?',
      message: 'Sign in to interact with users and collect your favorite spots!',
      type: 'info',
    });
    return;
  }

  // --- INSTANT optimistic update ---
  liked.value = !liked.value;
  count.value = liked.value ? count.value + 1 : Math.max(0, count.value - 1);
  emit('update:liked', liked.value);
  emit('update:count', count.value);

  // Trigger heart pop animation on every click
  animating.value = true;
  setTimeout(() => {
    animating.value = false;
  }, 300);

  // --- Debounced API call ---
  if (debounceTimer) {
    clearTimeout(debounceTimer);
  }

  debounceTimer = setTimeout(() => {
    // If user toggled back to the same state as server → no API call needed
    if (liked.value === serverLiked) {
      // Correct the count if it drifted (e.g. if we did +1 -1 but started offset)
      count.value = serverCount;
      debounceTimer = null;
      return;
    }

    // Clear timer reference before sending
    debounceTimer = null;
    sendToggleLike();
  }, 300);
}

/**
 * Send the actual API request to toggle like.
 */
async function sendToggleLike() {
  const requestId = ++lastRequestId;
  activeRequests++;
  isProcessing.value = true;

  try {
    const res = await SocialService.toggleLike(props.photoId);

    // If this is an old request (newer one started), ignore the results for UI update
    if (requestId !== lastRequestId) {
      return;
    }

    // Update server truth
    serverLiked = res.liked;
    serverCount = res.likes_count;

    // If the user has started a NEW interaction (debounceTimer exists),
    // DO NOT overwrite their optimistic state with this response.
    // The new interaction will eventually trigger its own request.
    if (debounceTimer) {
      return;
    }

    // Sync UI with server response
    liked.value = res.liked;
    count.value = res.likes_count;

    emit('update:liked', res.liked);
    emit('update:count', res.likes_count);
  } catch (e: unknown) {
    // Only rollback if this is the latest request AND no new interaction is pending
    if (requestId === lastRequestId && !debounceTimer) {
      liked.value = serverLiked;
      count.value = serverCount;

      // Show error toast
      const error = e as { response?: { status?: number; data?: { detail?: string } } };
      if (error.response?.status === 404) {
        toastStore.addToast({
          title: 'Ghost Cat?',
          message: 'This photo seems to have disappeared like a ninja.',
          type: 'error',
        });
      } else if (error.response?.status === 429) {
        // For rate limits, we should technically revert.
        toastStore.addToast({
          title: 'Slow Down!',
          message: 'Too many likes too fast! Take a breath. 🐱',
          type: 'warning',
        });
      } else if (error.response?.status === 503) {
        toastStore.addToast({
          title: 'Cat Nap in Progress',
          message: 'Our servers are taking a short break. Try again soon!',
          type: 'warning',
        });
      } else {
        toastStore.addToast({
          title: 'Hairball Error',
          message: 'Something went wrong. Please try liking again.',
          type: 'error',
        });
      }
    }
    console.error('Toggle like error:', e);
  } finally {
    activeRequests--;
    if (activeRequests === 0) {
      isProcessing.value = false;
    }
  }
}
</script>

<style scoped>
.like-button {
  cursor: pointer;
  border: none;
  background: transparent;
  outline: none;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
}

.like-button:hover {
  transform: scale(1.05);
}

.like-button:active {
  transform: scale(0.95);
}

/* Heart animation on like */
.like-animation {
  animation: heartPop 0.3s ease-out;
}

@keyframes heartPop {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.3);
  }
  100% {
    transform: scale(1);
  }
}
</style>
