<template>
  <div class="min-h-screen bg-gray-50 pt-20">
    <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Profile Header -->
      <div class="bg-white rounded-lg shadow-sm p-8 mb-8">
        <div class="flex flex-col items-center text-center">
          <!-- Profile Picture -->
          <div class="relative mb-4">
            <img 
              :src="authStore.user?.picture || '/default-avatar.svg'" 
              :alt="authStore.user?.name || 'User'"
              class="w-32 h-32 rounded-full object-cover border-4 border-orange-200"
            />
          </div>
          
          <!-- Name -->
          <h1 class="text-3xl font-bold text-gray-900 mb-2">
            {{ authStore.user?.name || 'Unknown User' }}
          </h1>
          
          <!-- Bio -->
          <p class="text-gray-600 mb-2">
            {{ authStore.user?.bio || 'Cat lover and explorer' }}
          </p>
          
          <!-- Join Date -->
          <p class="text-sm text-gray-500 mb-6">
            Joined in {{ formatJoinDate(authStore.user?.created_at) }}
          </p>
          
          <!-- Edit Profile Button -->
          <button 
            @click="showEditModal = true"
            class="px-6 py-2 bg-green-100 text-green-700 rounded-full hover:bg-green-200 transition-colors"
          >
            Edit Profile
          </button>
        </div>
      </div>

      <!-- Navigation Tabs -->
      <div class="bg-white rounded-lg shadow-sm mb-8">
        <div class="flex border-b border-gray-200">
          <button 
            @click="activeTab = 'uploads'"
            :class="[
              'px-6 py-3 text-sm font-medium border-b-2 transition-colors',
              activeTab === 'uploads' 
                ? 'border-orange-500 text-orange-600' 
                : 'border-transparent text-gray-500 hover:text-gray-700'
            ]"
          >
            My Uploads
          </button>
          <button 
            @click="activeTab = 'saved'"
            :class="[
              'px-6 py-3 text-sm font-medium border-b-2 transition-colors',
              activeTab === 'saved' 
                ? 'border-orange-500 text-orange-600' 
                : 'border-transparent text-gray-500 hover:text-gray-700'
            ]"
          >
            Saved Spots
          </button>
          <button 
            @click="activeTab = 'about'"
            :class="[
              'px-6 py-3 text-sm font-medium border-b-2 transition-colors',
              activeTab === 'about' 
                ? 'border-orange-500 text-orange-600' 
                : 'border-transparent text-gray-500 hover:text-gray-700'
            ]"
          >
            About
          </button>
        </div>
      </div>

      <!-- Tab Content -->
      <div class="bg-white rounded-lg shadow-sm p-6">
        <!-- My Uploads Tab -->
        <div v-if="activeTab === 'uploads'">
          <div v-if="uploads.length === 0" class="text-center py-12">
            <p class="text-gray-500 mb-4">No uploads yet</p>
            <button 
              @click="router.push('/upload')"
              class="px-6 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors"
            >
              Upload Your First Photo
            </button>
          </div>
          <div v-else class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
            <div 
              v-for="upload in uploads" 
              :key="upload.id"
              class="relative group aspect-square bg-gray-100 rounded-lg overflow-hidden cursor-pointer hover:shadow-lg transition-shadow"
              @click="openImageModal(upload)"
            >
              <img 
                :src="upload.image_url" 
                :alt="upload.description || 'Cat photo'"
                class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
              />
              <div class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-opacity"></div>
            </div>
          </div>
        </div>

        <!-- Saved Spots Tab -->
        <div v-if="activeTab === 'saved'">
          <div class="text-center py-12">
            <p class="text-gray-500">Saved spots feature coming soon!</p>
          </div>
        </div>

        <!-- About Tab -->
        <div v-if="activeTab === 'about'">
          <div class="max-w-2xl">
            <h3 class="text-lg font-semibold mb-4">About {{ authStore.user?.name }}</h3>
            <p class="text-gray-600 leading-relaxed">
              {{ authStore.user?.bio || 'This user hasn\'t added a bio yet.' }}
            </p>
            <div class="mt-6 space-y-2">
              <div class="flex items-center text-sm text-gray-500">
                <span class="font-medium">Email:</span>
                <span class="ml-2">{{ authStore.user?.email }}</span>
              </div>
              <div class="flex items-center text-sm text-gray-500">
                <span class="font-medium">Member since:</span>
                <span class="ml-2">{{ formatJoinDate(authStore.user?.created_at) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Profile Modal -->
    <div v-if="showEditModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 w-full max-w-md mx-4">
        <h2 class="text-xl font-bold mb-4">Edit Profile</h2>
        <form @submit.prevent="saveProfile">
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-2">Name</label>
            <input 
              v-model="editForm.name"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
              required
            />
          </div>
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-2">Bio</label>
            <textarea 
              v-model="editForm.bio"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
              rows="3"
              placeholder="Tell us about yourself..."
            ></textarea>
          </div>
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-2">Profile Picture URL</label>
            <input 
              v-model="editForm.picture"
              type="url"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
              placeholder="https://example.com/image.jpg"
            />
          </div>
          <div class="flex justify-end space-x-3">
            <button 
              type="button" 
              @click="showEditModal = false"
              class="px-4 py-2 text-gray-600 hover:text-gray-800"
            >
              Cancel
            </button>
            <button 
              type="submit"
              class="px-4 py-2 bg-orange-500 text-white rounded-md hover:bg-orange-600"
            >
              Save Changes
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Image Modal -->
    <div v-if="selectedImage" class="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50" @click="closeImageModal">
      <div class="relative max-w-4xl max-h-full p-4">
        <button 
          @click="closeImageModal"
          class="absolute top-2 right-2 z-10 text-white hover:text-gray-300"
        >
          <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
        <img 
          :src="selectedImage.image_url" 
          :alt="selectedImage.description || 'Cat photo'"
          class="max-w-full max-h-full object-contain"
          @click.stop
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { authStore } from '../store/auth';
import { ProfileService, type ProfileUpdateData } from '../services/profileService';

const router = useRouter();

interface Upload {
  id: string;
  image_url: string;
  description?: string;
  created_at: string;
}

const activeTab = ref('uploads');
const uploads = ref<Upload[]>([]);
const showEditModal = ref(false);
const selectedImage = ref<Upload | null>(null);

const editForm = reactive({
  name: '',
  bio: '',
  picture: ''
});

// Mock data for uploads - replace with actual API call
const mockUploads: Upload[] = [
  {
    id: '1',
    image_url: 'https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=300&h=300&fit=crop',
    description: 'Cute tabby cat',
    created_at: '2024-01-15T10:30:00Z'
  },
  {
    id: '2',
    image_url: 'https://images.unsplash.com/photo-1573865526739-10659fec78a5?w=300&h=300&fit=crop',
    description: 'Orange cat in garden',
    created_at: '2024-01-10T14:20:00Z'
  },
  {
    id: '3',
    image_url: 'https://images.unsplash.com/photo-1592194996308-7b43878e84a6?w=300&h=300&fit=crop',
    description: 'Sleepy kitten',
    created_at: '2024-01-05T09:15:00Z'
  },
  {
    id: '4',
    image_url: 'https://images.unsplash.com/photo-1533743983669-94fa5c4338ec?w=300&h=300&fit=crop',
    description: 'Black and white cat',
    created_at: '2024-01-01T16:45:00Z'
  },
  {
    id: '5',
    image_url: 'https://images.unsplash.com/photo-1561948955-570b270e7c36?w=300&h=300&fit=crop',
    description: 'Persian cat',
    created_at: '2023-12-28T11:30:00Z'
  },
  {
    id: '6',
    image_url: 'https://images.unsplash.com/photo-1596854407944-bf87f6fdd49e?w=300&h=300&fit=crop',
    description: 'Cat in library',
    created_at: '2023-12-25T13:20:00Z'
  }
];

const formatJoinDate = (dateString: string | undefined) => {
  if (!dateString) return 'Unknown';
  
  const date = new Date(dateString);
  return date.getFullYear().toString();
};

const openImageModal = (upload: Upload) => {
  selectedImage.value = upload;
};

const closeImageModal = () => {
  selectedImage.value = null;
};

const saveProfile = async () => {
  try {
    const updateData: ProfileUpdateData = {
      name: editForm.name,
      bio: editForm.bio,
      picture: editForm.picture
    };

    const updatedUser = await ProfileService.updateProfile(updateData);
    
    // Update local store
    if (authStore.user) {
      authStore.user.name = updatedUser.name;
      authStore.user.bio = updatedUser.bio;
      authStore.user.picture = updatedUser.picture;
      
      // Update localStorage
      localStorage.setItem('user_data', JSON.stringify(authStore.user));
    }
    
    showEditModal.value = false;
  } catch (error) {
    console.error('Error saving profile:', error);
    // You can add toast notification here
  }
};

onMounted(async () => {
  try {
    // Load user uploads from API
    const userUploads = await ProfileService.getUserUploads();
    uploads.value = userUploads;
  } catch (error) {
    console.error('Error loading uploads:', error);
    // Fallback to mock data
    uploads.value = mockUploads;
  }
  
  // Initialize edit form with current user data
  if (authStore.user) {
    editForm.name = authStore.user.name || '';
    editForm.bio = authStore.user.bio || '';
    editForm.picture = authStore.user.picture || '';
  }
});
</script>
