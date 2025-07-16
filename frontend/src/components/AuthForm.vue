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
        <label class="block mb-1 text-sm">Name</label>
        <input v-model="form.name" type="text" required class="w-full input" />
      </div>

      <button :disabled="isLoading" class="btn w-full">
        {{ isLoading ? 'กำลังโหลด...' : isLogin ? 'เข้าสู่ระบบ' : 'สมัครสมาชิก' }}
      </button>
    </form>

    <div v-if="errorMessage" class="mt-4 text-sm text-red-600">
      {{ errorMessage }}
    </div>

    <div class="mt-6 text-sm text-center">
      <span>
        {{ isLogin ? 'ยังไม่มีบัญชี?' : 'มีบัญชีแล้ว?' }}
        <a href="#" @click.prevent="toggleMode" class="text-blue-600 hover:underline">
          {{ isLogin ? 'สมัครสมาชิก' : 'เข้าสู่ระบบ' }}
        </a>
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { useRouter } from 'vue-router';
import { setAuth, isUserReady } from '../store/auth';

// Configure axios base URL
const API_BASE_URL = 'http://localhost:8000';
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

const isLogin = ref(true);
const isLoading = ref(false);
const errorMessage = ref('');
const router = useRouter();

const form = ref({
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

const toggleMode = () => {
  isLogin.value = !isLogin.value;
  errorMessage.value = '';
};

const handleSubmit = async () => {
  isLoading.value = true;
  errorMessage.value = '';

  try {
    const url = isLogin.value ? '/auth/login' : '/auth/signup';
    const { data } = await api.post(url, {
      email: form.value.email,
      password: form.value.password,
      ...(isLogin.value ? {} : { name: form.value.name }),
    });

    // Use auth store to manage authentication state
    setAuth(data);

    // Get redirect path from session storage
    const redirectPath = sessionStorage.getItem('redirectAfterAuth') || '/';
    sessionStorage.removeItem('redirectAfterAuth');
    
    // Redirect to intended destination
    router.push(redirectPath);
  } catch (err: any) {
    errorMessage.value = err.response?.data?.detail || 'เกิดข้อผิดพลาด';
  } finally {
    isLoading.value = false;
  }
};
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
