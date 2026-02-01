<script setup lang="ts">
/**
 * EditProfileModal Component
 *
 * Modal for editing user profile with avatar upload and password change.
 */
import { ref, reactive, watch, computed } from 'vue';
import { ProfileService } from '@/services/profileService';
import { showError, showSuccess } from '@/store/toast';
import { useFocusTrap, announce } from '@/composables/useAccessibility';
import { useAuthStore } from '@/store/authStore';
import PasswordStrengthMeter from '@/components/ui/PasswordStrengthMeter.vue';

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
const showPasswords = ref(false); // Toggle for password visibility

const passwordRequirements = computed(() => {
  const p = passwordForm.new;
  return [{ label: 'Min 8 characters', met: p.length >= 8 }];
});

const editForm = reactive({
  name: props.initialName,
  bio: props.initialBio,
  picture: props.initialPicture,
});

const passwordForm = reactive({
  current: '',
  new: '',
  confirm: '',
});

const authStore = useAuthStore();
const isSocialUser = computed(() => {
  // Logic to determine if user is from social provider
  // Usually social users have avatars from google/facebook domains
  const avatarUrl = props.initialPicture || '';

  const isSocialDomain = (url: string) => {
    try {
      const hostname = new URL(url).hostname;
      return hostname.endsWith('googleusercontent.com') || hostname.endsWith('facebook.com');
    } catch {
      return false;
    }
  };

  return (
    isSocialDomain(avatarUrl) || (authStore.user?.picture && isSocialDomain(authStore.user.picture))
  );
});

// Sync form when props change
watch(
  () => props.isOpen,
  (newVal) => {
    if (newVal) {
      editForm.name = props.initialName;
      editForm.bio = props.initialBio;
      editForm.picture = props.initialPicture;
      announce('Edit profile dialog opened');
    }
  }
);

const { activate, deactivate } = useFocusTrap(modalRef);

watch(
  () => props.isOpen,
  (isOpen) => {
    if (isOpen) {
      setTimeout(() => activate(), 100);
    } else {
      deactivate();
    }
  }
);

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
      // showSuccess('Photo uploaded!'); // Removed: Visual update in form is sufficient
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
      new_password: passwordForm.new,
    });
    showSuccess('Password updated successfully');
    announce('Password updated successfully');

    // Reset password form
    passwordForm.current = '';
    passwordForm.new = '';
    passwordForm.confirm = '';
    showPasswordSection.value = false;
  } catch (err: unknown) {
    let message = err instanceof Error ? err.message : 'Failed to update password';
    if (message.includes('status code')) message = 'Unable to update password. Please try again.';
    showError(message);
  } finally {
    isUpdatingPassword.value = false;
  }
};

