<template>
    <div class="upload-container">
        <h2>Upload Your Cat's Photo</h2>
        <form @submit.prevent="handleSubmit">
            <div class="form-group">
                <label for="locationName">Location Name</label>
                <input
                    id="locationName"
                    v-model="locationName"
                    type="text"
                    placeholder="Enter location name"
                    required
                />
            </div>
            <div class="form-group">
                <label for="description">Description</label>
                <textarea
                    id="description"
                    v-model="description"
                    placeholder="Enter description"
                    rows="3"
                    style="resize: none"
                ></textarea>
            </div>
            <div
                class="upload-area"
                @dragover.prevent
                @drop.prevent="handleDrop"
                @click="triggerFileInput"
            >
                <input
                    ref="fileInput"
                    type="file"
                    accept="image/*"
                    @change="handleFileChange"
                    style="display: none"
                />
                <div v-if="previewUrl">
                    <img :src="previewUrl" alt="Preview" class="preview-img" />
                </div>
                <div v-else>
                    <p>Drag and drop or click to upload</p>
                    <button type="button" class="browse-btn">Browse Files</button>
                </div>
            </div>
            <button type="submit" class="submit-btn">Upload</button>
        </form>
    </div>
</template>

<script setup>
import { ref } from 'vue';

const locationName = ref('');
const description = ref('');
const file = ref(null);
const previewUrl = ref(null);
const fileInput = ref(null);

function triggerFileInput() {
    fileInput.value.click();
}

function handleFileChange(e) {
    const selected = e.target.files[0];
    if (selected && selected.type.startsWith('image/')) {
        file.value = selected;
        previewUrl.value = URL.createObjectURL(selected);
    }
}

function handleDrop(e) {
    const dropped = e.dataTransfer.files[0];
    if (dropped && dropped.type.startsWith('image/')) {
        file.value = dropped;
        previewUrl.value = URL.createObjectURL(dropped);
    }
}

function handleSubmit() {
    // Implement upload logic here
    alert('Upload submitted!');
}
</script>

<style scoped>
.upload-container {
    max-width: 600px;
    margin: 2rem auto;
    padding: 2rem;
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.upload-container h2 {
    text-align: center;
    margin-bottom: 2rem;
    color: #374151;
    font-size: 1.5rem;
    font-weight: 600;
}

.form-group {
    margin-bottom: 1.5rem;
}

.form-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: #374151;
}

.form-group input,
.form-group textarea {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    font-size: 1rem;
    transition: border-color 0.2s;
}

.form-group input:focus,
.form-group textarea:focus {
    outline: none;
    border-color: #10b981;
    box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
}

.upload-area {
    border: 2px dashed #d1d5db;
    border-radius: 12px;
    padding: 3rem 2rem;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s;
    margin-bottom: 1.5rem;
}

.upload-area:hover {
    border-color: #10b981;
    background-color: #f0fdf4;
}

.upload-area p {
    margin-bottom: 1rem;
    color: #6b7280;
    font-size: 1.1rem;
}

.browse-btn {
    background: #10b981;
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    cursor: pointer;
    transition: background-color 0.2s;
}

.browse-btn:hover {
    background: #059669;
}

.preview-img {
    max-width: 100%;
    max-height: 300px;
    border-radius: 8px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.submit-btn {
    width: 100%;
    background: #10b981;
    color: white;
    border: none;
    padding: 0.875rem 1.5rem;
    border-radius: 8px;
    font-size: 1.1rem;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.2s;
}

.submit-btn:hover {
    background: #059669;
}
</style>

