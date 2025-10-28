<template>
    <div class="gallery-masonry-container max-w-7xl mx-auto pt-2 py-12 px-4 sm:px-6 lg:px-8">
        <h2 class="text-3xl font-bold text-gray-800 mb-8 text-center">Cat Photo Gallery</h2>
        
        <!-- Loading state -->
        <div v-if="loading" class="text-center py-12">
            <div class="flex flex-col items-center">
              <div class="animate-spin rounded-full h-20 w-20 border-b-2 border-orange-500 mb-4"></div>
              <h3 class="text-lg font-semibold text-gray-700 mb-2">🐱 Loading the gallery...</h3>
              <p class="text-sm text-gray-500">Hang tight! We're fetching all the adorable cat photos for you.</p>
            </div>
        </div>
        
        <!-- Error state -->
        <div v-else-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
            <p class="font-bold">Error:</p>
            <p>{{ error }}</p>
            <button @click="fetchImages" class="mt-2 bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600">Retry</button>
        </div>
        
        <!-- Empty state -->
        <div v-else-if="images.length === 0" class="text-center py-12">
            <svg class="h-24 w-24 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
            </svg>
            <p class="text-gray-600 text-lg">No photos uploaded yet</p>
        </div>
        
        <!-- Gallery grid with virtual scrolling -->
        <div v-else>
            <div ref="galleryContainer" class="columns-3 md:columns-3 lg:columns-4 xl:columns-5 gap-2 space-y-2">
                <div
                    v-for="(image, index) in visibleImages"
                    :key="image.id"
                    class="break-inside-avoid mb-2 relative cursor-pointer overflow-hidden group rounded-lg"
                    @click="openModal(image)"
                    ref="imageElements"
                    :data-image-id="image.id"
                >
                    <!-- Image placeholder while loading -->
                    <div v-if="!loadedImages[image.id]" class="w-full bg-gray-200 animate-pulse rounded-lg" :style="{ aspectRatio: getRandomAspectRatio() }"></div>
                    
                    <!-- Actual image with lazy loading -->
                    <img
                        :data-src="image.image_url"
                        :src="loadedImages[image.id] ? image.image_url : undefined"
                        :alt="image.filename"
                        class="w-full object-cover group-hover:brightness-110 transition-all duration-300 rounded-lg"
                        :class="{ 'opacity-0': !loadedImages[image.id], 'opacity-100': loadedImages[image.id] }"
                        @error="handleImageError"
                    />
                    <div class="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-lg"></div>
                </div>
            </div>
            
            <!-- Load more indicator -->
            <div v-if="hasMoreImages && !loadingMore" ref="loadMoreTrigger" class="text-center py-4">
                <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
            </div>
        </div>
        
        <!-- Modal -->
        <div v-if="selectedImage" class="fixed inset-0 bg-black bg-opacity-80 flex items-center justify-center z-50" @click="closeModal">
            <div class="max-w-4xl w-full p-4" @click.stop>
                <div class="relative">
                    <!-- Modal image placeholder -->
                    <div v-if="!modalImageLoaded" class="w-full h-[70vh] bg-gray-800 animate-pulse rounded-lg"></div>
                    
                    <!-- Modal image -->
                    <img
                        :src="selectedImage.image_url"
                        :alt="selectedImage.filename"
                        class="w-full max-h-[90vh] object-contain mx-auto rounded-lg"
                        :class="{ 'opacity-0': !modalImageLoaded, 'opacity-100': modalImageLoaded }"
                        @load="modalImageLoaded = true"
                        @error="handleModalImageError"
                    />
                    <button @click="closeModal" class="absolute top-2 right-2 bg-black bg-opacity-60 text-white p-2 rounded-full hover:bg-opacity-80 cursor-pointer">
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
import { ref, onMounted, onUnmounted, nextTick, watch, onErrorCaptured } from 'vue';
import { createApiUrl } from '../config/api';
import { useImageLazyLoad, preloadImages } from '../utils/lazyLoad';
import { isDev } from '../utils/env';

// Handle browser extension errors
onErrorCaptured((err) => {
  if (
    err.message &&
    (err.message.includes('message channel closed') ||
     err.message.includes('asynchronous response by returning true, but the message channel closed') ||
     err.message.includes('A listener indicated an asynchronous response by returning true, but the message channel closed before a response was received'))
  ) {
    if (isDev()) {
      console.warn('⚠️ Browser extension error caught in Gallery component:', err.message);
    }
    return false;
  }
  return true;
});

const images = ref([]);
const loading = ref(true);
const loadingMore = ref(false);
const error = ref('');
const selectedImage = ref(null);
const loadedImages = ref({});
const modalImageLoaded = ref(false);
const imageElements = ref([]);
const galleryContainer = ref(null);
const loadMoreTrigger = ref(null);

// Pagination and virtual scrolling
const currentPage = ref(1);
const imagesPerPage = 20;
const visibleImages = ref([]);
const hasMoreImages = ref(false);

// Lazy load observer
let lazyLoadObserver = null;
let loadMoreObserver = null;

onMounted(() => {
  fetchImages();
});

onUnmounted(() => {
  // Clean up observers
  if (lazyLoadObserver) {
    lazyLoadObserver.disconnect();
  }
  if (loadMoreObserver) {
    loadMoreObserver.disconnect();
  }
});

// Watch for changes in visibleImages to set up lazy loading
watch(visibleImages, async () => {
  await nextTick();
  setupLazyLoading();
});

// Watch for changes in imageElements
watch(imageElements, async () => {
  await nextTick();
  setupLazyLoading();
});

