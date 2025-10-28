<template>
  <div class="max-w-md mx-auto mt-10 p-6 bg-indigo-50 shadow rounded-xl">
  <div class="max-w-md mx-auto mt-10 p-6 bg-indigo-50 shadow rounded-xl">
    <h2 class="text-2xl font-semibold mb-4 text-center">
      {{ isLogin ? 'Sign In' : 'Sign Up' }}
      {{ isLogin ? 'Sign In' : 'Sign Up' }}
    </h2>

    <form @submit.prevent="handleSubmit" class="space-y-4">
      <div class="relative w-full mb-4">
        <input
          v-model="form.email"
          type="email"
          required
          placeholder=" "
          class="peer block w-full rounded-md border border-gray-300 bg-transparent px-3 pt-5 pb-2 text-gray-900 transition-all duration-300 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-300"
        />
        <label
          for="email"
          class="absolute left-3 top-2 text-gray-500 transition-all duration-300
            peer-placeholder-shown:top-5
            peer-placeholder-shown:text-gray-400
            peer-placeholder-shown:text-base
            peer-focus:top-2
            peer-focus:text-sm
            peer-focus:text-blue-500"
        >
          Email
        </label>
      <div class="relative w-full mb-4">
        <input
          v-model="form.email"
          type="email"
          required
          placeholder=" "
          class="peer block w-full rounded-md border border-gray-300 bg-transparent px-3 pt-5 pb-2 text-gray-900 transition-all duration-300 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-300"
        />
        <label
          for="email"
          class="absolute left-3 top-2 text-gray-500 transition-all duration-300
            peer-placeholder-shown:top-5
            peer-placeholder-shown:text-gray-400
            peer-placeholder-shown:text-base
            peer-focus:top-2
            peer-focus:text-sm
            peer-focus:text-blue-500"
        >
          Email
        </label>
      </div>

      <div class="relative w-full mb-4">
        <input
          v-model="form.password"
          type="password"
          required
          placeholder=" "
          class="peer block w-full rounded-md border border-gray-300 bg-transparent px-3 pt-5 pb-2 text-gray-900 transition-all duration-300 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-300"
        />
        <label
          for="password"
          class="absolute left-3 top-2 text-gray-500 transition-all duration-300
            peer-placeholder-shown:top-5
            peer-placeholder-shown:text-gray-400
            peer-placeholder-shown:text-base
            peer-focus:top-2
            peer-focus:text-sm
            peer-focus:text-blue-500"
        >
          Password
        </label>
      <div class="relative w-full mb-4">
        <input
          v-model="form.password"
          type="password"
          required
          placeholder=" "
          class="peer block w-full rounded-md border border-gray-300 bg-transparent px-3 pt-5 pb-2 text-gray-900 transition-all duration-300 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-300"
        />
        <label
          for="password"
          class="absolute left-3 top-2 text-gray-500 transition-all duration-300
            peer-placeholder-shown:top-5
            peer-placeholder-shown:text-gray-400
            peer-placeholder-shown:text-base
            peer-focus:top-2
            peer-focus:text-sm
            peer-focus:text-blue-500"
        >
          Password
        </label>
      </div>

      <div v-if="!isLogin" class="relative w-full mb-4">
        <input
          v-model="form.name"
          type="text"
          required
          placeholder=" "
          class="peer block w-full rounded-md border border-gray-300 bg-transparent px-3 pt-5 pb-2 text-gray-900 transition-all duration-300 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-300"
        />
        <label
          for="name"
          class="absolute left-3 top-2 text-gray-500 transition-all duration-300
            peer-placeholder-shown:top-5
            peer-placeholder-shown:text-gray-400
            peer-placeholder-shown:text-base
            peer-focus:top-2
            peer-focus:text-sm
            peer-focus:text-blue-500"
        >
          Full Name
        </label>
      <div v-if="!isLogin" class="relative w-full mb-4">
        <input
          v-model="form.name"
          type="text"
          required
          placeholder=" "
          class="peer block w-full rounded-md border border-gray-300 bg-transparent px-3 pt-5 pb-2 text-gray-900 transition-all duration-300 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-300"
        />
        <label
          for="name"
          class="absolute left-3 top-2 text-gray-500 transition-all duration-300
            peer-placeholder-shown:top-5
            peer-placeholder-shown:text-gray-400
            peer-placeholder-shown:text-base
            peer-focus:top-2
            peer-focus:text-sm
            peer-focus:text-blue-500"
        >
          Full Name
        </label>
      </div>

      <button :disabled="isLoading" class="btn w-full cursor-pointer">
        {{ isLoading ? 'Loading...' : isLogin ? 'Sign In' : 'Sign Up' }}
      </button>
    </form>

    <!-- OAuth Section -->
    <div class="mt-6">
      <div class="relative">
        <div class="absolute inset-0 flex items-center">
          <div class="w-full border-t border-gray-300"></div>
        </div>
        <div class="relative flex justify-center text-sm">
          <span class="px-2 bg-indigo-50 text-gray-500">or</span>
          <span class="px-2 bg-indigo-50 text-gray-500">or</span>
        </div>
      </div>
      
      <div class="mt-6">
        <button
          @click="handleGoogleLogin"
          :disabled="isLoading"
          type="button"
          class="w-full flex justify-center items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 cursor-pointer"
        >
          <svg class="w-5 h-5 mr-2" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Sign in with Google
          Sign in with Google
        </button>
      </div>
    </div>

    <div v-if="errorMessage" class="mt-4 text-sm text-red-600">
      {{ errorMessage }}
    </div>

    <div class="mt-6 text-sm text-center">
      <span>
        {{ isLogin ? "Don't have an account?" : 'Already have an account?' }}
        {{ isLogin ? "Don't have an account?" : 'Already have an account?' }}
        <router-link 
          :to="isLogin ? '/register' : '/login'" 
          class="text-blue-600 hover:underline"
        >
          {{ isLogin ? 'Sign Up' : 'Sign In' }}
          {{ isLogin ? 'Sign Up' : 'Sign In' }}
        </router-link>
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { setAuth, isUserReady } from '../store/auth';
import { AuthService } from '../services/authService';
import { isDev, getEnvVar } from '../utils/env';

