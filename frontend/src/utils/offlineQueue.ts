export type OfflineMutationMethod = 'POST' | 'PUT';
export type OfflineMutationStatus = 'pending' | 'failed';

export interface OfflineMutation {
  id: string;
  method: OfflineMutationMethod;
  endpoint: string;
  data?: unknown;
  idempotencyKey: string;
  createdAt: number;
  attempts: number;
  nextAttemptAt: number;
  status: OfflineMutationStatus;
  lastError?: string;
}

export interface OfflineQueuedResponse {
  queued: true;
  queue_id: string;
  idempotency_key: string;
}

export interface OfflineFlushResult {
  processed: number;
  remaining: number;
  failed: number;
}

export class OfflineQueueError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'OfflineQueueError';
  }
}

type ReplayHandler = (mutation: OfflineMutation) => Promise<unknown>;
type QueueListener = () => void;
type QueueChangeReason = 'changed' | 'enqueued' | 'synced' | 'failed';

const DB_NAME = 'purrfect-spots-offline';
const DB_VERSION = 1;
const STORE_NAME = 'mutations';
const LOCAL_STORAGE_KEY = 'purrfect_spots_offline_mutations';
const MAX_RECORDS = 100;
const MAX_DATA_BYTES = 64 * 1024;

const listeners = new Set<QueueListener>();
let replayHandler: ReplayHandler | null = null;
let databasePromise: Promise<IDBDatabase | null> | null = null;
let flushPromise: Promise<OfflineFlushResult> | null = null;
let fallbackIdSequence = 0;

export function createOfflineIdempotencyKey(): string {
  if (typeof globalThis.crypto?.randomUUID === 'function') return globalThis.crypto.randomUUID();
  if (typeof globalThis.crypto?.getRandomValues === 'function') {
    const bytes = globalThis.crypto.getRandomValues(new Uint8Array(16));
    return Array.from(bytes, (value) => value.toString(16).padStart(2, '0')).join('');
  }
  return `${Date.now().toString(36)}-${(fallbackIdSequence++).toString(36)}`;
}

function createId(): string {
  return createOfflineIdempotencyKey();
}

function notify(reason: QueueChangeReason = 'changed'): void {
  listeners.forEach((listener) => listener());
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('offline-queue-updated', { detail: { reason } }));
  }
}

function isBrowserStorageAvailable(): boolean {
  return globalThis.localStorage !== undefined;
}

function openDatabase(): Promise<IDBDatabase | null> {
  if (globalThis.indexedDB === undefined) return Promise.resolve(null);
  if (databasePromise) return databasePromise;

  databasePromise = new Promise((resolve) => {
    try {
      const request = globalThis.indexedDB.open(DB_NAME, DB_VERSION);
      request.onupgradeneeded = (): void => {
        const database = request.result;
        if (!database.objectStoreNames.contains(STORE_NAME)) {
          const store = database.createObjectStore(STORE_NAME, { keyPath: 'id' });
          store.createIndex('createdAt', 'createdAt', { unique: false });
        }
      };
      request.onsuccess = (): void => resolve(request.result);
      request.onerror = (): void => resolve(null);
    } catch {
      resolve(null);
    }
  });
  return databasePromise;
}

async function readIndexedRecords(): Promise<OfflineMutation[] | null> {
  const database = await openDatabase();
  if (!database) return null;
  return new Promise((resolve) => {
    try {
      const transaction = database.transaction(STORE_NAME, 'readonly');
      const request = transaction.objectStore(STORE_NAME).getAll();
      request.onsuccess = (): void => resolve((request.result as OfflineMutation[]).sort((a, b) => a.createdAt - b.createdAt));
      request.onerror = (): void => resolve(null);
    } catch {
      resolve(null);
    }
  });
}