const handleSave = () => {
  emit('save', {
    name: editForm.name,
    bio: editForm.bio,
    picture: editForm.picture,
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
          <div
            class="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-sage to-terracotta"
          ></div>
          <div
            class="absolute -top-10 -right-10 w-32 h-32 bg-terracotta/10 rounded-full blur-2xl"
          ></div>
          <div
            class="absolute -bottom-10 -left-10 w-32 h-32 bg-sage/10 rounded-full blur-2xl"
          ></div>

          <div class="overflow-y-auto pr-2 custom-scrollbar relative z-10">
            <h2
              id="edit-profile-title"
              class="text-3xl font-heading font-bold mb-8 text-brown text-center"
            >
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
                  <div
                    class="absolute inset-0 bg-black/40 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <span class="text-white text-sm font-bold">Change Photo</span>
                  </div>
                  <div
                    v-if="isUploading"
                    class="absolute inset-0 bg-white/60 rounded-full flex items-center justify-center"
                  >
                    <div
                      class="w-8 h-8 border-2 border-terracotta border-t-transparent rounded-full animate-spin"
                    ></div>
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
                <label
                  for="profile-name"
                  class="block text-xs font-bold text-brown-light mb-2 uppercase tracking-widest pl-1"
                >
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
                <label
                  for="profile-bio"
                  class="block text-xs font-bold text-brown-light mb-2 uppercase tracking-widest pl-1"
                >
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
                  class="flex items-center text-terracotta font-bold text-sm uppercase tracking-wider hover:text-terracotta-dark transition-colors cursor-pointer"
                  :aria-expanded="showPasswordSection"
                  @click="showPasswordSection = !showPasswordSection"
                >
                  <span class="mr-2">{{ showPasswordSection ? '−' : '+' }}</span>
                  Change Password
                </button>

                <div
                  v-if="showPasswordSection"
                  class="mt-4 space-y-4 bg-white/40 p-4 rounded-xl border border-white/60"
                >
                  <div
                    v-if="isSocialUser"
                    class="bg-amber-50/80 border-l-4 border-amber-400 p-4 rounded-r-xl shadow-sm"
                  >
                    <p class="text-amber-900 text-sm font-medium leading-relaxed">
                      This account is linked with a social provider (Google/Facebook). Please manage
                      your password through your social account settings.
                    </p>
                  </div>

                  <template v-else>
                    <div>
                      <label
                        for="current-password"
                        class="block text-xs font-bold text-brown-light mb-1 uppercase tracking-wider"
                      >
                        Current Password
                      </label>
                      <div class="relative">
                        <input
                          id="current-password"
                          v-model="passwordForm.current"
                          :type="showPasswords ? 'text' : 'password'"
                          autocomplete="current-password"
                          required
                          class="w-full px-4 py-2 bg-white/60 border-2 border-stone-200 rounded-xl focus:border-terracotta focus:ring-2 focus:ring-terracotta/10 outline-none text-brown pr-10"
                        />
                        <button
                          type="button"
                          class="absolute right-3 top-1/2 -translate-y-1/2 text-stone-400 hover:text-terracotta transition-colors cursor-pointer"
                          :aria-label="showPasswords ? 'Hide password' : 'Show password'"
                          @click="showPasswords = !showPasswords"
                        >
                          <svg
                            v-if="!showPasswords"
                            xmlns="http://www.w3.org/2000/svg"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke-width="1.5"
                            stroke="currentColor"
                            class="w-5 h-5"
                          >
                            <path
                              stroke-linecap="round"
                              stroke-linejoin="round"
                              d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z"
                            />
                            <path
                              stroke-linecap="round"
                              stroke-linejoin="round"
                              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                            />
                          </svg>
                          <svg
                            v-else
                            xmlns="http://www.w3.org/2000/svg"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke-width="1.5"
                            stroke="currentColor"
                            class="w-5 h-5"
                          >
                            <path
                              stroke-linecap="round"
                              stroke-linejoin="round"
                              d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88"
                            />
                          </svg>
                        </button>
                      </div>
                    </div>
                    <div>
                      <label
                        for="new-password"
                        class="block text-xs font-bold text-brown-light mb-1 uppercase tracking-wider"
                      >
                        New Password
                      </label>
                      <div class="relative">
                        <input
                          id="new-password"
                          v-model="passwordForm.new"
                          :type="showPasswords ? 'text' : 'password'"
                          autocomplete="new-password"
                          required
                          class="w-full px-4 py-2 bg-white/60 border-2 border-stone-200 rounded-xl focus:border-terracotta focus:ring-2 focus:ring-terracotta/10 outline-none text-brown pr-10"
                        />
                      </div>
                      <div class="mt-3 flex flex-wrap gap-2">
                        <span
                          v-for="req in passwordRequirements"
                          :key="req.label"
                          class="text-[10px] px-2 py-1 rounded-full border transition-all duration-300"
                          :class="
                            req.met
                              ? 'bg-sage/20 border-sage text-sage-dark'
                              : 'bg-stone-50 border-stone-200 text-stone-400'
                          "
                        >
                          {{ req.met ? '✓' : '○' }} {{ req.label }}
                        </span>
                      </div>
                      <div class="mt-2">
                        <PasswordStrengthMeter :password="passwordForm.new" />
                      </div>
                    </div>
                    <div>
                      <label
                        for="confirm-password"
                        class="block text-xs font-bold text-brown-light mb-1 uppercase tracking-wider"
                      >
                        Confirm New Password
                      </label>
                      <input
                        id="confirm-password"
                        v-model="passwordForm.confirm"
                        :type="showPasswords ? 'text' : 'password'"
                        autocomplete="new-password"
                        required
                        class="w-full px-4 py-2 bg-white/60 border-2 border-stone-200 rounded-xl focus:border-terracotta focus:ring-2 focus:ring-terracotta/10 outline-none text-brown"
                      />
                    </div>
                    <!-- Password Save Button -->
                    <div class="flex justify-end mt-2">
                      <button
                        type="button"
                        :disabled="
                          isUpdatingPassword ||
                            !passwordForm.current ||
                            !passwordForm.new ||
                            !passwordForm.confirm
                        "
                        class="px-5 py-2.5 bg-[#C07040] text-white rounded-lg text-sm font-bold hover:bg-[#A05030] shadow-md transition-all disabled:opacity-50 disabled:shadow-none cursor-pointer disabled:cursor-not-allowed"
                        @click="updatePassword"
                      >
                        {{ isUpdatingPassword ? 'Updating...' : 'Update Password' }}
                      </button>
                    </div>
                  </template>
                </div>
              </div>

              <div
                class="flex justify-end items-center gap-4 mt-8 pt-4 border-t border-stone-200/50 sticky bottom-0 p-2"
              >
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
