<script setup lang="ts">
import { useI18n } from 'vue-i18n';

/**
 * ProfileHeader Component
 *
 * Displays user profile card with avatar, name, bio, and stats.
 */
defineProps<{
  name: string;
  username?: string;
  bio?: string;
  picture?: string;
  createdAt?: string;
  uploadsCount: number;
  isPro?: boolean;
  treatBalance?: number;
  isOwnProfile?: boolean;
}>();

defineEmits<{
  (e: 'edit' | 'logout'): void;
  (e: 'imageError', event: Event): void;
}>();

const { t, locale } = useI18n();

const formatJoinDate = (dateString?: string) => {
  if (!dateString) return t('common.unknown');
  const date = new Date(dateString);
  return date.toLocaleDateString(locale.value, { year: 'numeric', month: 'long' });
};
</script>

<template>
  <div
    class="bg-glass rounded-2xl md:rounded-3xl shadow-lg p-4 sm:p-6 md:p-8 mb-8 sm:mb-10 md:mb-12 relative overflow-hidden backdrop-blur-sm border border-white/40"
  >
    <!-- Decoration Circles -->
    <div
      class="absolute -top-10 -right-10 w-40 h-40 bg-orange-100 rounded-full opacity-50 blur-3xl pointer-events-none"
    ></div>
    <div
      class="absolute -bottom-10 -left-10 w-40 h-40 bg-green-100 rounded-full opacity-50 blur-3xl pointer-events-none"
    ></div>

    <div class="flex flex-col md:flex-row items-center gap-4 sm:gap-6 md:gap-8 relative z-10">
      <!-- Profile Picture -->
      <div class="relative group">
        <div
          class="absolute inset-0 bg-terracotta rounded-full blur-md opacity-20 group-hover:opacity-40 transition-opacity duration-500"
        ></div>
        <img
          :src="picture || '/default-avatar.svg'"
          :alt="name || t('profile.unknownUser')"
          class="w-28 h-28 sm:w-32 sm:h-32 md:w-36 md:h-36 lg:w-40 lg:h-40 rounded-full object-cover border-4 border-white shadow-md relative z-10"
          @error="$emit('imageError', $event)"
        />
        <button
          v-if="isOwnProfile"
          class="absolute bottom-2 right-2 p-1.5 sm:p-2 bg-white text-terracotta rounded-full shadow-lg hover:bg-terracotta hover:text-white transition-all transform hover:scale-110 z-20 cursor-pointer"
          :title="t('common.edit')"
          :aria-label="t('common.edit')"
          @click="$emit('edit')"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-4 w-4 sm:h-5 sm:w-5"
            viewBox="0 0 20 20"
            fill="currentColor"
            aria-hidden="true"
          >
            <path
              d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z"
            />
          </svg>
        </button>
      </div>

      <!-- Profile Info -->
      <div class="flex-1 text-center md:text-left">
        <h1 class="text-2xl sm:text-3xl md:text-4xl font-heading font-bold text-brown mb-1">
          {{ name || t('profile.unknownUser') }}
        </h1>
        <p
          v-if="username"
          class="text-terracotta font-medium mb-3 sm:mb-4 flex items-center justify-center md:justify-start gap-2 text-sm sm:text-base"
        >
          @{{ username }}
        </p>

        <p
          class="text-brown-light text-base sm:text-lg mb-3 sm:mb-4 max-w-xl font-body leading-relaxed"
        >
          {{ bio || t('profile.defaultBio') }}
        </p>

        <div
          class="flex flex-wrap items-center justify-center md:justify-start gap-2 sm:gap-3 md:gap-4 text-xs sm:text-sm text-gray-500 font-medium"
        >
          <!-- PRO Badge -->
          <div
            v-if="isPro"
            class="flex items-center px-2.5 sm:px-3 py-1 bg-gradient-to-r from-yellow-400 to-orange-500 text-white rounded-full shadow-sm border border-orange-400/30 text-xs sm:text-sm"
          >
            <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path d="M5 4a2 2 0 012-2h6a2 2 0 012 2v14l-5-2.5L5 18V4z" />
            </svg>
            {{ t('common.pro') }}
          </div>

          <!-- Join Date -->
          <span
            class="flex items-center px-2.5 sm:px-3 py-1 bg-white/50 rounded-full border border-white/60 text-xs sm:text-sm"
          >
            <svg
              class="w-4 h-4 mr-2 text-sage-dark"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            {{ t('profile.joined') }} {{ formatJoinDate(createdAt) }}
          </span>

          <!-- Uploads Count -->
          <span
            class="flex items-center px-2.5 sm:px-3 py-1 bg-white/50 rounded-full border border-white/60 text-xs sm:text-sm"
          >
            <svg
              class="w-4 h-4 mr-2 text-terracotta"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            {{ uploadsCount }} {{ t('profile.uploads') }}
          </span>

          <!-- Treats Count -->
          <span
            class="flex items-center px-2.5 sm:px-3 py-1 bg-orange-50 rounded-full border border-orange-200 text-orange-700 shadow-sm text-xs sm:text-sm"
          >
            <img
              src="/give-treat.png"
              alt=""
              class="w-4 h-4 mr-1.5 object-contain"
              aria-hidden="true"
              loading="lazy"
            />
            <span class="mr-1.5">{{ t('profile.treats') }}</span>
            {{ treatBalance || 0 }}
          </span>
        </div>

        <!-- Action Buttons -->
        <div class="mt-3 sm:mt-4 flex justify-center md:justify-start gap-2 sm:gap-3">
          <router-link
            v-if="isOwnProfile && !isPro"
            to="/subscription"
            class="text-xs bg-terracotta/10 text-terracotta hover:bg-terracotta hover:text-white px-3 py-1 rounded-lg transition-all font-bold border border-terracotta/20"
          >
            {{ t('profile.upgradeToPro') }}
          </router-link>
          <router-link
            to="/leaderboard"
            class="text-xs bg-sage/10 text-sage-dark hover:bg-sage hover:text-white px-3 py-1 rounded-lg transition-all font-bold border border-sage/20"
          >
            {{ t('common.leaderboard') }}
          </router-link>

          <!-- Logout Button (Mobile/Tablet only) -->
          <button
            v-if="isOwnProfile"
            class="text-xs bg-red-50 text-red-600 hover:bg-red-600 hover:text-white px-3 py-1 rounded-lg transition-all font-bold border border-red-200 lg:hidden"
            @click="$emit('logout')"
          >
            {{ t('auth.logout') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
