<template>
    <div class="max-w-2xl mx-auto mt-8 p-8 bg-white rounded-xl shadow-md">
        <h2 class="text-center mb-8 text-gray-700 text-2xl font-semibold">Upload Your Cat's Photo</h2>
        
        <!-- Upload Form -->
        <form @submit.prevent="handleSubmit" v-if="!uploading">
            <div class="mb-6">
                <label for="locationName" class="block mb-2 font-medium text-gray-700">Location Name</label>
                <input
                    id="locationName"
                    v-model="locationName"
                    type="text"
                    placeholder="Enter location name"
                    required
                    class="w-full px-3 py-3 border border-gray-300 rounded-lg text-base transition-colors focus:outline-none focus:border-emerald-500 focus:ring-3 focus:ring-emerald-100"
                />
            </div>
            <div class="mb-6">
                <label for="description" class="block mb-2 font-medium text-gray-700">Description</label>
                <textarea
                    id="description"
                    v-model="description"
                    placeholder="Enter description"
                    rows="3"
                    class="w-full px-3 py-3 border border-gray-300 rounded-lg text-base transition-colors resize-none focus:outline-none focus:border-emerald-500 focus:ring-3 focus:ring-emerald-100"
                ></textarea>
            </div>
            
            <!-- GPS Coordinates -->
            <div class="mb-6 grid grid-cols-2 gap-4">
                <div>
                    <label for="latitude" class="block mb-2 font-medium text-gray-700">Latitude</label>
                    <input
                        id="latitude"
                        v-model="latitude"
                        type="number"
                        step="any"
                        placeholder="13.7563"
                        class="w-full px-3 py-3 border border-gray-300 rounded-lg text-base transition-colors focus:outline-none focus:border-emerald-500 focus:ring-3 focus:ring-emerald-100"
                    />
                </div>
                <div>
                    <label for="longitude" class="block mb-2 font-medium text-gray-700">Longitude</label>
                    <input
                        id="longitude"
                        v-model="longitude"
                        type="number"
                        step="any"
                        placeholder="100.5018"
                        class="w-full px-3 py-3 border border-gray-300 rounded-lg text-base transition-colors focus:outline-none focus:border-emerald-500 focus:ring-3 focus:ring-emerald-100"
                    />
                </div>
            </div>
            
            <!-- Get Current Location Button -->
            <div class="mb-6 text-center">
                <button
                    type="button"
                    @click="getCurrentLocation"
                    :disabled="gettingLocation"
                    class="bg-blue-500 text-white border-none px-4 py-2 rounded-md cursor-pointer transition-colors hover:bg-blue-600 disabled:opacity-50"
                >
                    {{ gettingLocation ? 'Getting Location...' : 'Get Current Location' }}
                </button>
            </div>
            
            <!-- File Upload Area -->
            <div
                class="border-2 border-dashed border-gray-300 rounded-xl p-12 text-center cursor-pointer transition-all mb-6 hover:border-emerald-500 hover:bg-green-50"
                @dragover.prevent
                @drop.prevent="handleDrop"
                @click="triggerFileInput"
            >
                <input
                    ref="fileInput"
                    type="file"
                    accept="image/*"
                    @change="handleFileChange"
                    class="hidden"
                />
                <div v-if="previewUrl">
                    <img :src="previewUrl" alt="Preview" class="max-w-full max-h-72 rounded-lg shadow-md mx-auto" />
                    <p class="mt-4 text-gray-600">{{ file?.name }}</p>
                </div>
                <div v-else>
                    <p class="mb-4 text-gray-500 text-lg">Drag and drop or click to upload</p>
                    <button type="button" class="bg-emerald-500 text-white border-none px-4 py-2 rounded-md cursor-pointer transition-colors hover:bg-emerald-600">Browse Files</button>
                </div>
            </div>
            
            <!-- Submit Button -->
            <button 
                type="submit" 
                :disabled="!file"
                class="w-full bg-emerald-500 text-white border-none py-3.5 px-6 rounded-lg text-lg font-medium cursor-pointer transition-colors hover:bg-emerald-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
                Upload Photo
            </button>
        </form>
        
        <!-- Upload Progress -->
        <div v-if="uploading" class="text-center">
            <div class="mb-4">
                <div class="animate-spin rounded-full h-16 w-16 border-4 border-emerald-500 border-t-transparent mx-auto"></div>
            </div>
            <p class="text-gray-600 text-lg">Uploading your photo...</p>
        </div>
        
        <!-- Success Message -->
        <div v-if="uploadSuccess" class="text-center">
            <div class="mb-4">
                <svg class="h-16 w-16 text-green-500 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                </svg>
            </div>
            <p class="text-green-600 text-lg mb-4">Photo uploaded successfully!</p>
            <button 
                @click="resetForm"
                class="bg-emerald-500 text-white border-none px-6 py-2 rounded-md cursor-pointer transition-colors hover:bg-emerald-600"
            >
                Upload Another Photo
            </button>
        </div>
        
        <!-- Error Message -->
        <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
            <p class="font-bold">Error:</p>
            <p>{{ error }}</p>
        </div>
    </div>
