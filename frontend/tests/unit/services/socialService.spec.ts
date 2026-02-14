import { describe, it, expect, vi, beforeEach } from 'vitest';
import { SocialService } from '@/services/socialService';
import { apiV1 } from '@/utils/api';

vi.mock('@/utils/api', () => ({
  apiV1: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('SocialService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('toggles like for a photo', async () => {
    const mockResponse = { liked: true, likes_count: 5 };
    vi.mocked(apiV1.post).mockResolvedValue(mockResponse);

    const result = await SocialService.toggleLike('photo-123');
    
    expect(apiV1.post).toHaveBeenCalledWith('/social/photos/photo-123/like');
    expect(result).toEqual(mockResponse);
  });

  it('gets comments for a photo', async () => {
    const mockComments = [
      { id: 'c1', content: 'Cute!', user_id: 'u1', photo_id: 'photo-123', created_at: '2024-01-01' }
    ];
    vi.mocked(apiV1.get).mockResolvedValue(mockComments);

    const result = await SocialService.getComments('photo-123');

    expect(apiV1.get).toHaveBeenCalledWith('/social/photos/photo-123/comments');
    expect(result).toEqual(mockComments);
  });

  it('adds a comment to a photo', async () => {
    const mockComment = { id: 'c2', content: 'New comment', user_id: 'u2', photo_id: 'photo-123', created_at: '2024-01-01' };
    vi.mocked(apiV1.post).mockResolvedValue(mockComment);

    const result = await SocialService.addComment('photo-123', 'New comment');

    expect(apiV1.post).toHaveBeenCalledWith('/social/photos/photo-123/comments', { content: 'New comment' });
    expect(result).toEqual(mockComment);
  });

  it('updates a comment', async () => {
    const mockComment = { id: 'c1', content: 'Updated', user_id: 'u1', photo_id: 'photo-123', created_at: '2024-01-01' };
    vi.mocked(apiV1.put).mockResolvedValue(mockComment);

    const result = await SocialService.updateComment('c1', 'Updated');

    expect(apiV1.put).toHaveBeenCalledWith('/social/comments/c1', { content: 'Updated' });
    expect(result).toEqual(mockComment);
  });

  it('deletes a comment', async () => {
    vi.mocked(apiV1.delete).mockResolvedValue(undefined);

    await SocialService.deleteComment('c1');

    expect(apiV1.delete).toHaveBeenCalledWith('/social/comments/c1');
  });
});
