<template>
  <div class="max-w-md mx-auto mt-10 p-6 bg-white shadow rounded-xl">
    <h2 class="text-2xl font-semibold mb-4 text-center">
      {{ isLogin ? 'เข้าสู่ระบบ' : 'สมัครสมาชิก' }}
    </h2>

    <form @submit.prevent="handleSubmit" class="space-y-4">
      <div>
        <label class="block mb-1 text-sm">Email</label>
        <input v-model="form.email" type="email" required class="w-full input" />
      </div>

      <div>
        <label class="block mb-1 text-sm">Password</label>
        <input v-model="form.password" type="password" required class="w-full input" />
      </div>

      <div v-if="!isLogin">
        <label class="block mb-1 text-sm">ชื่อ-นามสกุล</label>
        <input v-model="form.name" type="text" required class="w-full input" placeholder="กรุณากรอกชื่อ-นามสกุล" />
      </div>

      <button :disabled="isLoading" class="btn w-full">
        {{ isLoading ? 'กำลังโหลด...' : isLogin ? 'เข้าสู่ระบบ' : 'สมัครสมาชิก' }}
      </button>
    </form>

    <!-- OAuth Section -->
    <div class="mt-6">
      <div class="relative">
        <div class="absolute inset-0 flex items-center">
          <div class="w-full border-t border-gray-300"></div>
        </div>
        <div class="relative flex justify-center text-sm">
          <span class="px-2 bg-white text-gray-500">หรือ</span>
        </div>
      </div>
      
      <div class="mt-6">
        <button
          @click="handleGoogleLogin"
          :disabled="isLoading"
          type="button"
          class="w-full flex justify-center items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
        >
          <svg class="w-5 h-5 mr-2" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          เข้าสู่ระบบด้วย Google
        </button>
      </div>
    </div>

    <div v-if="errorMessage" class="mt-4 text-sm text-red-600">
      {{ errorMessage }}
    </div>

    <div class="mt-6 text-sm text-center">
      <span>
        {{ isLogin ? 'ยังไม่มีบัญชี?' : 'มีบัญชีแล้ว?' }}
        <router-link 
          :to="isLogin ? '/register' : '/login'" 
          class="text-blue-600 hover:underline"
        >
          {{ isLogin ? 'สมัครสมาชิก' : 'เข้าสู่ระบบ' }}
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
    // User is fully authenticated, redirect to intended destination
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
      throw new Error('กรุณากรอกอีเมล');
    }
    
    if (!form.password.trim()) {
      throw new Error('กรุณากรอกรหัสผ่าน');
    }
    
    if (!isLogin.value) {
      if (!form.name.trim()) {
        throw new Error('กรุณากรอกชื่อ-นามสกุล');
      }
      
      if (form.password.length < 6) {
        throw new Error('รหัสผ่านต้องมีความยาวอย่างน้อย 6 ตัวอักษร');
      }
    }

    let data;
    if (isLogin.value) {
      data = await AuthService.login(form.email, form.password);
    } else {
      data = await AuthService.signup(form.email, form.password, form.name);
    }

    // Use auth store to manage authentication state
    setAuth(data);

    // Get redirect path from session storage
    const redirectPath = sessionStorage.getItem('redirectAfterAuth') || '/';
    sessionStorage.removeItem('redirectAfterAuth');
    
    // Redirect to intended destination
    router.push(redirectPath);
  } catch (err: any) {
    errorMessage.value = err.message || 'เกิดข้อผิดพลาด';
  } finally {
    isLoading.value = false;
  }
};

const handleGoogleLogin = async () => {
  isLoading.value = true;
  errorMessage.value = '';

  try {
    // Use manual OAuth with PKCE for better security
    const googleClientId = '40710057825-09pahjbe71ncf7adq9c8892r2mivm9b3.apps.googleusercontent.com';
    const redirectUri = `${window.location.origin}/auth/callback`;
    
    // Generate PKCE parameters
    const codeVerifier = generateCodeVerifier();
    const codeChallenge = await generateCodeChallenge(codeVerifier);
    
    // Store code verifier in session storage
    sessionStorage.setItem('google_code_verifier', codeVerifier);
    
    // Build OAuth URL
    const oauthUrl = new URL('https://accounts.google.com/o/oauth2/v2/auth');
    oauthUrl.searchParams.append('client_id', googleClientId);
    oauthUrl.searchParams.append('redirect_uri', redirectUri);
    oauthUrl.searchParams.append('response_type', 'code');
    oauthUrl.searchParams.append('scope', 'openid email profile');
    oauthUrl.searchParams.append('code_challenge', codeChallenge);
    oauthUrl.searchParams.append('code_challenge_method', 'S256');
    oauthUrl.searchParams.append('access_type', 'offline');
    oauthUrl.searchParams.append('prompt', 'consent');
    
    // Redirect to Google OAuth
    window.location.href = oauthUrl.toString();
  } catch (err: any) {
    console.error('Google OAuth Error:', err);
    errorMessage.value = err.message || 'เกิดข้อผิดพลาดในการเข้าสู่ระบบด้วย Google';
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
.input {
  border: 1px solid #ccc;
  padding: 0.5rem;
  border-radius: 6px;
}
.btn {
  background-color: #4f46e5;
  color: white;
  padding: 0.6rem;
  border-radius: 6px;
  font-weight: bold;
}
.btn:disabled {
  background-color: #a5b4fc;
}
</style>
