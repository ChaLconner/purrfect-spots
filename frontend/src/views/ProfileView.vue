<template>
  <div class="min-h-screen pt-24 pb-12 px-4 sm:px-6 lg:px-8">
    <GhibliBackground />
    <div class="max-w-5xl mx-auto relative z-10">
      <!-- Profile Card -->
      <div class="bg-glass rounded-3xl shadow-lg p-8 mb-12 relative overflow-hidden backdrop-blur-sm border border-white/40">
        <div class="flex flex-col md:flex-row items-center gap-8 relative z-10">
          <!-- Profile Picture -->
          <div class="relative group">
            <div class="absolute inset-0 bg-terracotta rounded-full blur-md opacity-20 group-hover:opacity-40 transition-opacity duration-500"></div>
            <img
              :src="authStore.user?.picture || '/default-avatar.svg'"
              :alt="authStore.user?.name || 'User'"
              class="w-40 h-40 rounded-full object-cover border-4 border-white shadow-md relative z-10"
              @error="handleImageError"
            />
            <button 
              class="absolute bottom-2 right-2 p-2 bg-white text-terracotta rounded-full shadow-lg hover:bg-terracotta hover:text-white transition-all transform hover:scale-110 z-20 cursor-pointer"
              title="Edit Profile"
              @click="showEditModal = true"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
              </svg>
            </button>
          </div>
          
          <!-- Profile Info -->
          <div class="flex-1 text-center md:text-left">
            <h1 class="text-4xl font-heading font-bold text-brown mb-3">
              {{ authStore.user?.name || 'Unknown User' }}
            </h1>
            
            <p class="text-brown-light text-lg mb-4 max-w-xl font-body leading-relaxed">
              {{ authStore.user?.bio || 'Just a cat wandering through the world...' }}
            </p>
            
            <div class="flex flex-wrap items-center justify-center md:justify-start gap-4 text-sm text-gray-500 font-medium">
              <span class="flex items-center px-3 py-1 bg-white/50 rounded-full border border-white/60">
                <svg class="w-4 h-4 mr-2 text-sage-dark" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                Joined {{ formatJoinDate(authStore.user?.created_at) }}
              </span>
              <span class="flex items-center px-3 py-1 bg-white/50 rounded-full border border-white/60">
                <svg class="w-4 h-4 mr-2 text-terracotta" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                {{ uploads.length }} Uploads
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Content Tabs -->
      <div class="flex justify-center mb-8">
        <div class="bg-white/40 p-1.5 rounded-full inline-flex backdrop-blur-sm border border-white/40 shadow-sm">
          <button 
            :class="[
              'px-6 py-2 rounded-full font-heading font-semibold transition-all duration-300 transform cursor-pointer',
              activeTab === 'uploads' 
                ? 'bg-white text-terracotta shadow-md scale-105' 
                : 'text-brown-light hover:text-brown hover:bg-white/30'
            ]"
            @click="activeTab = 'uploads'"
          >
            My Collection
          </button>
          <button 
            :class="[
              'px-6 py-2 rounded-full font-heading font-semibold transition-all duration-300 transform cursor-pointer',
              activeTab === 'about' 
                ? 'bg-white text-terracotta shadow-md scale-105' 
                : 'text-brown-light hover:text-brown hover:bg-white/30'
            ]"
            @click="activeTab = 'about'"
          >
            About Me
          </button>
        </div>
      </div>

      <!-- Tab Content: Uploads -->
      <div v-if="activeTab === 'uploads'" class="min-h-[300px]">
        <!-- Loading State -->
        <!-- Loading State -->
        <div v-if="uploadsLoading" class="flex flex-col justify-center items-center py-20">
          <GhibliLoader text="Gathering memories..." />
        </div>
        
        <!-- Error State -->
        <ErrorState 
          v-else-if="uploadsError" 
          :message="uploadsError" 
          @retry="loadUploads"
        />
        
        <!-- No Uploads State -->
        <EmptyState 
          v-else-if="uploads.length === 0"
          title="Your Collection"
          message="No photos yet"
          sub-message="Start your journey by uploading a cat photo!"
          action-text="Upload Photo"
          action-link="/upload"
        />
        
        <!-- Uploads Grid (Pinterest Masonry Style) -->
        <div v-else class="columns-2 md:columns-3 lg:columns-4 gap-4 p-4 space-y-4">
          <div 
            v-for="upload in uploads" 
            :key="upload.id"
            class="break-inside-avoid mb-4 group relative rounded-2xl overflow-hidden cursor-pointer shadow-md hover:shadow-xl transition-all duration-300"
            @click="openImageModal(upload)"
          >
            <!-- Image -->
            <img 
              :src="upload.image_url" 
              :alt="upload.description || 'Cat photo'"
              class="w-full h-auto block"
              loading="lazy"
            />
          </div>
        </div>
      </div>

      <!-- Tab Content: About -->
      <div v-if="activeTab === 'about'" class="bg-white/60 p-8 rounded-3xl shadow-sm border border-white/50 backdrop-blur-md max-w-2xl mx-auto">
        <h3 class="text-2xl font-heading font-bold text-brown mb-6 flex items-center">
          <span class="text-4xl mr-3">🍃</span> About Me
        </h3>
        <div class="space-y-6">
          <div class="bg-white/50 p-6 rounded-2xl border border-white/60">
            <p class="text-brown leading-relaxed font-body text-lg">
              {{ authStore.user?.bio || 'This user hasn\'t written a bio yet.' }}
            </p>
          </div>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="flex items-center p-4 bg-sage/10 rounded-xl border border-sage/20">
              <div class="bg-sage/20 p-2 rounded-full mr-3 text-sage-dark">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <div class="min-w-0">
                <p class="text-xs text-sage-dark uppercase font-bold tracking-wider">Email</p>
                <p class="text-brown text-sm font-medium truncate" :title="authStore.user?.email">{{ authStore.user?.email }}</p>
              </div>
            </div>
            
            <div class="flex items-center p-4 bg-terracotta/10 rounded-xl border border-terracotta/20">
              <div class="bg-terracotta/20 p-2 rounded-full mr-3 text-terracotta-dark">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <div>
                <p class="text-xs text-terracotta-dark uppercase font-bold tracking-wider">Joined</p>
                <p class="text-brown text-sm font-medium">{{ formatJoinDate(authStore.user?.created_at) }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Profile Modal -->
    <div v-if="showEditModal" class="fixed inset-0 bg-stone-900/40 backdrop-blur-sm flex items-center justify-center z-50 p-4 transition-all duration-300">
      <div 
        class="bg-white/90 backdrop-blur-xl rounded-[2rem] shadow-2xl p-8 w-full max-w-lg border border-white/50 transform transition-all scale-100 relative overflow-hidden flex flex-col max-h-[90vh]"
      >
        <!-- Decorative background elements -->
        <div class="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-sage to-terracotta"></div>
        <div class="absolute -top-10 -right-10 w-32 h-32 bg-terracotta/10 rounded-full blur-2xl"></div>
        <div class="absolute -bottom-10 -left-10 w-32 h-32 bg-sage/10 rounded-full blur-2xl"></div>

        <div class="overflow-y-auto pr-2 custom-scrollbar relative z-10">
          <h2 class="text-3xl font-heading font-bold mb-8 text-brown text-center">Edit Profile</h2>
          
          <form class="space-y-6" @submit.prevent="saveProfile">
            <!-- Profile Picture Upload -->
            <div class="flex flex-col items-center mb-6">
              <div class="relative group cursor-pointer" @click="triggerFileInput">
                <img 
                  :src="editForm.picture || '/default-avatar.svg'" 
                  class="w-32 h-32 rounded-full object-cover border-4 border-white shadow-md transition-transform group-hover:scale-105"
                />
                <div class="absolute inset-0 bg-black/40 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                  <span class="text-white text-sm font-bold">Change Photo</span>
                </div>
                <div v-if="isUploading" class="absolute inset-0 bg-white/60 rounded-full flex items-center justify-center">
                  <div class="w-8 h-8 border-2 border-terracotta border-t-transparent rounded-full animate-spin"></div>
                </div>
              </div>
              <input 
                ref="fileInput"
                type="file" 
                accept="image/*" 
                class="hidden" 
                @change="handleFileSelect"
              />
              <p class="text-xs text-brown-light mt-2">Click to upload new picture</p>
            </div>

            <div>
              <label class="block text-xs font-bold text-brown-light mb-2 uppercase tracking-widest pl-1">Name</label>
              <input 
                v-model="editForm.name"
                type="text"
                class="w-full px-5 py-3.5 bg-white/60 border-2 border-stone-200 rounded-2xl focus:outline-none focus:border-terracotta focus:bg-white focus:ring-4 focus:ring-terracotta/10 transition-all duration-300 text-brown font-medium placeholder-stone-400"
                placeholder="Your name"
                required
              />
            </div>
            
            <div>
              <label class="block text-xs font-bold text-brown-light mb-2 uppercase tracking-widest pl-1">Bio</label>
              <textarea 
                v-model="editForm.bio"
                class="w-full px-5 py-3.5 bg-white/60 border-2 border-stone-200 rounded-2xl focus:outline-none focus:border-terracotta focus:bg-white focus:ring-4 focus:ring-terracotta/10 transition-all duration-300 text-brown font-medium resize-none placeholder-stone-400"
                rows="4"
                placeholder="Tell us a bit about yourself..."
              ></textarea>
            </div>
            
            <!-- Change Password Section -->
            <div class="border-t border-stone-200 pt-6 mt-6">
              <button 
                type="button" 
                class="flex items-center text-terracotta font-bold text-sm uppercase tracking-wider hover:text-terracotta-dark transition-colors"
                @click="showPasswordSection = !showPasswordSection"
              >
                <span class="mr-2">{{ showPasswordSection ? '−' : '+' }}</span>
                Change Password
              </button>
              
              <div v-if="showPasswordSection" class="mt-4 space-y-4 bg-white/40 p-4 rounded-xl border border-white/60">
                <div>
                  <label class="block text-xs font-bold text-brown-light mb-1 uppercase tracking-wider">Current Password</label>
                  <input 
                    v-model="passwordForm.current"
                    type="password"
                    class="w-full px-4 py-2 bg-white/60 border-2 border-stone-200 rounded-xl focus:border-terracotta focus:ring-2 focus:ring-terracotta/10 outline-none text-brown"
                  />
                </div>
                <div>
                  <label class="block text-xs font-bold text-brown-light mb-1 uppercase tracking-wider">New Password</label>
                  <input 
                    v-model="passwordForm.new"
                    type="password"
                    class="w-full px-4 py-2 bg-white/60 border-2 border-stone-200 rounded-xl focus:border-terracotta focus:ring-2 focus:ring-terracotta/10 outline-none text-brown"
                  />
                </div>
                <div>
                  <label class="block text-xs font-bold text-brown-light mb-1 uppercase tracking-wider">Confirm New Password</label>
                  <input 
                    v-model="passwordForm.confirm"
                    type="password"
                    class="w-full px-4 py-2 bg-white/60 border-2 border-stone-200 rounded-xl focus:border-terracotta focus:ring-2 focus:ring-terracotta/10 outline-none text-brown"
                  />
                </div>
                <!-- Password Save Button -->
                <div class="flex justify-end mt-2">
                  <button 
                    type="button"
                    :disabled="isUpdatingPassword || !passwordForm.current || !passwordForm.new"
                    class="px-5 py-2.5 bg-[#C07040] text-white rounded-lg text-sm font-bold hover:bg-[#A05030] shadow-md transition-all disabled:opacity-50 disabled:shadow-none"
                    @click="updatePassword"
                  >
                    {{ isUpdatingPassword ? 'Updating...' : 'Update Password' }}
                  </button>
                </div>
              </div>
            </div>
            
            <div class="flex justify-end items-center gap-4 mt-8 pt-4 border-t border-stone-200/50 sticky bottom-0 bg-white/0 backdrop-blur-none p-2">
              <button 
                type="button" 
                class="px-6 py-3 text-brown-dark hover:text-black font-heading font-bold transition-colors cursor-pointer"
                @click="showEditModal = false"
              >
                Cancel
              </button>
              <button 
                type="submit"
                class="px-8 py-3 bg-[#C07040] hover:bg-[#A05030] text-white rounded-xl shadow-lg hover:shadow-xl hover:scale-[1.02] transition-all duration-300 cursor-pointer font-heading font-extrabold tracking-wide"
              >
                Save Profile
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Image Modal -->
    <Transition
      enter-active-class="transition duration-300 ease-out"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition duration-200 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div v-if="selectedImage" class="fixed inset-0 bg-stone-900/80 backdrop-blur-md z-50 flex items-center justify-center p-4 md:p-8" @click="closeImageModal">
        <div 
          class="relative bg-white rounded-3xl overflow-hidden shadow-2xl max-w-6xl w-full max-h-[90vh] flex flex-col md:flex-row transform transition-all"
          @click.stop
        >
          <!-- Close Button (Minimalist) -->
          <button
            class="absolute top-6 right-6 z-20 text-stone-400 hover:text-brown bg-transparent transition-colors p-1"
            @click="closeImageModal"
          >
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>

          <!-- Image Section -->
          <div class="w-full md:w-3/5 bg-stone-100 flex items-center justify-center relative overflow-hidden h-[45vh] md:h-auto group">
            <!-- Main Image -->
            <img
              :src="selectedImage.image_url"
              class="w-full h-full object-cover z-10"
              :alt="selectedImage.description || 'Cat photo'"
            />
          </div>

          <!-- Details Section -->
          <div class="w-full md:w-2/5 bg-white flex flex-col h-auto md:h-auto relative">
            <div class="p-8 md:p-10 flex flex-col h-full">
              <!-- Header: User Info -->
              <div class="flex items-center gap-4 mb-8 pt-2">
                <img :src="authStore.user?.picture || '/default-avatar.svg'" class="w-14 h-14 rounded-full object-cover border-2 border-stone-100 shadow-sm" />
                <div>
                  <h4 class="text-brown font-heading font-bold text-xl leading-none mb-1">{{ authStore.user?.name }}</h4>
                  <p class="text-xs text-stone-400 font-medium uppercase tracking-widest">
                    Uploaded {{ new Date(selectedImage.uploaded_at).toLocaleDateString() }}
                  </p>
                </div>
              </div>

              <!-- Content -->
              <div class="flex-grow overflow-y-auto custom-scrollbar pr-2 space-y-4">
                <div>
                  <h3 class="text-3xl font-heading font-extrabold text-terracotta mb-2 leading-tight">
                    {{ selectedImage.location_name || 'Unknown Spot' }}
                  </h3>
                  <div class="h-1 w-20 bg-sage/30 rounded-full"></div>
                </div>
                 
                <p v-if="selectedImage.description && selectedImage.description !== '-'" class="text-brown-light font-body leading-relaxed text-lg whitespace-pre-wrap">
                  {{ selectedImage.description }}
                </p>
                <p v-else class="text-stone-300 italic">No description provided.</p>
              </div>

              <!-- Footer Actions -->
              <div class="mt-8 pt-6 border-t border-stone-100 flex justify-between items-center text-stone-400 text-sm">
                <span class="flex items-center text-brown-light font-medium bg-stone-50 px-3 py-1.5 rounded-lg">
                  <svg class="w-4 h-4 mr-2 text-terracotta" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                  {{ selectedImage.latitude ? 'Location tagged' : 'No location' }}
                </span>
                  
                <!-- Like/Action buttons could go here -->
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, reactive, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '../store/authStore';
const authStore = useAuthStore();
import { showError, showSuccess } from '../store/toast';
import { ProfileService, type ProfileUpdateData } from '../services/profileService';
import { isDev } from '../utils/env';
import ErrorState from '@/components/ui/ErrorState.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import GhibliLoader from '@/components/ui/GhibliLoader.vue';
import GhibliBackground from '@/components/ui/GhibliBackground.vue';
import { useSeo } from '@/composables/useSeo';

const router = useRouter();
const route = useRoute();
const { setMetaTags, resetMetaTags } = useSeo();

interface Upload {
  id: string;
  image_url: string;
  description?: string;
  location_name?: string;
  latitude?: number;
  longitude?: number;
  uploaded_at: string;
}

const activeTab = ref('uploads');
const uploads = ref<Upload[]>([]);
const uploadsLoading = ref(false);
const uploadsError = ref<string | null>(null);

const showEditModal = ref(false);
const selectedImage = ref<Upload | null>(null);
const fileInput = ref<HTMLInputElement | null>(null);
const isUploading = ref(false);
const showPasswordSection = ref(false);
const isUpdatingPassword = ref(false);

const editForm = reactive({
  name: '',
  bio: '',
  picture: ''
});

const passwordForm = reactive({
  current: '',
  new: '',
  confirm: ''
});

const triggerFileInput = () => {
    fileInput.value?.click();
};

const handleFileSelect = async (event: Event) => {
    const target = event.target as HTMLInputElement;
    if (target.files && target.files[0]) {
        const file = target.files[0];
        
        // Validate file type
        if (!file.type.startsWith('image/')) {
            showError('Please upload an image file');
            return;
        }

        // Upload immediately
        isUploading.value = true;
        try {
            const imageUrl = await ProfileService.uploadProfilePicture(file);
            editForm.picture = imageUrl;
            showSuccess('Photo uploaded!');
        } catch {
            showError('Failed to upload photo');
        } finally {
            isUploading.value = false;
        }
    }
};

const updatePassword = async () => {
    if (passwordForm.new !== passwordForm.confirm) {
        showError('New passwords do not match');
        return;
    }
    
    if (passwordForm.new.length < 8) {
        showError('Password must be at least 8 characters');
        return;
    }

    isUpdatingPassword.value = true;
    try {
        await ProfileService.changePassword({
            current_password: passwordForm.current,
            new_password: passwordForm.new
        });
        showSuccess('Password updated successfully');
        // Reset password form
        passwordForm.current = '';
        passwordForm.new = '';
        passwordForm.confirm = '';
        showPasswordSection.value = false;
    } catch (error: unknown) {
        showError((error as Error).message || 'Failed to update password');
    } finally {
        isUpdatingPassword.value = false;
    }
};

const formatJoinDate = (dateString: string | undefined) => {
  if (!dateString) return 'Unknown';
  
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long' });
};

const handleImageError = (event: Event) => {
  const target = event.target as HTMLImageElement;
  if (!target.src.includes('default-avatar.svg')) {
    target.src = '/default-avatar.svg';
  }
};

const loadUploads = async () => {
  uploadsLoading.value = true;
  uploadsError.value = null;
  
  try {
    const userUploads = await ProfileService.getUserUploads();
    uploads.value = userUploads;
  } catch (error) {
    if (isDev()) {
      console.error('Error loading uploads:', error);
    }
    
    if (error instanceof Error && error.message.includes('Authentication expired')) {
      uploadsError.value = 'Your session has expired. Please log in again.';
      setTimeout(() => {
        router.push('/auth');
      }, 2000);
    } else if (error instanceof Error && error.message.includes('No authentication token')) {
      uploadsError.value = 'Please log in to view your uploads.';
      setTimeout(() => {
        router.push('/auth');
      }, 2000);
    } else {
      uploadsError.value = 'Failed to load uploads. Please try again later.';
    }
    showError(uploadsError.value);
    
    uploads.value = [];
  } finally {
    uploadsLoading.value = false;
  }
};

// Sync modal state from URL
const syncStateFromUrl = () => {
  const imageId = route.query.image as string;
  if (!imageId) {
    selectedImage.value = null;
    return;
  }
  
  const foundImage = uploads.value.find(img => img.id === imageId);
  if (foundImage) {
    selectedImage.value = foundImage;
  }
};

// Watch for URL changes
watch(() => route.query.image, () => {
  syncStateFromUrl();
});

const openImageModal = (upload: Upload) => {
  router.push({ query: { ...route.query, image: upload.id } });
};

const closeImageModal = () => {
  const query = { ...route.query };
  delete query.image;
  router.push({ query });
};

const saveProfile = async () => {
  try {
    const updateData: ProfileUpdateData = {
      name: editForm.name,
      bio: editForm.bio,
      picture: editForm.picture
    };

    const updatedUser = await ProfileService.updateProfile(updateData);
    
    // Update local store
    if (authStore.user) {
      authStore.user.name = updatedUser.name;
      authStore.user.bio = updatedUser.bio;
      authStore.user.picture = updatedUser.picture;
      
      // Update localStorage
      localStorage.setItem('user_data', JSON.stringify(authStore.user));
    }
    
    showEditModal.value = false;
    showSuccess('Profile updated successfully!');
  } catch (error) {
    if (isDev()) {
      console.error('Error saving profile:', error);
    }
    
    // Handle authentication errors specifically
    if (error instanceof Error && error.message.includes('Authentication expired')) {
      // Redirect to login after a short delay
      setTimeout(() => {
        router.push('/auth');
      }, 2000);
    } else if (error instanceof Error && error.message.includes('No authentication token')) {
      // Redirect to login after a short delay
      setTimeout(() => {
        router.push('/auth');
      }, 2000);
    }
    
    const msg = error instanceof Error ? error.message : 'Failed to update profile';
    showError(msg);
  }
};

onMounted(async () => {
  // Set SEO meta tags
  setMetaTags({
    title: 'Profile | Purrfect Spots',
    description: 'View and manage your Purrfect Spots profile and cat photo uploads.',
    type: 'website'
  });
  
  // Load user uploads
  await loadUploads();
  
  // Sync state from URL after data is loaded
  syncStateFromUrl();
  
  // Initialize edit form with current user data
  if (authStore.user) {
    editForm.name = authStore.user.name || '';
    editForm.bio = authStore.user.bio || '';
    editForm.picture = authStore.user.picture || '';
  }
});

// Cleanup on unmount
onUnmounted(() => {
  resetMetaTags();
});
</script>

<style scoped>
/* Scoped styles mainly for specific overrides if needed */
.aspect-square {
  aspect-ratio: 1 / 1;
}

/* Custom scrollbar for textareas if needed */
textarea::-webkit-scrollbar {
  width: 8px;
}
textarea::-webkit-scrollbar-track {
  background: #f1f1f1;
}
textarea::-webkit-scrollbar-thumb {
  background: #C97B49;
  border-radius: 4px;
}
</style>
