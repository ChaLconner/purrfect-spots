<template>
  <button
    class="like-button flex items-center gap-2 transition-all duration-300 group"
    :class="[liked ? 'text-terracotta' : 'text-brown-light', { 'is-processing': isProcessing }]"
    :disabled="isProcessing"
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
const isProcessing = ref(false);
const animating = ref(false);

// Debounce timer
let debounceTimer: ReturnType<typeof setTimeout> | null = null;

// Flag to ignore realtime updates triggered by our own action
let ignoreNextRealtimeUpdate = false;

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
        // Skip if this update was triggered by our own action
        if (ignoreNextRealtimeUpdate) {
          ignoreNextRealtimeUpdate = false;
          return;
        }
        if (payload.new && typeof payload.new.likes_count === 'number') {
          count.value = payload.new.likes_count;
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
  // Clear any pending debounce
  if (debounceTimer) {
    clearTimeout(debounceTimer);
  }
});

// Watch for prop changes with proper default handling
watch(
  () => props.initialLiked,
  (val) => {
    liked.value = val ?? false;
  }
);

watch(
  () => props.initialCount,
  (val) => {
    count.value = val ?? 0;
  }
);

/**
 * Handle click with debouncing to prevent rapid clicks
 */
function handleClick() {
  // Prevent action if already processing
  if (isProcessing.value) {
    return;
  }

  // Check authentication
  if (!authStore.isAuthenticated) {
    toastStore.addToast({
      title: 'Sign in needed',
      message: 'Please sign in to like photos',
      type: 'info',
    });
    return;
  }

  // Clear any pending debounce and start new one
  if (debounceTimer) {
    clearTimeout(debounceTimer);
  }

  // Debounce: wait 150ms before actually sending the request
  // This prevents double-clicks and rapid toggling
  debounceTimer = setTimeout(() => {
    toggleLike();
  }, 150);
}

async function toggleLike() {
  // Optimistic update
  const previousLiked = liked.value;
  const previousCount = count.value;

  liked.value = !liked.value;
  count.value = liked.value ? count.value + 1 : Math.max(0, count.value - 1);

  // Trigger animation
  animating.value = true;
  setTimeout(() => {
    animating.value = false;
  }, 300);

  isProcessing.value = true;
  // Flag to ignore the realtime update we're about to trigger
  ignoreNextRealtimeUpdate = true;

  try {
    const res = await SocialService.toggleLike(props.photoId);
    // Sync with server source of truth
    liked.value = res.liked;
    count.value = res.likes_count;
    emit('update:liked', res.liked);
    emit('update:count', res.likes_count);
  } catch (e: unknown) {
    // Revert on error
    liked.value = previousLiked;
    count.value = previousCount;
    ignoreNextRealtimeUpdate = false;

    // Show user-friendly error message
    const error = e as { response?: { status?: number; data?: { detail?: string } } };
    if (error.response?.status === 404) {
      toastStore.addToast({
        title: 'Not found',
        message: 'This photo no longer exists',
        type: 'error',
      });
    } else if (error.response?.status === 503) {
      toastStore.addToast({
        title: 'Service unavailable',
        message: 'Please try again in a moment',
        type: 'warning',
      });
    } else {
      toastStore.addToast({
        title: 'Error',
        message: 'Failed to update like',
        type: 'error',
      });
    }
    console.error('Toggle like error:', e);
  } finally {
    isProcessing.value = false;
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

.like-button:hover:not(.is-processing) {
  transform: scale(1.05);
}

.like-button:active:not(.is-processing) {
  transform: scale(0.95);
}

.like-button.is-processing {
  opacity: 0.7;
  pointer-events: none;
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