interface Props {
  initialMode?: 'login' | 'register';
}

const props = withDefaults(defineProps<Props>(), {
  initialMode: 'login'
});

const isLogin = ref(props.initialMode !== 'register');
const isLoading = ref(false);
const errorMessage = ref('');
const router = useRouter();

// Watch for changes in initialMode prop
watch(() => props.initialMode, (newMode: 'login' | 'register' | undefined) => {
  isLogin.value = newMode !== 'register';
  errorMessage.value = '';
});

const form = reactive({
  email: '',
  password: '',
  name: '',
});

// Check if user is already logged in
onMounted(() => {
  if (isUserReady()) {
    const redirectPath = sessionStorage.getItem('redirectAfterAuth') || '/';
    sessionStorage.removeItem('redirectAfterAuth');
    router.push(redirectPath);
  }
});

const handleSubmit = async () => {
  isLoading.value = true;
  errorMessage.value = '';

  try {
    // ✅ Client-side validation
    if (!form.email.trim()) {
      throw new Error('Please enter your email');
      throw new Error('Please enter your email');
    }
    
    if (!form.password.trim()) {
      throw new Error('Please enter your password');
      throw new Error('Please enter your password');
    }
    
    if (!isLogin.value) {
      if (!form.name.trim()) {
        throw new Error('Please enter your full name');
        throw new Error('Please enter your full name');
      }
      
      if (form.password.length < 6) {
        throw new Error('Password must be at least 6 characters');
        throw new Error('Password must be at least 6 characters');
      }
    }

    let data;
    if (isLogin.value) {
      data = await AuthService.login(form.email, form.password);
    } else {
      data = await AuthService.signup(form.email, form.password, form.name);
    }

    setAuth(data);

    const redirectPath = sessionStorage.getItem('redirectAfterAuth') || '/';
    sessionStorage.removeItem('redirectAfterAuth');
    router.push(redirectPath);
  } catch (err: any) {
    errorMessage.value = err.message || 'Something went wrong';
    errorMessage.value = err.message || 'Something went wrong';
  } finally {
    isLoading.value = false;
  }
};

