<script setup lang="ts">
import logo from "../components/icon/logo.vue";
import { ref, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { authStore, initializeAuth, clearAuth } from "../store/auth";
import { AuthService } from "../services/authService";

const menuOpen = ref(false);
const showUserMenu = ref(false);
const router = useRouter();

function goHome() {
    router.push('/');
}

const logout = async () => {
    try {
        await AuthService.logout();
        clearAuth();
        showUserMenu.value = false;
        router.push('/'); // Redirect to home after logout
        // You can show a logout success toast here
    } catch (error) {
        console.error('Logout error:', error);
    }
};

// Close user menu when clicking outside
const handleClickOutside = (event: Event) => {
    const target = event.target as HTMLElement;
    if (showUserMenu.value && target && !target.closest('.user-menu-container')) {
        showUserMenu.value = false;
    }
};

// Initialize auth state on component mount
onMounted(() => {
    initializeAuth();
    document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
    document.removeEventListener('click', handleClickOutside);
});
</script>
<template>
    <nav class="flex flex-col md:flex-row items-center justify-between px-6 py-4 bg-white shadow-md">
        <div class="flex items-center mb-2 md:mb-0 space-x-2 cursor-pointer" @click="goHome">
            <logo class="w-8 h-8" />
            <div class="text-lg font-bold whitespace-nowrap">Purrfect Spots</div>
        </div>
        <!-- Hamburger button (mobile only) -->
        <button
            class="md:hidden p-2 rounded focus:outline-none"
            @click="menuOpen = !menuOpen"
            aria-label="Toggle menu"
        >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M4 6h16M4 12h16M4 18h16" />
            </svg>
        </button>
        <!-- Menu -->
        <div
            class="flex-col md:flex-row items-center gap-4 md:gap-6 md:flex"
            :class="menuOpen ? 'flex' : 'hidden'"
        >
            <router-link to="/" class="hover:underline"> Map </router-link>
            <router-link to="/upload" class="hover:underline"> Upload </router-link>
            <router-link to="/gallery" class="hover:underline"> Gallery </router-link>
            
            <!-- Authentication Section -->
            <div v-if="!authStore.isAuthenticated" class="flex items-center gap-2">
                <router-link 
                    to="/login"
                    class="px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all duration-200 font-medium"
                >
                    เข้าสู่ระบบ
                </router-link>
                <router-link 
                    to="/signin"
                    class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-all duration-200 font-medium"
                >
                    สมัครสมาชิก
                </router-link>
            </div>
            
            <!-- User Menu (when authenticated) -->
            <div v-else class="relative flex items-center gap-4">
                <!-- Notification Icon -->
                <button class="relative focus:outline-none bg-[#F0F5F0] rounded-md p-2">
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        class="h-6 w-6 text-gray-600"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                    >
                        <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                        />
                    </svg>
                    <span
                        class="absolute translate-x-1/2 -translate-y-6 inline-block w-2 h-2 bg-red-500 rounded-full"
                    ></span>
                </button>
                
                <!-- User Avatar & Dropdown -->
                <div class="relative user-menu-container">
                    <button
                        @click="showUserMenu = !showUserMenu"
                        class="flex items-center gap-2 focus:outline-none"
                    >
                        <img
                            :src="authStore.user?.picture || 'https://randomuser.me/api/portraits/men/32.jpg'"
                            :alt="authStore.user?.name || 'User Avatar'"
                            class="w-8 h-8 rounded-full border border-gray-300"
                        />
                        <span class="hidden md:block text-sm font-medium text-gray-700">
                            {{ authStore.user?.name }}
                        </span>
                        <svg class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                        </svg>
                    </button>
                    
                    <!-- Dropdown Menu -->
                    <div
                        v-if="showUserMenu"
                        @click.stop
                        class="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50"
                    >
                        <div class="px-4 py-2 border-b border-gray-100">
                            <p class="text-sm font-medium text-gray-900">{{ authStore.user?.name }}</p>
                            <p class="text-xs text-gray-500">{{ authStore.user?.email }}</p>
                        </div>
                        <router-link
                            to="/profile"
                            @click="showUserMenu = false"
                            class="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                        >
                            โปรไฟล์
                        </router-link>
                        <button
                            @click="logout"
                            class="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
                        >
                            ออกจากระบบ
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </nav>
</template>
