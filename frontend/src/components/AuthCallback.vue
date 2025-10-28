<template>
  <div class="fixed inset-0 min-h-screen bg-transparent flex items-center justify-center z-50">
    <div class="max-w-md w-full bg-white rounded-lg shadow-md p-6">
      <div class="text-center">
        <div v-if="isLoading" class="mb-4">
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p class="mt-4 text-gray-600">Loading...</p>
        </div>
        
        <div v-if="error" class="mb-4">
          <div class="text-red-500 text-4xl mb-2">❌</div>
          <h2 class="text-xl font-semibold text-gray-800 mb-2">oops!</h2>
          <p class="text-red-600 text-sm mb-3">{{ error }}</p>
          
          <!-- Browser extension help message -->
          <div v-if="error.includes('extension')" class="bg-yellow-50 border border-yellow-200 rounded-md p-3 mb-3">
            <div class="text-yellow-800 text-xs">
              <p class="font-semibold mb-1">💡 How to fix:</p>
              <ul class="list-disc list-inside space-y-1">
                <li>Temporarily disable browser extensions</li>
                <li>Try using Incognito/Private mode</li>
                <li>Or try a different browser</li>
              </ul>
            </div>
          </div>
          
          <div class="space-x-2">
            <button 
              @click="goToLogin"
              class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Go to Login
            </button>
            <button 
              @click="reloadPage"
              class="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
            >
             Try Again
            </button>
          </div>
        </div>
        
        <div v-if="success" class="mb-4">
          <div class="text-green-500 text-4xl mb-2">✅</div>
          <h2 class="text-xl font-semibold text-gray-800 mb-2">Successfully</h2>
          
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
        throw new Error('Authentication code not found from Google');
      }
      
      if (!codeVerifier) {
        throw new Error('Authentication data not found. Please try logging in again.');
      }
      
      // Exchange code for tokens with retry logic
      console.log('Exchanging code for tokens...', { code: code ? 'present' : 'missing', codeVerifier: codeVerifier ? 'present' : 'missing' });
      const data = await AuthService.googleCodeExchange(code, codeVerifier);
      console.log('Token exchange successful', data);
      
      // Save authentication data
      setAuth(data);
      
      // Sync user data with backend
      try {
        await AuthService.syncUser();
      } catch (syncError: any) {
        // Don't let sync error stop the login process
      }
      
      // Clean up
      sessionStorage.removeItem('google_code_verifier');
      
      success.value = true;
      
      // Redirect to intended destination
      setTimeout(() => {
        const redirectPath = sessionStorage.getItem('redirectAfterAuth') || '/upload';
        sessionStorage.removeItem('redirectAfterAuth');
        router.push(redirectPath);
      }, 1000);
      
      return; // Success, exit retry loop
      
    } catch (err: any) {
      // Handle browser extension errors
      if (err.message && err.message.includes('message channel closed')) {
        retryCount++;
        if (retryCount < maxRetries) {
          await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second before retry
          continue;
        }
      }
      
      // Handle specific OAuth errors
      if (err.message && err.message.includes('invalid_grant')) {
        error.value = 'Authentication expired. Please try logging in again.';
      } else if (err.message && err.message.includes('redirect_uri')) {
        error.value = 'Invalid OAuth configuration. Please contact the administrator.';
      } else if (err.message === 'Failed to fetch') {
        error.value = 'Cannot connect to server. Please check your internet connection.';
      } else {
        error.value = err.message || 'An error occurred during login.';
      }
      break;
    }
  }
  
  if (retryCount >= maxRetries) {
    error.value = 'An error occurred from browser extensions. Please disable extensions and try again.';
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
