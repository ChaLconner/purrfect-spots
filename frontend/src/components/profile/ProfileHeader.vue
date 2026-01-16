<script setup lang="ts">
/**
 * ProfileHeader Component
 * 
 * Displays user profile card with avatar, name, bio, and stats.
 */
defineProps<{
  name: string;
  bio?: string;
  picture?: string;
  email?: string;
  createdAt?: string;
  uploadsCount: number;
}>();

defineEmits<{
  (e: 'edit'): void;
  (e: 'imageError', event: Event): void;
}>();

const formatJoinDate = (dateString: string | undefined) => {
  if (!dateString) return 'Unknown';
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long' });
};
</script>

<template>
  <div class="bg-glass rounded-3xl shadow-lg p-8 mb-12 relative overflow-hidden backdrop-blur-sm border border-white/40">
    <!-- Decoration Circles -->
    <div class="absolute -top-10 -right-10 w-40 h-40 bg-orange-100 rounded-full opacity-50 blur-3xl"></div>
    <div class="absolute -bottom-10 -left-10 w-40 h-40 bg-green-100 rounded-full opacity-50 blur-3xl"></div>

    <div class="flex flex-col md:flex-row items-center gap-8 relative z-10">
      <!-- Profile Picture -->
      <div class="relative group">
        <div class="absolute inset-0 bg-terracotta rounded-full blur-md opacity-20 group-hover:opacity-40 transition-opacity duration-500"></div>
        <img
          :src="picture || '/default-avatar.svg'"
          :alt="name || 'User'"
          class="w-40 h-40 rounded-full object-cover border-4 border-white shadow-md relative z-10"
          @error="$emit('imageError', $event)"
        />
        <button 
          class="absolute bottom-2 right-2 p-2 bg-white text-terracotta rounded-full shadow-lg hover:bg-terracotta hover:text-white transition-all transform hover:scale-110 z-20 cursor-pointer"
          title="Edit Profile"
          aria-label="Edit profile"
          @click="$emit('edit')"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
            <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
          </svg>
        </button>
      </div>
      
      <!-- Profile Info -->
      <div class="flex-1 text-center md:text-left">
        <h1 class="text-4xl font-heading font-bold text-brown mb-3">
          {{ name || 'Unknown User' }}
        </h1>
        
        <p class="text-brown-light text-lg mb-4 max-w-xl font-body leading-relaxed">
          {{ bio || 'Just a cat wandering through the world...' }}
        </p>
        
        <div class="flex flex-wrap items-center justify-center md:justify-start gap-4 text-sm text-gray-500 font-medium">
          <span class="flex items-center px-3 py-1 bg-white/50 rounded-full border border-white/60">
            <svg class="w-4 h-4 mr-2 text-sage-dark" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            Joined {{ formatJoinDate(createdAt) }}
          </span>
          <span class="flex items-center px-3 py-1 bg-white/50 rounded-full border border-white/60">
            <svg class="w-4 h-4 mr-2 text-terracotta" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            {{ uploadsCount }} Uploads
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