</template>

<script setup>
import { ref } from 'vue';

const locationName = ref('');
const description = ref('');
const latitude = ref('');
const longitude = ref('');
const file = ref(null);
const previewUrl = ref(null);
const fileInput = ref(null);
const uploading = ref(false);
const uploadSuccess = ref(false);
const error = ref('');
const gettingLocation = ref(false);

// Backend API URL
const API_URL = 'http://localhost:5000';

function triggerFileInput() {
    fileInput.value.click();
}

function handleFileChange(e) {
    const selected = e.target.files[0];
    if (selected && selected.type.startsWith('image/')) {
        file.value = selected;
        previewUrl.value = URL.createObjectURL(selected);
        error.value = '';
    }
}

function handleDrop(e) {
    const dropped = e.dataTransfer.files[0];
    if (dropped && dropped.type.startsWith('image/')) {
        file.value = dropped;
        previewUrl.value = URL.createObjectURL(dropped);
        error.value = '';
    }
}

function getCurrentLocation() {
    if (!navigator.geolocation) {
        error.value = 'Geolocation is not supported by this browser.';
        return;
    }

    gettingLocation.value = true;
    
    navigator.geolocation.getCurrentPosition(
        (position) => {
            latitude.value = position.coords.latitude.toFixed(6);
            longitude.value = position.coords.longitude.toFixed(6);
            gettingLocation.value = false;
        },
        (error) => {
            console.error('Error getting location:', error);
            error.value = 'Unable to retrieve your location. Please enter coordinates manually.';
            gettingLocation.value = false;
        }
    );
}

async function handleSubmit() {
    if (!file.value) {
        error.value = 'Please select a file to upload.';
        return;
    }

    uploading.value = true;
    error.value = '';

    try {
        const formData = new FormData();
        formData.append('file', file.value);
        formData.append('location', locationName.value);
        formData.append('description', description.value);
        formData.append('latitude', latitude.value);
        formData.append('longitude', longitude.value);

        const response = await fetch(`${API_URL}/upload`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Upload failed');
        }

        const result = await response.json();
        console.log('Upload successful:', result);
        
        uploadSuccess.value = true;
        uploading.value = false;
        
    } catch (err) {
        console.error('Upload error:', err);
        error.value = err.message || 'An error occurred during upload';
        uploading.value = false;
    }
}

function resetForm() {
    locationName.value = '';
    description.value = '';
    latitude.value = '';
    longitude.value = '';
    file.value = null;
    previewUrl.value = null;
    uploadSuccess.value = false;
    error.value = '';
    
    // Clear the file input
    if (fileInput.value) {
        fileInput.value.value = '';
    }
}
</script>

<style scoped>
/* All styles are now handled by Tailwind CSS classes */
</style>

