<script setup lang="ts">
import logo from "../components/icon/logo.vue";
import { ref } from "vue";
import { useRouter } from "vue-router";

const menuOpen = ref(false);
const router = useRouter();
function goHome() {
    router.push('/');
}
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
            <!-- Avatar -->
            <img
                src="https://randomuser.me/api/portraits/men/32.jpg"
                alt="User Avatar"
                class="w-8 h-8 rounded-full border border-gray-300"
            />
        </div>
    </nav>
</template>
