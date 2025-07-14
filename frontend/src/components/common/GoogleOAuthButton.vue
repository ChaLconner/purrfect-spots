<template>
  <div>
    <!-- Google Sign-In Button -->
    <button
      v-if="!isLoading"
      @click="handleGoogleLogin"
      class="flex items-center justify-center gap-3 w-full bg-white border border-gray-300 rounded-lg px-6 py-3 text-gray-700 font-medium hover:bg-gray-50 hover:shadow-md transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
    >
      <svg class="w-5 h-5" viewBox="0 0 24 24">
        <path
          fill="#4285F4"
          d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
        />
        <path
          fill="#34A853"
          d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
        />
        <path
          fill="#FBBC05"
          d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
        />
        <path
          fill="#EA4335"
          d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
        />
      </svg>
      <span>{{ buttonText }}</span>
    </button>

    <!-- Loading state -->
    <div v-else class="flex items-center justify-center gap-3 w-full bg-gray-100 border border-gray-300 rounded-lg px-6 py-3">
      <LoadingSpinner size="sm" :show-text="false" />
      <span class="text-gray-600">กำลังเข้าสู่ระบบ...</span>
    </div>

    <!-- Error message -->
    <div v-if="errorMessage" class="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
      <p class="text-red-600 text-sm">{{ errorMessage }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { AuthService } from '../../services/authService';
import { setAuth } from '../../store/auth';
import LoadingSpinner from './LoadingSpinner.vue';

interface Props {
  buttonText?: string;
}

withDefaults(defineProps<Props>(), {
  buttonText: 'เข้าสู่ระบบด้วย Google'
});

const emit = defineEmits<{
  loginSuccess: [user: any];
  loginError: [error: string];
}>();

const isLoading = ref(false);
const errorMessage = ref('');

// Google Sign-In handling
const handleGoogleLogin = async () => {
  if (!window.google) {
    errorMessage.value = 'Google Sign-In ไม่พร้อมใช้งาน กรุณาลองใหม่อีกครั้ง';
    return;
  }

  isLoading.value = true;
  errorMessage.value = '';

  try {
    const response = await new Promise((resolve, reject) => {
      window.google.accounts.id.prompt((notification: any) => {
        if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
          reject(new Error('การเข้าสู่ระบบถูกยกเลิก'));
        }
      });

      window.google.accounts.id.initialize({
        client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID,
        callback: (response: any) => {
          resolve(response);
        },
      });

      window.google.accounts.id.prompt();
    });

    // Send token to backend
    const loginData = await AuthService.loginWithGoogle((response as any).credential);
    
    // Store authentication data
    setAuth(loginData);
    
    emit('loginSuccess', loginData.user);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'เกิดข้อผิดพลาดในการเข้าสู่ระบบ';
    errorMessage.value = message;
    emit('loginError', message);
  } finally {
    isLoading.value = false;
  }
};

// Initialize Google Sign-In
onMounted(() => {
  // Load Google Sign-In script if not already loaded
  if (!window.google) {
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    document.head.appendChild(script);
  }
});
</script>

<style scoped>
/* Additional styles if needed */
</style>
