<template>
  <div>
    <!-- Modern Google OAuth Button -->
    <button
      v-if="!isLoading"
      @click="handleModernGoogleLogin"
      class="flex items-center justify-center gap-3 w-full bg-white border border-gray-300 rounded-lg px-6 py-3 text-gray-700 font-medium hover:bg-gray-50 hover:shadow-md transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 relative overflow-hidden"
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
      <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
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

// Generate a random state parameter for security
const generateState = (): string => {
  const array = new Uint32Array(1);
  crypto.getRandomValues(array);
  return array[0].toString(36);
};

// Generate code verifier for PKCE
const generateCodeVerifier = (): string => {
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return btoa(String.fromCharCode.apply(null, Array.from(array)))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');
};

// Generate code challenge from verifier
const generateCodeChallenge = async (verifier: string): Promise<string> => {
  const encoder = new TextEncoder();
  const data = encoder.encode(verifier);
  const digest = await crypto.subtle.digest('SHA-256', data);
  return btoa(String.fromCharCode.apply(null, Array.from(new Uint8Array(digest))))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');
};

// Modern OAuth 2.0 Authorization Code Flow with PKCE
const handleModernGoogleLogin = async () => {
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
  
  if (!clientId || clientId === 'your_google_client_id.apps.googleusercontent.com') {
    errorMessage.value = 'Google Client ID ยังไม่ได้ตั้งค่า กรุณาดูคู่มือการตั้งค่า OAuth';
    return;
  }

  try {
    isLoading.value = true;
    errorMessage.value = '';

    // Generate PKCE parameters
    const codeVerifier = generateCodeVerifier();
    const codeChallenge = await generateCodeChallenge(codeVerifier);
    const state = generateState();

    // Store PKCE parameters in sessionStorage
    sessionStorage.setItem('oauth_code_verifier', codeVerifier);
    sessionStorage.setItem('oauth_state', state);

    // Build OAuth 2.0 authorization URL
    const authUrl = new URL('https://accounts.google.com/o/oauth2/v2/auth');
    authUrl.searchParams.set('client_id', clientId);
    authUrl.searchParams.set('redirect_uri', window.location.origin + '/auth/callback');
    authUrl.searchParams.set('response_type', 'code');
    authUrl.searchParams.set('scope', 'openid email profile');
    authUrl.searchParams.set('state', state);
    authUrl.searchParams.set('code_challenge', codeChallenge);
    authUrl.searchParams.set('code_challenge_method', 'S256');
    authUrl.searchParams.set('access_type', 'offline');
    authUrl.searchParams.set('prompt', 'consent');

    console.log('OAuth URL:', authUrl.toString());
    console.log('Redirect URI:', window.location.origin + '/auth/callback');

    // Redirect to Google OAuth
    window.location.href = authUrl.toString();

  } catch (error) {
    const message = error instanceof Error ? error.message : 'เกิดข้อผิดพลาดในการเข้าสู่ระบบ';
    errorMessage.value = message;
    emit('loginError', message);
    isLoading.value = false;
  }
};

// Handle OAuth callback
const handleOAuthCallback = async () => {
  const urlParams = new URLSearchParams(window.location.search);
  const code = urlParams.get('code');
  const state = urlParams.get('state');
  const error = urlParams.get('error');

  console.log('OAuth Callback - URL params:', { code: !!code, state: !!state, error });

  if (error) {
    console.error('OAuth Error:', error);
    errorMessage.value = `OAuth Error: ${error}`;
    return;
  }

  if (!code || !state) {
    console.log('No OAuth callback detected');
    return; // Not an OAuth callback
  }

  const storedState = sessionStorage.getItem('oauth_state');
  const codeVerifier = sessionStorage.getItem('oauth_code_verifier');

  console.log('OAuth Callback - Stored data:', { 
    storedState: !!storedState, 
    codeVerifier: !!codeVerifier,
    stateMatch: state === storedState 
  });

  if (state !== storedState) {
    console.error('State mismatch:', { received: state, stored: storedState });
    errorMessage.value = 'Invalid state parameter. Possible security issue.';
    return;
  }

  if (!codeVerifier) {
    console.error('Missing code verifier');
    errorMessage.value = 'Missing code verifier. Please try again.';
    return;
  }

  try {
    isLoading.value = true;
    console.log('Exchanging code for tokens...');

    // Exchange authorization code for tokens
    const loginData = await AuthService.exchangeCodeForTokens({
      code,
      codeVerifier,
      redirectUri: window.location.origin + '/auth/callback'
    });

    console.log('OAuth Success:', { user: loginData.user?.email });

    // Clean up
    sessionStorage.removeItem('oauth_state');
    sessionStorage.removeItem('oauth_code_verifier');
    
    // Clear URL parameters
    window.history.replaceState({}, document.title, window.location.pathname);

    // Store authentication data
    setAuth(loginData);
    
    emit('loginSuccess', loginData.user);

  } catch (error) {
    console.error('Token exchange error:', error);
    const message = error instanceof Error ? error.message : 'เกิดข้อผิดพลาดในการแลกเปลี่ยน token';
    errorMessage.value = message;
    emit('loginError', message);
  } finally {
    isLoading.value = false;
  }
};

// Initialize and check for OAuth callback
onMounted(() => {
  // Check if this is an OAuth callback
  handleOAuthCallback();
});
</script>

<style scoped>
/* Additional styles if needed */
</style>
