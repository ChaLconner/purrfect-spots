import { apiV1 } from '../utils/api';
import type { OfflineQueuedResponse } from '../utils/offlineQueue';

export interface Comment {
  id: string;
  user_id: string;
  photo_id: string;
  content: string;
  created_at: string;
  user_name?: string;
  user_picture?: string;
  user_is_pro?: boolean;
  pending?: boolean;
  queue_id?: string;
}

export interface LikeResponse {
  liked: boolean;
  likes_count: number;
}

export const SocialService = {
  async toggleLike(photoId: string): Promise<LikeResponse | OfflineQueuedResponse> {
    return apiV1.post(`/social/photos/${photoId}/like`, undefined, {
      queueWhenOffline: true,
      retryConfig: { maxRetries: 0 },
    });
  },

  async getComments(photoId: string): Promise<Comment[]> {
    return apiV1.get(`/social/photos/${photoId}/comments`);
  },

  async addComment(photoId: string, content: string): Promise<Comment | OfflineQueuedResponse> {
    return apiV1.post(`/social/photos/${photoId}/comments`, { content }, {
      queueWhenOffline: true,
      retryConfig: { maxRetries: 0 },
    });
  },

  async deleteComment(commentId: string): Promise<void> {
    return apiV1.delete(`/social/comments/${commentId}`);
  },

  async updateComment(commentId: string, content: string): Promise<Comment | OfflineQueuedResponse> {
    return apiV1.put(`/social/comments/${commentId}`, { content }, {
      queueWhenOffline: true,
      retryConfig: { maxRetries: 0 },
    });
  },
};
