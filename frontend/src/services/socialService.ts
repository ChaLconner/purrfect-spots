import { apiV1 } from '../utils/api';

export interface Comment {
  id: string;
  user_id: string;
  photo_id: string;
  content: string;
  created_at: string;
  user_name?: string;
  user_picture?: string;
}

export const SocialService = {
  async toggleLike(photoId: string): Promise<{ liked: boolean; likes_count: number }> {
    return apiV1.post(`/social/photos/${photoId}/like`);
  },

  async getComments(photoId: string): Promise<Comment[]> {
    return apiV1.get(`/social/photos/${photoId}/comments`);
  },

  async addComment(photoId: string, content: string): Promise<Comment> {
    return apiV1.post(`/social/photos/${photoId}/comments`, { content });
  },

  async deleteComment(commentId: string): Promise<void> {
    return apiV1.delete(`/social/comments/${commentId}`);
  },

  async updateComment(commentId: string, content: string): Promise<Comment> {
    return apiV1.put(`/social/comments/${commentId}`, { content });
  },
};
