<template>
    <div class="gallery-container">
        <h2 class="text-3xl font-bold text-gray-800 mb-8 text-center">Cat Photo Gallery</h2>
        
        <!-- Loading State -->
        <div v-if="loading" class="text-center">
            <div class="animate-spin rounded-full h-16 w-16 border-4 border-emerald-500 border-t-transparent mx-auto"></div>
            <p class="mt-4 text-gray-600">Loading photos...</p>
        </div>
        
        <!-- Error State -->
        <div v-else-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
            <p class="font-bold">Error:</p>
            <p>{{ error }}</p>
            <button @click="fetchImages" class="mt-2 bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600">
                Retry
            </button>
        </div>
        
        <!-- Empty State -->
        <div v-else-if="images.length === 0" class="text-center py-12">
            <svg class="h-24 w-24 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
            </svg>
            <p class="text-gray-600 text-lg">No photos uploaded yet</p>
            <router-link to="/upload" class="mt-4 inline-block bg-emerald-500 text-white px-6 py-2 rounded-lg hover:bg-emerald-600">
                Upload Your First Photo
            </router-link>
        </div>
        
        <!-- Gallery Grid -->
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div
                v-for="image in images"
                :key="image.filename"
                class="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow"
            >
                <!-- Image -->
                <div class="relative">
                    <img
                        :src="image.url"
                        :alt="image.metadata.description || 'Cat photo'"
                        class="w-full h-64 object-cover cursor-pointer"
                        @click="openModal(image)"
                        @error="handleImageError"
                    />
                    <div class="absolute top-2 right-2">
                        <button
                            @click="deleteImage(image.filename)"
                            class="bg-red-500 text-white p-2 rounded-full hover:bg-red-600 transition-colors"
                            title="Delete photo"
                        >
                            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                            </svg>
                        </button>
                    </div>
                </div>
                
                <!-- Image Info -->
                <div class="p-4">
                    <h3 class="font-semibold text-gray-800 mb-2">
                        {{ image.metadata.location || 'Unknown Location' }}
                    </h3>
                    <p class="text-gray-600 text-sm mb-3">
                        {{ image.metadata.description || 'No description' }}
                    </p>
                    <div class="flex justify-between items-center text-xs text-gray-500">
                        <span>{{ formatDate(image.last_modified) }}</span>
                        <span>{{ formatFileSize(image.size) }}</span>
                    </div>
                    <div v-if="image.metadata.latitude && image.metadata.longitude" class="mt-2 text-xs text-gray-500">
                        📍 {{ parseFloat(image.metadata.latitude).toFixed(4) }}, {{ parseFloat(image.metadata.longitude).toFixed(4) }}
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Modal -->
        <div v-if="selectedImage" class="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50" @click="closeModal">
            <div class="max-w-4xl max-h-full p-4" @click.stop>
                <div class="bg-white rounded-lg overflow-hidden">
                    <div class="relative">
                        <img
                            :src="selectedImage.url"
                            :alt="selectedImage.metadata.description || 'Cat photo'"
                            class="w-full max-h-96 object-contain"
                        />
                        <button
                            @click="closeModal"
                            class="absolute top-2 right-2 bg-black bg-opacity-50 text-white p-2 rounded-full hover:bg-opacity-75"
                        >
                            <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                            </svg>
                        </button>
                    </div>
                    <div class="p-6">
                        <h3 class="text-xl font-bold text-gray-800 mb-2">
                            {{ selectedImage.metadata.location || 'Unknown Location' }}
                        </h3>
                        <p class="text-gray-600 mb-4">
                            {{ selectedImage.metadata.description || 'No description' }}
                        </p>
                        <div class="grid grid-cols-2 gap-4 text-sm text-gray-600">
                            <div>
                                <strong>Uploaded:</strong> {{ formatDate(selectedImage.last_modified) }}
                            </div>
                            <div>
                                <strong>Size:</strong> {{ formatFileSize(selectedImage.size) }}
                            </div>
                            <div v-if="selectedImage.metadata.latitude && selectedImage.metadata.longitude" class="col-span-2">
                                <strong>Coordinates:</strong> {{ parseFloat(selectedImage.metadata.latitude).toFixed(6) }}, {{ parseFloat(selectedImage.metadata.longitude).toFixed(6) }}
                            </div>
                        </div>
                    </div>
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

// Backend API URL
const API_URL = 'http://localhost:5000';

onMounted(() => {
    fetchImages();
});

async function fetchImages() {
    loading.value = true;
    error.value = '';
    
    try {
        const response = await fetch(`${API_URL}/images`);
        
        if (!response.ok) {
            throw new Error('Failed to fetch images');
        }
        
        const data = await response.json();
        images.value = data.images || [];
        
    } catch (err) {
        console.error('Error fetching images:', err);
        error.value = err.message || 'Failed to load images';
    } finally {
        loading.value = false;
    }
}

async function deleteImage(filename) {
    if (!confirm('Are you sure you want to delete this photo?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/delete/${filename}`, {
            method: 'DELETE',
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete image');
        }
        
        // Remove the image from the local array
        images.value = images.value.filter(img => img.filename !== filename);
        
        // Close modal if the deleted image was selected
        if (selectedImage.value && selectedImage.value.filename === filename) {
            selectedImage.value = null;
        }
        
    } catch (err) {
        console.error('Error deleting image:', err);
        alert('Failed to delete image: ' + err.message);
    }
}

function openModal(image) {
    selectedImage.value = image;
}

function closeModal() {
    selectedImage.value = null;
}

function handleImageError(event) {
    console.error('Error loading image:', event.target.src);
    // You could set a placeholder image here
    // event.target.src = '/placeholder-image.jpg';
}

function formatDate(dateString) {
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (error) {
        return 'Invalid date';
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}
</script>

<style scoped>
.gallery-container {
    max-width: 1200px;
    margin: 2rem auto;
    padding: 2rem;
}

/* Modal backdrop */
.modal-backdrop {
    backdrop-filter: blur(4px);
}

/* Smooth transitions */
.transition-shadow {
    transition: box-shadow 0.3s ease;
}

.transition-colors {
    transition: all 0.3s ease;
}

/* Image hover effects */
.gallery-container img:hover {
    transform: scale(1.02);
    transition: transform 0.2s ease;
}

/* Custom scrollbar for modal */
.modal-content::-webkit-scrollbar {
    width: 8px;
}

.modal-content::-webkit-scrollbar-track {
    background: #f1f1f1;
}

.modal-content::-webkit-scrollbar-thumb {
    background: #888;
    border-radius: 4px;
}

.modal-content::-webkit-scrollbar-thumb:hover {
    background: #555;
}
</style>
