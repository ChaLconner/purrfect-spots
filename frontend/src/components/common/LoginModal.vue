<template>
  <Transition name="modal" appear>
    <div
      v-if="show"
      @click="closeModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4"
    >
      <div
        @click.stop
        class="bg-white rounded-xl shadow-2xl w-full max-w-md mx-auto transform transition-all"
      >
        <!-- Header -->
        <div class="px-6 py-4 border-b border-gray-200">
          <div class="flex items-center justify-between">
            <h2 class="text-xl font-semibold text-gray-900">เข้าสู่ระบบ</h2>
            <button
              @click="closeModal"
              class="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Content -->
        <div class="px-6 py-6">
          <div class="text-center mb-6">
            <div class="mx-auto w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center mb-4">
              <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
            <p class="text-gray-600">เข้าสู่ระบบเพื่อแชร์รูปแมวและสร้างความทรงจำดีๆ ร่วมกับชุมชน</p>
          </div>

          <!-- Google OAuth Button -->
          <GoogleOAuthButton
            @login-success="handleLoginSuccess"
            @login-error="handleLoginError"
            button-text="เข้าสู่ระบบด้วย Google"
          />

          <!-- Terms -->
          <p class="text-xs text-gray-500 text-center mt-4">
            การเข้าสู่ระบบหมายความว่าคุณยอมรับ
            <a href="#" class="text-blue-600 hover:underline">เงื่อนไขการใช้งาน</a>
            และ
            <a href="#" class="text-blue-600 hover:underline">นโยบายความเป็นส่วนตัว</a>
          </p>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { defineEmits, defineProps } from 'vue';
import GoogleOAuthButton from './GoogleOAuthButton.vue';
import type { User } from '../../types/auth';

interface Props {
  show: boolean;
}

defineProps<Props>();

const emit = defineEmits<{
  close: [];
  loginSuccess: [user: User];
}>();

const closeModal = () => {
  emit('close');
};

const handleLoginSuccess = (user: User) => {
  emit('loginSuccess', user);
  closeModal();
};

const handleLoginError = (error: string) => {
  console.error('Login error:', error);
  // You can show a toast notification here
};
</script>

<style scoped>
/* Modal transition animations */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .bg-white,
.modal-leave-active .bg-white {
  transition: all 0.3s ease;
}

.modal-enter-from .bg-white,
.modal-leave-to .bg-white {
  transform: scale(0.9) translateY(-10px);
  opacity: 0;
}
</style>