async function fetchImages() {
  loading.value = true;
  error.value = '';
  currentPage.value = 1;
  
  try {
    const apiUrl = createApiUrl('/api/gallery');
    
    const response = await fetch(apiUrl, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      try {
        const errorData = JSON.parse(errorText);
        throw new Error(errorData.detail || errorData.message || `Failed to fetch images (${response.status})`);
      } catch (parseError) {
        throw new Error(`Server returned non-JSON response (${response.status}): ${errorText.substring(0, 200)}`);
      }
    }
    
    const contentType = response.headers.get('content-type');
    
    
    if (!contentType || !contentType.includes('application/json')) {
      const responseText = await response.text();
      throw new Error(`Invalid response format: not JSON (got ${contentType})`);
    }
    
    
    const data = await response.json();
    
    if (data.error) {
      throw new Error(data.message || data.detail || 'Server error occurred');
    }
    
    if (!data || !Array.isArray(data.images)) {
      throw new Error('Malformed data from server');
    }
    
    
    images.value = data.images;
    updateVisibleImages();
    
  } catch (err) {
    error.value = err.message || 'Failed to load images';
    images.value = [];
  } finally {
    loading.value = false;
  }
}

function updateVisibleImages() {
  const startIndex = 0;
  const endIndex = currentPage.value * imagesPerPage;
  visibleImages.value = images.value.slice(startIndex, endIndex);
  hasMoreImages.value = endIndex < images.value.length;
  
  // Initialize loadedImages for new visible images
  visibleImages.value.forEach(image => {
    if (!(image.id in loadedImages.value)) {
      loadedImages.value[image.id] = false;
    }
  });
}

function setupLazyLoading() {
  // Clean up previous observer
  if (lazyLoadObserver) {
    lazyLoadObserver.disconnect();
  }
  
  // Create new observer
  lazyLoadObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target;
        const src = img.getAttribute('data-src');
        
        if (src && !img.src) {
          // Get image ID from the parent element
          const imageContainer = img.closest('[data-image-id]');
          if (imageContainer) {
            const imageId = imageContainer.getAttribute('data-image-id');
            
            // Set the image source
            img.src = src;
            
            // Handle image load
            img.onload = () => {
              loadedImages.value[imageId] = true;
            };
            
            // Handle image error
            img.onerror = () => {
              img.src = 'https://placehold.co/400x400?text=No+Image';
              loadedImages.value[imageId] = true; // Still mark as loaded to show the error placeholder
            };
            
            // Stop observing this image
            lazyLoadObserver.unobserve(img);
          }
        }
      }
    });
  }, {
    rootMargin: '100px',
    threshold: 0.1
  });
  
  // Observe all images
  imageElements.value.forEach(element => {
    const img = element.querySelector('img');
    if (img) {
      lazyLoadObserver.observe(img);
    }
  });
  
  // Set up load more observer
  setupLoadMoreObserver();
}

function setupLoadMoreObserver() {
  // Clean up previous observer
  if (loadMoreObserver) {
    loadMoreObserver.disconnect();
  }
  
  if (!loadMoreTrigger.value || !hasMoreImages.value) return;
  
  // Create new observer for load more trigger
  loadMoreObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting && hasMoreImages.value && !loadingMore.value) {
        loadMoreImages();
      }
    });
  }, {
    rootMargin: '200px',
    threshold: 0.1
  });
  
  loadMoreObserver.observe(loadMoreTrigger.value);
}

function loadMoreImages() {
  if (loadingMore.value || !hasMoreImages.value) return;
  
  loadingMore.value = true;
  
  // Simulate loading delay for better UX
  setTimeout(() => {
    currentPage.value++;
    updateVisibleImages();
    loadingMore.value = false;
  }, 300);
}

function openModal(image) {
  selectedImage.value = image;
  modalImageLoaded.value = false;
  
  // Preload the image if not already loaded
  if (image.image_url) {
    preloadImages([image.image_url]).then(() => {
      modalImageLoaded.value = true;
    }).catch(() => {
      modalImageLoaded.value = true; // Still show the modal even if preloading fails
    });
  }
}

function closeModal() {
  selectedImage.value = null;
  modalImageLoaded.value = false;
}

function handleImageError(event) {
  event.target.src = 'https://placehold.co/400x400?text=No+Image';
}

function handleModalImageError(event) {
  event.target.src = 'https://placehold.co/800x600?text=Image+Error';
}

// Function to get random aspect ratio for placeholder images
function getRandomAspectRatio() {
  const aspectRatios = [
    '1/1',      // Square
    '2/3',      // Portrait
    '3/2',      // Landscape
    '4/5',      // Portrait
    '5/4',      // Landscape
    '3/4',      // Portrait
    '4/3',      // Landscape
  ];
  
  return aspectRatios[Math.floor(Math.random() * aspectRatios.length)];
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

<style scoped>
/* Masonry columns layout */
.columns-3 {
  column-count: 3;
}

.columns-4 {
  column-count: 4;
}

.columns-5 {
  column-count: 5;
}

@media (min-width: 768px) {
  .md\:columns-3 {
    column-count: 3;
  }
}

@media (min-width: 1024px) {
  .lg\:columns-4 {
    column-count: 4;
  }
}

@media (min-width: 1280px) {
  .xl\:columns-5 {
    column-count: 5;
  }
}

/* Column gap */
.gap-2 {
  column-gap: 0.5rem;
}

.space-y-2 > * + * {
  margin-top: 0.5rem;
}

/* Prevent column breaks */
.break-inside-avoid {
  break-inside: avoid;
  page-break-inside: avoid;
}

/* Smooth hover effects */
.group:hover img {
  transform: scale(1.05);
}

/* Image loading transitions */
img {
  transition: opacity 0.3s ease-in-out;
}

/* Loading placeholder animation */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* Modal image transition */
.modal-image-transition {
  transition: opacity 0.3s ease-in-out;
}
</style>

