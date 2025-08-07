<template>
  <div class="min-h-screen bg-gray-50 flex items-center justify-center">
    <div class="max-w-md w-full bg-white rounded-lg shadow-md p-6">
      <div class="text-center">
        <div v-if="isLoading" class="mb-4">
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p class="mt-4 text-gray-600">กำลังประมวลผล...</p>
        </div>
        
        <div v-if="error" class="mb-4">
          <div class="text-red-500 text-4xl mb-2">❌</div>
          <h2 class="text-xl font-semibold text-gray-800 mb-2">เกิดข้อผิดพลาด</h2>
          <p class="text-red-600 text-sm mb-3">{{ error }}</p>
          
          <!-- Browser extension help message -->
          <div v-if="error.includes('ส่วนขยาย')" class="bg-yellow-50 border border-yellow-200 rounded-md p-3 mb-3">
            <div class="text-yellow-800 text-xs">
              <p class="font-semibold mb-1">💡 วิธีแก้ไข:</p>
              <ul class="list-disc list-inside space-y-1">
                <li>ปิดส่วนขยายของเบราว์เซอร์ชั่วคราว</li>
                <li>ลองใช้ Incognito/Private mode</li>
                <li>หรือลองใช้เบราว์เซอร์อื่น</li>
              </ul>
            </div>
          </div>
          
          <div class="space-x-2">
            <button 
              @click="goToLogin"
              class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              กลับไปหน้าเข้าสู่ระบบ
            </button>
            <button 
              @click="reloadPage"
              class="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
            >
              ลองใหม่
            </button>
          </div>
        </div>
        
        <div v-if="success" class="mb-4">
          <div class="text-green-500 text-4xl mb-2">✅</div>
          <h2 class="text-xl font-semibold text-gray-800 mb-2">เข้าสู่ระบบสำเร็จ</h2>
          <p class="text-gray-600 text-sm">กำลังเปลี่ยนหน้า...</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onErrorCaptured } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { AuthService } from '../services/authService';
import { setAuth } from '../store/auth';

const router = useRouter();
const route = useRoute();

const isLoading = ref(true);
const error = ref('');
const success = ref(false);

// Error handling for browser extension conflicts
onErrorCaptured((err) => {
  // Ignore extension-related errors
  if (err.message && err.message.includes('message channel closed')) {
    console.warn('Browser extension conflict detected in callback, ignoring:', err.message);
    return false; // Prevent the error from propagating
  }
  return true; // Let other errors propagate normally
});

// Handle unhandled promise rejections (often from extensions)
onMounted(() => {
  window.addEventListener('unhandledrejection', (event) => {
    if (
      event.reason &&
      event.reason.message &&
      event.reason.message.includes('message channel closed')
    ) {
      console.warn('Prevented extension error in callback:', event.reason.message);
      event.preventDefault();
    }
  });
});

const goToLogin = () => {
  router.push('/login');
};

const reloadPage = () => {
  window.location.reload();
};

const handleAuthCallback = async () => {
  let retryCount = 0;
  const maxRetries = 3;
  
  while (retryCount < maxRetries) {
    try {
      const code = route.query.code as string;
      const codeVerifier = sessionStorage.getItem('google_code_verifier');
      
      if (!code) {
        throw new Error('ไม่พบรหัสการยืนยัน');
      }
      
      if (!codeVerifier) {
        throw new Error('ไม่พบข้อมูลการยืนยัน');
      }
      
      // Exchange code for tokens with retry logic
      const data = await AuthService.googleCodeExchange(code, codeVerifier);
      
      // Save authentication data
      setAuth(data);
      
      // Sync user data with backend
      try {
        await AuthService.syncUser();
      } catch (syncError: any) {
        console.warn('⚠️ User sync failed:', syncError);
        // Don't let sync error stop the login process
      }
      
      // Clean up
      sessionStorage.removeItem('google_code_verifier');
      
      success.value = true;
      
      // Redirect to intended destination
      setTimeout(() => {
        const redirectPath = sessionStorage.getItem('redirectAfterAuth') || '/';
        sessionStorage.removeItem('redirectAfterAuth');
        router.push(redirectPath);
      }, 1000);
      
      return; // Success, exit retry loop
      
    } catch (err: any) {
      console.error(`🔥 OAuth Callback Error (attempt ${retryCount + 1}):`, err);
      
      // Handle browser extension errors
      if (err.message && err.message.includes('message channel closed')) {
        console.warn('🔧 Browser extension conflict detected, retrying...');
        retryCount++;
        if (retryCount < maxRetries) {
          await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second before retry
          continue;
        }
      }
      
      // Handle network errors
      if (err.message === 'Failed to fetch') {
        error.value = 'ไม่สามารถเชื่อมต่อกับเซิร์ฟเวอร์ได้ กรุณาตรวจสอบการเชื่อมต่ออินเทอร์เน็ต';
      } else {
        error.value = err.message || 'เกิดข้อผิดพลาดในการเข้าสู่ระบบ';
      }
      break;
    }
  }
  
  if (retryCount >= maxRetries) {
    error.value = 'เกิดข้อผิดพลาดจากส่วนขยายของเบราว์เซอร์ กรุณาปิดส่วนขยายและลองใหม่อีกครั้ง';
  }
};

onMounted(async () => {
  try {
    await handleAuthCallback();
  } finally {
    isLoading.value = false;
  }
});
</script>