const handleGoogleLogin = async () => {
  isLoading.value = true;
  errorMessage.value = '';

  try {
    const googleClientId = getEnvVar('VITE_GOOGLE_CLIENT_ID') || '40710057825-09pahjbe71ncf7adq9c8892r2mivm9b3.apps.googleusercontent.com';
    const redirectUri = `${window.location.origin}/auth/callback`;
    
    const codeVerifier = generateCodeVerifier();
    const codeChallenge = await generateCodeChallenge(codeVerifier);
    
    sessionStorage.setItem('google_code_verifier', codeVerifier);
    
    const oauthUrl = new URL('https://accounts.google.com/o/oauth2/v2/auth');
    oauthUrl.searchParams.append('client_id', googleClientId);
    oauthUrl.searchParams.append('redirect_uri', redirectUri);
    oauthUrl.searchParams.append('response_type', 'code');
    oauthUrl.searchParams.append('scope', 'openid email profile');
    oauthUrl.searchParams.append('code_challenge', codeChallenge);
    oauthUrl.searchParams.append('code_challenge_method', 'S256');
    oauthUrl.searchParams.append('access_type', 'offline');
    oauthUrl.searchParams.append('prompt', 'consent');
    
    window.location.href = oauthUrl.toString();
  } catch (err: any) {
    if (isDev()) {
      console.error('Google OAuth Error:', err);
    }
    errorMessage.value = err.message || 'Google sign-in failed';
    isLoading.value = false;
  }
};

// PKCE helper functions
function generateCodeVerifier(): string {
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return base64URLEncode(array);
}

async function generateCodeChallenge(codeVerifier: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(codeVerifier);
  const digest = await crypto.subtle.digest('SHA-256', data);
  return base64URLEncode(new Uint8Array(digest));
}

function base64URLEncode(array: Uint8Array): string {
  return btoa(String.fromCharCode(...array))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');
}
</script>

<style scoped>
.input-wrapper {
  position: relative;
  margin-bottom: 1.5rem;
}

.input-wrapper {
  position: relative;
  margin-bottom: 1.5rem;
}

.input {
  border: 1px solid #ccc;
  padding: 0.5rem 0.75rem;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  background: #f8fafc;
  width: 100%;
  transition: border-color 0.2s;
}

.input:focus {
  border-color: #4f46e5;
  outline: none;
}

.floating-label {
  position: absolute;
  left: 0.75rem;
  top: 50%;
  transform: translateY(-50%) translateX(-120%);
  color: #6b7280;
  pointer-events: none;
  background: transparent;
  padding: 0 0.25rem;
  font-size: 1rem;
  opacity: 0;
  transition:
    transform 0.3s cubic-bezier(.4,0,.2,1),
    opacity 0.2s,
    color 0.2s,
    font-size 0.2s;
}

.input:focus + .floating-label,
.input:not(:placeholder-shown) + .floating-label {
  transform: translateY(-50%) translateX(0);
  opacity: 1;
  color: #4f46e5;
  font-size: 0.95rem;
  background: #f8fafc;
}

  background: #f8fafc;
  width: 100%;
  transition: border-color 0.2s;
}

.input:focus {
  border-color: #4f46e5;
  outline: none;
}

.floating-label {
  position: absolute;
  left: 0.75rem;
  top: 50%;
  transform: translateY(-50%) translateX(-120%);
  color: #6b7280;
  pointer-events: none;
  background: transparent;
  padding: 0 0.25rem;
  font-size: 1rem;
  opacity: 0;
  transition:
    transform 0.3s cubic-bezier(.4,0,.2,1),
    opacity 0.2s,
    color 0.2s,
    font-size 0.2s;
}

.input:focus + .floating-label,
.input:not(:placeholder-shown) + .floating-label {
  transform: translateY(-50%) translateX(0);
  opacity: 1;
  color: #4f46e5;
  font-size: 0.95rem;
  background: #f8fafc;
}

.btn {
  background-color: #4f46e5;
  color: white;
  padding: 0.6rem;
  border-radius: 6px;
  font-weight: bold;
  transition: background 0.2s;
  transition: background 0.2s;
}
.btn:disabled {
  background-color: #a5b4fc;
}
</style>
