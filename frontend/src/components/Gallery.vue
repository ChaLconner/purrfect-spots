<template>
    <div class="gallery-masonry-container max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
        <h2 class="text-3xl font-bold text-gray-800 mb-8 text-center">Cat Photo Gallery</h2>
        <div v-if="loading" class="text-center py-12">
            <div class="flex flex-col items-center">
                <div class="animate-spin rounded-full h-20 w-20 border-b-2 border-orange-500 mb-4"></div>
                <h3 class="text-lg font-semibold text-gray-700 mb-2">🐱 กำลังโหลดแกลเลอรี่...</h3>
                <p class="text-sm text-gray-500">เรากำลังรวบรวมรูปแมวน่ารักทั้งหมดให้คุณ</p>
            </div>
        </div>
        <div v-else-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
            <p class="font-bold">Error:</p>
            <p>{{ error }}</p>
            <button @click="fetchImages" class="mt-2 bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600">Retry</button>
        </div>
        <div v-else-if="images.length === 0" class="text-center py-12">
            <svg class="h-24 w-24 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
            </svg>
            <p class="text-gray-600 text-lg">No photos uploaded yet</p>
        </div>
        <div v-else class="gallery-masonry grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            <div v-for="image in images" :key="image.id" class="gallery-item group" @click="openModal(image)">
                <img
                    :src="image.url"
                    :alt="image.filename"
                    class="gallery-img w-full h-64 object-cover rounded-lg shadow-md group-hover:scale-105 transition-transform duration-200 ease-in-out cursor-pointer"
                    loading="lazy"
                    @error="handleImageError"
                />
            </div>
        </div>
        <!-- Modal -->
        <div v-if="selectedImage" class="fixed inset-0 bg-black bg-opacity-80 flex items-center justify-center z-50" @click="closeModal">
            <div class="max-w-4xl w-full p-4" @click.stop>
                <div class="relative">
                    <img :src="selectedImage.url" :alt="selectedImage.filename" class="w-full max-h-[90vh] object-contain mx-auto rounded-lg" />
                    <button @click="closeModal" class="absolute top-2 right-2 bg-black bg-opacity-60 text-white p-2 rounded-full hover:bg-opacity-80">
                        <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
const images = ref([]);
const loading = ref(true);
const error = ref('');
const selectedImage = ref(null);

onMounted(() => {
  fetchImages();
});

async function fetchImages() {
  loading.value = true;
  error.value = '';
  try {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/gallery`);
    if (!response.ok) throw new Error(`Failed to fetch images (${response.status})`);
    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
      throw new Error('Invalid response format: not JSON');
    }
    const data = await response.json();
    if (!data || !Array.isArray(data.images)) {
      throw new Error('Malformed data from server');
    }
    images.value = data.images;
  } catch (err) {
    error.value = err.message || 'Failed to load images';
    images.value = [];
  } finally {
    loading.value = false;
  }
}

function openModal(image) {
  selectedImage.value = image;
}
function closeModal() {
  selectedImage.value = null;
}
function handleImageError(event) {
  event.target.src = 'https://placehold.co/400x300?text=No+Image';
}
function formatDate(dateString) {
  if (!dateString) return '';
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
    });
  } catch (error) {
    return 'Invalid date';
  }
}
function formatFileSize(bytes) {
  if (!bytes) return '';
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}
</script>