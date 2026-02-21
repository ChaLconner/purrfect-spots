<script setup lang="ts">
import { ref, reactive } from 'vue';
import PasswordStrengthMeter from '@/components/ui/PasswordStrengthMeter.vue';

interface Props {
  isLogin: boolean;
  isLoading: boolean;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  submit: (form: { email: string; password: string; name: string }) => void;
}>();

const showPassword = ref(false);

const form = reactive({
  email: '',
  password: '',
  name: '',
});

const handleSubmit = () => {
  emit('submit', { ...form });
};
</script>

<template>
  <form class="flex flex-col gap-5" novalidate @submit.prevent="handleSubmit">
    <!-- Email Field -->
    <div class="flex flex-col gap-2">
      <label
        for="email"
        class="flex items-center gap-2 font-['Nunito'] text-[0.9rem] font-semibold text-[#5a4632]"
      >
        Email
      </label>
      <div class="relative">
        <input
          id="email"
          v-model="form.email"
          type="email"
          required
          placeholder="your@email.com"
          class="w-full py-4 px-5 font-sans text-base text-[#5a4632] bg-white/70 border-2 border-[rgba(127,183,164,0.2)] rounded-2xl outline-none transition-all duration-300 placeholder:text-[#6b6b6b] focus:bg-white/95 focus:border-[#7fb7a4] focus:shadow-[0_0_0_4px_rgba(127,183,164,0.15)] hover:not:focus:border-[rgba(127,183,164,0.4)]"
        />
      </div>
    </div>

    <!-- Password Field -->
    <div class="flex flex-col gap-2">
      <label
        for="password"
        class="flex items-center gap-2 font-['Nunito'] text-[0.9rem] font-semibold text-[#5a4632]"
      >
        Password
      </label>
      <div class="relative">
        <input
          id="password"
          v-model="form.password"
          :type="showPassword ? 'text' : 'password'"
          required
          placeholder="••••••••"
          class="w-full py-4 px-5 pr-12 font-sans text-base text-[#5a4632] bg-white/70 border-2 border-[rgba(127,183,164,0.2)] rounded-2xl outline-none transition-all duration-300 placeholder:text-[#6b6b6b] focus:bg-white/95 focus:border-[#7fb7a4] focus:shadow-[0_0_0_4px_rgba(127,183,164,0.15)] hover:not:focus:border-[rgba(127,183,164,0.4)]"
        />
        <button
          type="button"
          class="absolute right-4 top-1/2 -translate-y-1/2 bg-transparent border-none cursor-pointer p-0 flex items-center justify-center text-[#a0a0a0] transition-colors duration-300 hover:text-[#7fb7a4]"
          :aria-label="showPassword ? 'Hide password' : 'Show password'"
          @click="showPassword = !showPassword"
        >
          <!-- Eye Off Icon (Show Password) -->
          <svg
            v-if="!showPassword"
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
          <!-- Eye Icon (Hide Password) -->
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

      <!-- Password Strength Meter (Register only) -->
      <transition
        enter-active-class="transition-all duration-300 ease-out"
        leave-active-class="transition-all duration-300 ease-out"
        enter-from-class="opacity-0 -translate-y-1"
        leave-to-class="opacity-0 -translate-y-1"
      >
        <PasswordStrengthMeter v-if="!props.isLogin" :password="form.password" />
      </transition>

      <p v-if="!props.isLogin" class="font-sans text-[0.8rem] text-[#7d7d7d] mt-1 ml-2">
        Must be at least 8 characters
      </p>
      <div v-if="props.isLogin" class="text-right mt-1">
        <router-link
          to="/forgot-password"
          class="font-sans text-[0.85rem] text-[#7fb7a4] no-underline font-medium hover:underline"
        >
          Forgot Password?
        </router-link>
      </div>
    </div>

    <!-- Full Name Field (Sign Up only) -->
    <div v-if="!props.isLogin" class="flex flex-col gap-2">
      <label
        for="name"
        class="flex items-center gap-2 font-['Nunito'] text-[0.9rem] font-semibold text-[#5a4632]"
      >
        Full Name
      </label>
      <div class="relative">
        <input
          id="name"
          v-model="form.name"
          type="text"
          required
          placeholder="Your name"
          class="w-full py-4 px-5 font-sans text-base text-[#5a4632] bg-white/70 border-2 border-[rgba(127,183,164,0.2)] rounded-2xl outline-none transition-all duration-300 placeholder:text-[#6b6b6b] focus:bg-white/95 focus:border-[#7fb7a4] focus:shadow-[0_0_0_4px_rgba(127,183,164,0.15)] hover:not:focus:border-[rgba(127,183,164,0.4)]"
        />
      </div>
    </div>

    <button
      :disabled="isLoading"
      class="flex items-center justify-center gap-3 w-full py-4 px-8 mt-2 font-['Nunito'] text-[1.1rem] font-bold text-white bg-gradient-to-br from-[#7fb7a4] to-[#6da491] border-none rounded-2xl cursor-pointer transition-all duration-300 shadow-[0_4px_15px_rgba(127,183,164,0.4)] hover:not:disabled:-translate-y-0.5 hover:not:disabled:shadow-[0_8px_25px_rgba(127,183,164,0.5)] active:not:disabled:translate-y-0 disabled:opacity-70 disabled:cursor-not-allowed"
    >
      <span
        v-if="isLoading"
        class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-[spin_0.8s_linear_infinite]"
      ></span>
      {{ isLoading ? 'Loading...' : props.isLogin ? 'Sign In' : 'Create Account' }}
    </button>
  </form>
</template>
