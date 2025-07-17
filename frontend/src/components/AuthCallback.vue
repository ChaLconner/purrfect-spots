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
          <p class="text-red-600 text-sm">{{ error }}</p>
          <button 
            @click="goToLogin"
            class="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            กลับไปหน้าเข้าสู่ระบบ
          </button>
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
import { ref, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { AuthService } from '../services/authService';
import { setAuth } from '../store/auth';

const router = useRouter();
const route = useRoute();

const isLoading = ref(true);
const error = ref('');
const success = ref(false);

const goToLogin = () => {
  router.push('/login');
};

onMounted(async () => {
  try {
    const code = route.query.code as string;
    const codeVerifier = sessionStorage.getItem('google_code_verifier');
    
    if (!code) {
      throw new Error('ไม่พบรหัสการยืนยัน');
    }
    
    if (!codeVerifier) {
      throw new Error('ไม่พบข้อมูลการยืนยัน');
    }
    
    // Exchange code for tokens
    const data = await AuthService.googleCodeExchange(code, codeVerifier);
    
    // Save authentication data
    setAuth(data);
    
    // Sync user data with backend
    try {
      await AuthService.syncUser();
    } catch (syncError) {
      console.warn('User sync failed:', syncError);
      // ไม่ให้ sync error หยุดการ login
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
    
  } catch (err: any) {
    console.error('🔥 OAuth Callback Error:', err);
    error.value = err.message || 'เกิดข้อผิดพลาดในการเข้าสู่ระบบ';
  } finally {
    isLoading.value = false;
  }
});
</script>