async function writeIndexedRecords(records: OfflineMutation[]): Promise<boolean> {
  const database = await openDatabase();
  if (!database) return false;
  return new Promise((resolve) => {
    try {
      const transaction = database.transaction(STORE_NAME, 'readwrite');
      const store = transaction.objectStore(STORE_NAME);
      store.clear();
      records.forEach((record) => store.put(record));
      transaction.oncomplete = (): void => resolve(true);
      transaction.onerror = (): void => resolve(false);
      transaction.onabort = (): void => resolve(false);
    } catch {
      resolve(false);
    }
  });
}

function readLocalRecords(): OfflineMutation[] {
  if (!isBrowserStorageAvailable()) return [];
  try {
    const raw = globalThis.localStorage.getItem(LOCAL_STORAGE_KEY);
    if (!raw) return [];
    const records = JSON.parse(raw);
    return Array.isArray(records) ? (records as OfflineMutation[]).sort((a, b) => a.createdAt - b.createdAt) : [];
  } catch {
    return [];
  }
}

function writeLocalRecords(records: OfflineMutation[]): boolean {
  if (!isBrowserStorageAvailable()) return false;
  try {
    globalThis.localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(records));
    return true;
  } catch {
    return false;
  }
}

async function readRecords(): Promise<OfflineMutation[]> {
  const indexedRecords = await readIndexedRecords();
  return indexedRecords ?? readLocalRecords();
}

async function writeRecords(records: OfflineMutation[]): Promise<void> {
  const normalized = [...records].sort((a, b) => a.createdAt - b.createdAt);
  if (!(await writeIndexedRecords(normalized)) && !writeLocalRecords(normalized)) {
    throw new OfflineQueueError('Offline queue storage is unavailable');
  }
}

export function isAllowedMutation(method: string, endpoint: string): method is OfflineMutationMethod {
  const normalizedMethod = method.toUpperCase();
  const path = endpoint.split('?')[0].replace(/\/$/, '');
  if (normalizedMethod === 'POST') {
    return /^\/api\/v1\/social\/photos\/[^/]+\/(like|comments)$/.test(path) ||
      path === '/api/v1/notifications/read-all';
  }
  if (normalizedMethod === 'PUT') {
    return /^\/api\/v1\/social\/comments\/[^/]+$/.test(path) ||
      /^\/api\/v1\/notifications\/[^/]+\/read$/.test(path) ||
      path === '/api/v1/notifications/read-all';
  }
  return false;
}

function serializeData(data: unknown): string {
  try {
    return JSON.stringify(data ?? null);
  } catch {
    throw new OfflineQueueError('Offline mutation data is not serializable');
  }
}

export function isOfflineQueuedResponse(value: unknown): value is OfflineQueuedResponse {
  return Boolean(
    value &&
      typeof value === 'object' &&
      (value as { queued?: unknown }).queued === true &&
      typeof (value as { queue_id?: unknown }).queue_id === 'string'
  );
}

export async function enqueueMutation(
  mutation: Pick<OfflineMutation, 'method' | 'endpoint' | 'data'> & Partial<Pick<OfflineMutation, 'idempotencyKey'>>
): Promise<OfflineQueuedResponse> {
  const method = mutation.method.toUpperCase();
  if (!isAllowedMutation(method, mutation.endpoint)) {
    throw new OfflineQueueError('This mutation is not allowed to be queued offline');
  }
  if (new TextEncoder().encode(serializeData(mutation.data)).byteLength > MAX_DATA_BYTES) {
    throw new OfflineQueueError('Offline mutation is too large');
  }

  const records = await readRecords();
  if (records.length >= MAX_RECORDS) throw new OfflineQueueError('Offline queue is full');

  const id = createId();
  const idempotencyKey = mutation.idempotencyKey || createId();
  const record: OfflineMutation = {
    id,
    method,
    endpoint: mutation.endpoint,
    data: mutation.data,
    idempotencyKey,
    createdAt: Date.now(),
    attempts: 0,
    nextAttemptAt: Date.now(),
    status: 'pending',
  };
  await writeRecords([...records, record]);
  notify('enqueued');
  return { queued: true, queue_id: id, idempotency_key: idempotencyKey };
}

