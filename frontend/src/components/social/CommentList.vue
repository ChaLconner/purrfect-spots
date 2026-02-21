<template>
  <div
    class="w-full min-w-0 overflow-x-hidden bg-cream-dark/30 p-4 rounded-2xl mt-2 border border-cream-dark/50"
  >
    <h3 class="font-heading text-lg font-bold mb-3 text-brown flex items-center gap-2">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="h-5 w-5"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        stroke-width="2.5"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
        />
      </svg>
      Comments ({{ comments.length }})
    </h3>

    <!-- Comment List -->
    <div class="space-y-4 mb-6">
      <div
        v-if="loading"
        class="text-brown-light text-center py-6 flex flex-col items-center gap-2"
      >
        <div
          class="w-6 h-6 border-2 border-brown/20 border-t-brown rounded-full animate-spin"
        ></div>
        <span class="text-sm font-medium">Loading comments...</span>
      </div>
      <div
        v-else-if="comments.length === 0"
        class="text-brown-light/70 text-center py-8 italic text-sm"
      >
        Be the first to leave a friendly paw-print!
      </div>

      <div v-for="comment in displayedComments" :key="comment.id" class="flex gap-4 group">
        <img
          :src="getAvatarUrl(comment)"
          alt="User avatar"
          class="w-10 h-10 rounded-full object-cover border-2 border-white shadow-sm flex-shrink-0"
          @error="handleAvatarError(comment.id)"
        />
        <div class="flex-1 min-w-0">
          <BaseCard
            variant="glass"
            padding="sm"
            class="relative rounded-2xl bg-white/80 overflow-hidden"
          >
            <div class="flex justify-between items-baseline mb-1 gap-2">
              <span class="font-bold text-sm text-brown truncate">{{
                comment.user_name || 'Anonymous'
              }}</span>
              <span
                class="text-[10px] uppercase tracking-wider font-bold text-brown-light/60 whitespace-nowrap flex-shrink-0"
                >{{ formatDate(comment.created_at) }}</span
              >
            </div>
            <div v-if="editingId === comment.id" class="mt-2">
              <BaseInput
                v-model="editContent"
                is-textarea
                :rows="2"
                class="bg-white border-sage/30"
              />
              <div class="flex justify-end gap-2 mt-2">
                <button
                  class="text-[11px] font-bold text-gray-400 hover:text-gray-600 px-2 py-1"
                  @click="cancelEdit"
                >
                  Cancel
                </button>
                <button
                  class="text-[11px] font-bold text-sage hover:text-sage-dark px-3 py-1 bg-sage/10 rounded-lg transition-colors"
                  :disabled="isUpdating"
                  @click="saveEdit(comment.id)"
                >
                  Save
                </button>
              </div>
            </div>
            <p v-else class="text-brown-dark/80 text-sm leading-relaxed pr-6 break-words">
              {{ comment.content }}
            </p>

            <!-- Action Icons at Bottom Right -->
            <div
              v-if="currentUserId === comment.user_id && editingId !== comment.id"
              class="absolute bottom-2 right-2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity bg-white/60 backdrop-blur-sm rounded-lg p-0.5"
            >
              <button
                class="text-sage hover:text-sage-dark transition-colors p-1"
                title="Edit comment"
                @click="startEdit(comment)"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-3.5 w-3.5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2.5"
                    d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
                  />
                </svg>
              </button>
              <button
                class="text-terracotta hover:text-terracotta-dark transition-colors p-1"
                title="Remove comment"
                @click="deleteComment(comment.id)"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-3.5 w-3.5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2.5"
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
              </button>
            </div>
          </BaseCard>
        </div>
      </div>

      <!-- View All Toggle -->
      <div v-if="comments.length > 3" class="flex justify-center mt-2">
        <button
          class="text-xs font-bold text-brown-light hover:text-brown transition-colors py-2 px-4 bg-white/40 rounded-full border border-brown-light/10"
          @click="showAll = !showAll"
        >
          {{ showAll ? 'Show less' : `View all ${comments.length} comments` }}
        </button>
      </div>
    </div>

    <!-- Add Comment Form -->
    <div v-if="isAuthenticated" class="mt-6 border-t border-cream-dark/50 pt-6">
      <div class="flex gap-3 items-start">
        <div class="flex-1 relative">
          <BaseInput
            v-model="newComment"
            is-textarea
            placeholder="Write a comment..."
            :rows="3"
            :disabled="isSubmitting"
            @keydown.ctrl.enter="postComment"
          />
        </div>
      </div>
      <div class="flex justify-end mt-3">
        <BaseButton
          variant="ghibli-primary"
          class="px-8"
          :disabled="!newComment.trim() || isSubmitting"
          :loading="isSubmitting"
          @click="postComment"
        >
          {{ isSubmitting ? 'Posting...' : 'Post Comment' }}
        </BaseButton>
      </div>
    </div>
    <div
      v-else
      class="text-center py-6 bg-cream-dark/10 rounded-2xl border border-dashed border-brown-light/20"
    >
      <a href="/login" class="text-sm text-sage font-bold hover:text-sage-dark transition-colors">
        Sign in to post a comment
      </a>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { SocialService, type Comment } from '@/services/socialService';
