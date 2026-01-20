<script setup lang="ts">
/**
 * EditProfileModal Component
 * 
 * Modal for editing user profile with avatar upload and password change.
 */
import { ref, reactive, watch } from 'vue';
import { ProfileService } from '@/services/profileService';
import { showError, showSuccess } from '@/store/toast';
import { useFocusTrap, announce } from '@/composables/useAccessibility';

interface Props {
  isOpen: boolean;
  initialName: string;
  initialBio: string;
  initialPicture: string;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'save', data: { name: string; bio: string; picture: string }): void;
}>();

const modalRef = ref<HTMLElement | null>(null);
const fileInput = ref<HTMLInputElement | null>(null);
const isUploading = ref(false);
const isUpdatingPassword = ref(false);
const showPasswordSection = ref(false);

const editForm = reactive({
  name: props.initialName,
  bio: props.initialBio,
  picture: props.initialPicture
});

const passwordForm = reactive({
  current: '',
  new: '',
  confirm: ''
});

// Sync form when props change
watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    editForm.name = props.initialName;
    editForm.bio = props.initialBio;
    editForm.picture = props.initialPicture;
    announce('Edit profile dialog opened');
  }
});

const { activate, deactivate } = useFocusTrap(modalRef);

watch(() => props.isOpen, (isOpen) => {
  if (isOpen) {
    setTimeout(() => activate(), 100);
  } else {
    deactivate();
  }
});

const triggerFileInput = () => {
  fileInput.value?.click();
};

const handleFileSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files[0]) {
    const file = target.files[0];
    
    if (!file.type.startsWith('image/')) {
      showError('Please upload an image file');
      return;
    }

    isUploading.value = true;
    try {
      const imageUrl = await ProfileService.uploadProfilePicture(file);
      editForm.picture = imageUrl;
      showSuccess('Photo uploaded!');
      announce('Profile photo uploaded successfully');
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
    announce('Password updated successfully');
    
    // Reset password form
    passwordForm.current = '';
    passwordForm.new = '';
    passwordForm.confirm = '';
    showPasswordSection.value = false;
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Failed to update password';
    showError(message);
  } finally {
    isUpdatingPassword.value = false;
  }
};

const handleSave = () => {
  emit('save', {
    name: editForm.name,
    bio: editForm.bio,
    picture: editForm.picture
  });
};

const handleClose = () => {
  emit('close');
};

const handleBackdropClick = (event: MouseEvent) => {
  if (event.target === event.currentTarget) {
    handleClose();
  }
};

const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Escape') {
    handleClose();
  }
};
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div 
        v-if="isOpen" 
        class="fixed inset-0 bg-stone-900/40 backdrop-blur-sm flex items-center justify-center z-50 p-4"
        role="dialog"
        aria-modal="true"
        aria-labelledby="edit-profile-title"
        @click="handleBackdropClick"
        @keydown="handleKeydown"
      >
        <div 
          ref="modalRef"
          class="bg-white/90 backdrop-blur-xl rounded-[2rem] shadow-2xl p-8 w-full max-w-lg border border-white/50 transform transition-all relative overflow-hidden flex flex-col max-h-[90vh]"
          tabindex="-1"
        >
          <!-- Decorative background elements -->
          <div class="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-sage to-terracotta"></div>
          <div class="absolute -top-10 -right-10 w-32 h-32 bg-terracotta/10 rounded-full blur-2xl"></div>
          <div class="absolute -bottom-10 -left-10 w-32 h-32 bg-sage/10 rounded-full blur-2xl"></div>

          <div class="overflow-y-auto pr-2 custom-scrollbar relative z-10">
            <h2 id="edit-profile-title" class="text-3xl font-heading font-bold mb-8 text-brown text-center">
              Edit Profile
            </h2>
            
            <form class="space-y-6" @submit.prevent="handleSave">
              <!-- Profile Picture Upload -->
              <div class="flex flex-col items-center mb-6">
                <div class="relative group cursor-pointer" @click="triggerFileInput">
                  <img 
                    :src="editForm.picture || '/default-avatar.svg'" 
                    class="w-32 h-32 rounded-full object-cover border-4 border-white shadow-md transition-transform group-hover:scale-105"
                    alt="Profile picture"
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
                  aria-label="Upload profile picture"
                  @change="handleFileSelect"
                />
                <p class="text-xs text-brown-light mt-2">Click to upload new picture</p>
              </div>

              <div>
                <label for="profile-name" class="block text-xs font-bold text-brown-light mb-2 uppercase tracking-widest pl-1">
                  Name
                </label>
                <input 
                  id="profile-name"
                  v-model="editForm.name"
                  type="text"
                  class="w-full px-5 py-3.5 bg-white/60 border-2 border-stone-200 rounded-2xl focus:outline-none focus:border-terracotta focus:bg-white focus:ring-4 focus:ring-terracotta/10 transition-all duration-300 text-brown font-medium placeholder-stone-400"
                  placeholder="Your name"
                  required
                />
              </div>
              
              <div>
                <label for="profile-bio" class="block text-xs font-bold text-brown-light mb-2 uppercase tracking-widest pl-1">
                  Bio
                </label>
                <textarea 
                  id="profile-bio"
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
                  :aria-expanded="showPasswordSection"
                  @click="showPasswordSection = !showPasswordSection"
                >
                  <span class="mr-2">{{ showPasswordSection ? '−' : '+' }}</span>
                  Change Password
                </button>
                
                <div v-if="showPasswordSection" class="mt-4 space-y-4 bg-white/40 p-4 rounded-xl border border-white/60">
                  <div>
                    <label for="current-password" class="block text-xs font-bold text-brown-light mb-1 uppercase tracking-wider">
                      Current Password
                    </label>
                    <input 
                      id="current-password"
                      v-model="passwordForm.current"
                      type="password"
                      autocomplete="current-password"
                      class="w-full px-4 py-2 bg-white/60 border-2 border-stone-200 rounded-xl focus:border-terracotta focus:ring-2 focus:ring-terracotta/10 outline-none text-brown"
                    />
                  </div>
                  <div>
                    <label for="new-password" class="block text-xs font-bold text-brown-light mb-1 uppercase tracking-wider">
                      New Password
                    </label>
                    <input 
                      id="new-password"
                      v-model="passwordForm.new"
                      type="password"
                      autocomplete="new-password"
                      class="w-full px-4 py-2 bg-white/60 border-2 border-stone-200 rounded-xl focus:border-terracotta focus:ring-2 focus:ring-terracotta/10 outline-none text-brown"
                    />
                  </div>
                  <div>
                    <label for="confirm-password" class="block text-xs font-bold text-brown-light mb-1 uppercase tracking-wider">
                      Confirm New Password
                    </label>
                    <input 
                      id="confirm-password"
                      v-model="passwordForm.confirm"
                      type="password"
                      autocomplete="new-password"
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
              
              <div class="flex justify-end items-center gap-4 mt-8 pt-4 border-t border-stone-200/50 sticky bottom-0 p-2">
                <button 
                  type="button" 
                  class="px-6 py-3 text-brown-dark hover:text-black font-heading font-bold transition-colors cursor-pointer"
                  @click="handleClose"
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
    </Transition>
  </Teleport>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 3px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}
</style>