export async function listOfflineMutations(): Promise<OfflineMutation[]> {
  return readRecords();
}

export async function getPendingMutationCount(): Promise<number> {
  const records = await readRecords();
  return records.filter((record) => record.status === 'pending').length;
}

export async function getFailedMutationCount(): Promise<number> {
  const records = await readRecords();
  return records.filter((record) => record.status === 'failed').length;
}

export function subscribeOfflineQueue(listener: QueueListener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function registerOfflineReplayHandler(handler: ReplayHandler): void {
  replayHandler = handler;
}

function getStatus(error: unknown): number | undefined {
  if (!error || typeof error !== 'object') return undefined;
  const candidate = error as { statusCode?: unknown; response?: { status?: unknown } };
  if (typeof candidate.statusCode === 'number') return candidate.statusCode;
  return typeof candidate.response?.status === 'number' ? candidate.response.status : undefined;
}

function isNetworkFailure(error: unknown): boolean {
  if (!error || typeof error !== 'object') return true;
  const candidate = error as { type?: unknown; statusCode?: unknown };
  return candidate.type === 'NETWORK_ERROR' || typeof candidate.statusCode !== 'number';
}

function errorMessage(error: unknown): string {
  if (error instanceof Error) return error.message.slice(0, 300);
  return 'Offline mutation replay failed';
}

async function saveRecordUpdate(record: OfflineMutation, updates: Partial<OfflineMutation>): Promise<void> {
  const records = await readRecords();
  const index = records.findIndex((candidate) => candidate.id === record.id);
  if (index === -1) return;
  records[index] = { ...records[index], ...updates };
  await writeRecords(records);
}

export async function flushOfflineQueue(options: { retryFailed?: boolean; force?: boolean } = {}): Promise<OfflineFlushResult> {
  if (flushPromise) return flushPromise;
  flushPromise = (async (): Promise<OfflineFlushResult> => {
    if (!replayHandler) {
      const records = await readRecords();
      return { processed: 0, remaining: records.filter((record) => record.status === 'pending').length, failed: records.filter((record) => record.status === 'failed').length };
    }

    let processed = 0;
    const records = await readRecords();
    if (options.retryFailed) {
      for (const record of records.filter((candidate) => candidate.status === 'failed')) {
        await saveRecordUpdate(record, { status: 'pending', nextAttemptAt: Date.now(), lastError: undefined });
      }
    }

    const pending = (await readRecords()).filter(
      (record) => record.status === 'pending' && (options.force || record.nextAttemptAt <= Date.now())
    );
    for (const record of pending) {
      try {
        await replayHandler(record);
        const latest = await readRecords();
        await writeRecords(latest.filter((candidate) => candidate.id !== record.id));
        processed++;
        notify('synced');
      } catch (error) {
        const status = getStatus(error);
        const attempts = record.attempts + 1;
        if (status === 401) {
          await saveRecordUpdate(record, {
            attempts,
            lastError: 'Authentication required before offline sync can continue',
            nextAttemptAt: Date.now() + 60_000,
          });
          break;
        }
        if (isNetworkFailure(error) || status === 408 || status === 429 || (status !== undefined && status >= 500)) {
          await saveRecordUpdate(record, {
            attempts,
            lastError: errorMessage(error),
            nextAttemptAt: Date.now() + Math.min(60_000, 1000 * 2 ** Math.min(attempts, 6)),
          });
          break;
        }
        await saveRecordUpdate(record, {
          attempts,
          status: 'failed',
          lastError: errorMessage(error),
          nextAttemptAt: Number.MAX_SAFE_INTEGER,
        });
        notify('failed');
      }
    }

    const finalRecords = await readRecords();
    return {
      processed,
      remaining: finalRecords.filter((record) => record.status === 'pending').length,
      failed: finalRecords.filter((record) => record.status === 'failed').length,
    };
  })().finally(() => {
    flushPromise = null;
  });
  return flushPromise;
}

export async function clearOfflineQueue(): Promise<void> {
  await writeRecords([]);
  notify();
}