import { useAuthStore } from '@/store';
import { useToastStore } from '@/store';
import { BaseButton, BaseCard, BaseInput } from '@/components/ui';
import { EXTERNAL_URLS } from '@/utils/constants';

const props = defineProps<{
  photoId: string;
}>();

const emit = defineEmits<{
  (e: 'comment:added'): void;
}>();

const authStore = useAuthStore();
const toastStore = useToastStore();
const comments = ref<Comment[]>([]);
const loading = ref(true);
const newComment = ref('');
const isSubmitting = ref(false);
const editingId = ref<string | null>(null);
const editContent = ref('');
const isUpdating = ref(false);
const showAll = ref(false);

const isAuthenticated = computed(() => authStore.isAuthenticated);
const currentUserId = computed(() => authStore.user?.id);

const displayedComments = computed(() => {
  if (showAll.value) return comments.value;
  return [...comments.value].slice(-3); // Show 3 most recent
});

// Avatar handling
const avatarErrors = ref<Record<string, boolean>>({});

function getAvatarUrl(comment: Comment) {
  if (avatarErrors.value[comment.id]) {
    return EXTERNAL_URLS.DEFAULT_AVATAR; // Use valid fallback
  }
  return comment.user_picture || EXTERNAL_URLS.DEFAULT_AVATAR;
}

function handleAvatarError(commentId: string) {
  avatarErrors.value[commentId] = true;
}

onMounted(() => {
  fetchComments();
});

async function fetchComments() {
  loading.value = true;
  try {
    comments.value = await SocialService.getComments(props.photoId);
  } catch (e) {
    console.error('Failed to load comments', e);
  } finally {
    loading.value = false;
  }
}

async function postComment() {
  if (!newComment.value.trim()) return;

  isSubmitting.value = true;
  try {
    const comment = await SocialService.addComment(props.photoId, newComment.value);
    comments.value.push(comment); // Append locally
    newComment.value = '';
    emit('comment:added');
  } catch (e) {
    console.error(e);
    toastStore.addToast({
      title: 'Error',
      message: 'Failed to post comment',
      type: 'error',
    });
  } finally {
    isSubmitting.value = false;
  }
}

async function deleteComment(id: string) {
  // eslint-disable-next-line no-alert
  if (!window.confirm('Delete this comment?')) return;
  try {
    await SocialService.deleteComment(id);
    comments.value = comments.value.filter((c) => c.id !== id);
  } catch {
    toastStore.addToast({ title: 'Error', message: 'Failed to delete', type: 'error' });
  }
}

function startEdit(comment: Comment) {
  editingId.value = comment.id;
  editContent.value = comment.content;
}

function cancelEdit() {
  editingId.value = null;
  editContent.value = '';
}

async function saveEdit(id: string) {
  if (!editContent.value.trim() || isUpdating.value) return;

  isUpdating.value = true;
  try {
    const updated = await SocialService.updateComment(id, editContent.value);
    const index = comments.value.findIndex((c) => c.id === id);
    if (index !== -1) {
      comments.value[index] = updated;
    }
    cancelEdit();
  } catch {
    toastStore.addToast({
      title: 'Error',
      message: 'Failed to update comment',
      type: 'error',
    });
  } finally {
    isUpdating.value = false;
  }
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}
</script>
