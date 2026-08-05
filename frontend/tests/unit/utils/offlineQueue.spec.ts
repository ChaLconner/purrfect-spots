import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  clearOfflineQueue,
  enqueueMutation,
  flushOfflineQueue,
  getFailedMutationCount,
  getPendingMutationCount,
  isAllowedMutation,
  listOfflineMutations,
  registerOfflineReplayHandler,
} from '@/utils/offlineQueue';

describe('offline mutation queue', () => {
  beforeEach(async () => {
    await clearOfflineQueue();
    registerOfflineReplayHandler(vi.fn().mockResolvedValue(undefined));
  });

  it('allow-lists only safe social and notification mutations', () => {
    expect(isAllowedMutation('POST', '/api/v1/social/photos/photo-1/like')).toBe(true);
    expect(isAllowedMutation('PUT', '/api/v1/social/comments/comment-1')).toBe(true);
    expect(isAllowedMutation('POST', '/api/v1/subscription/checkout')).toBe(false);
    expect(isAllowedMutation('DELETE', '/api/v1/social/comments/comment-1')).toBe(false);
  });

  it('persists a queue record without authorization material', async () => {
    const result = await enqueueMutation({
      method: 'POST',
      endpoint: '/api/v1/social/photos/photo-1/comments',
      data: { content: 'offline comment' },
    });
    const records = await listOfflineMutations();

    expect(result.queued).toBe(true);
    expect(records).toHaveLength(1);
    expect(records[0].data).toEqual({ content: 'offline comment' });
    expect(JSON.stringify(records[0])).not.toContain('Authorization');
    expect(records[0].idempotencyKey).toBe(result.idempotency_key);
  });

  it('replays mutations in creation order and removes successful records', async () => {
    const replay = vi.fn().mockResolvedValue(undefined);
    registerOfflineReplayHandler(replay);
    await enqueueMutation({ method: 'POST', endpoint: '/api/v1/social/photos/a/like' });
    await enqueueMutation({ method: 'POST', endpoint: '/api/v1/social/photos/b/like' });

    const result = await flushOfflineQueue();

    expect(replay).toHaveBeenCalledTimes(2);
    expect(replay.mock.calls[0][0].endpoint).toContain('/photos/a/');
    expect(replay.mock.calls[1][0].endpoint).toContain('/photos/b/');
    expect(result).toEqual({ processed: 2, remaining: 0, failed: 0 });
    expect(await getPendingMutationCount()).toBe(0);
  });

  it('moves permanent failures to retained dead-letter state', async () => {
    registerOfflineReplayHandler(vi.fn().mockRejectedValue({ statusCode: 422 }));
    await enqueueMutation({ method: 'POST', endpoint: '/api/v1/social/photos/a/like' });

    const result = await flushOfflineQueue();

    expect(result.failed).toBe(1);
    expect(await getFailedMutationCount()).toBe(1);
    expect(await getPendingMutationCount()).toBe(0);
  });
});
