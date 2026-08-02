import { z } from 'zod';

const optionalString = z.string().optional();
const optionalUrl = z.union([z.string().url(), z.string().regex(/^\/[^\s]*$/), z.literal('')]).optional();
const optionalNumericString = z.union([z.string().regex(/^\d+$/), z.literal('')]).optional();
const secretLikeViteVariable = /^VITE_.*(?:SECRET|PRIVATE|PASSWORD|TOKEN)$/i;

/** Public Vite variables accepted by the application at runtime. */
export const publicEnvSchema = z
  .object({
    MODE: z.string().optional(),
    VITE_API_BASE_URL: optionalUrl,
    VITE_SUPABASE_URL: z.union([z.string().url(), z.literal('')]).optional(),
    VITE_SUPABASE_ANON_KEY: optionalString,
    VITE_GOOGLE_CLIENT_ID: optionalString,
    VITE_GOOGLE_MAPS_API_KEY: optionalString,
    VITE_CDN_BASE_URL: z.union([z.string().url(), z.literal('')]).optional(),
    VITE_SENTRY_DSN: optionalUrl,
    VITE_MAX_FILE_SIZE: optionalNumericString,
    VITE_MAX_IMAGE_WIDTH: optionalNumericString,
    VITE_MAX_IMAGE_HEIGHT: optionalNumericString,
    VITE_IMAGE_QUALITY: optionalNumericString,
    VITE_ENABLE_SENTRY: z.enum(['true', 'false', '']).optional(),
    VITE_SENTRY_REPLAY_ENABLED: z.enum(['true', 'false', '']).optional(),
  })
  .passthrough()
  .superRefine((env, context) => {
    for (const key of Object.keys(env)) {
      if (secretLikeViteVariable.test(key)) {
        context.addIssue({
          code: 'custom',
          path: [key],
          message: `${key} must not be exposed through Vite`,
        });
      }
    }

    if (env.MODE !== 'production') return;

    for (const key of ['VITE_SUPABASE_URL', 'VITE_SUPABASE_ANON_KEY'] as const) {
      if (!env[key]) {
        context.addIssue({
          code: 'custom',
          path: [key],
          message: `${key} is required in production`,
        });
      }
    }
  });

type RawEnv = Record<string, unknown>;

// Keep this object explicit. Referencing the complete import.meta.env object
// would let Vite inline unknown VITE_* values, including accidental secrets.
const runtimeEnv: RawEnv = {
  MODE: import.meta.env.MODE,
  VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
  VITE_SUPABASE_URL: import.meta.env.VITE_SUPABASE_URL,
  VITE_SUPABASE_ANON_KEY: import.meta.env.VITE_SUPABASE_ANON_KEY,
  VITE_GOOGLE_CLIENT_ID: import.meta.env.VITE_GOOGLE_CLIENT_ID,
  VITE_GOOGLE_MAPS_API_KEY: import.meta.env.VITE_GOOGLE_MAPS_API_KEY,
  VITE_CDN_BASE_URL: import.meta.env.VITE_CDN_BASE_URL,
  VITE_SENTRY_DSN: import.meta.env.VITE_SENTRY_DSN,
  VITE_MAX_FILE_SIZE: import.meta.env.VITE_MAX_FILE_SIZE,
  VITE_MAX_IMAGE_WIDTH: import.meta.env.VITE_MAX_IMAGE_WIDTH,
  VITE_MAX_IMAGE_HEIGHT: import.meta.env.VITE_MAX_IMAGE_HEIGHT,
  VITE_IMAGE_QUALITY: import.meta.env.VITE_IMAGE_QUALITY,
  VITE_ENABLE_SENTRY: import.meta.env.VITE_ENABLE_SENTRY,
  VITE_SENTRY_REPLAY_ENABLED: import.meta.env.VITE_SENTRY_REPLAY_ENABLED,
};

/** Validate public runtime configuration without logging secret values. */
export const validateEnv = (rawEnv: RawEnv): RawEnv => {
  const result = publicEnvSchema.safeParse(rawEnv);
  if (result.success) return result.data;

  const invalidKeys = [...new Set(result.error.issues.map((issue) => issue.path.join('.')))].join(', ');
  const message = `Invalid frontend environment variables: ${invalidKeys}`;
  if (rawEnv.MODE === 'production') throw new Error(message);

  console.warn(message);
  return Object.fromEntries(Object.entries(rawEnv).filter(([key]) => !secretLikeViteVariable.test(key)));
};

const validatedEnv = validateEnv(runtimeEnv);

/**
 * Get an environment variable after runtime validation.
 */
export const getEnvVar = (key: string, defaultValue = ''): string => {
  const value = validatedEnv[key];
  return typeof value === 'string' && value.length > 0 ? value : defaultValue;
};

export const isDev = (): boolean => {
  return import.meta.env.DEV === true || import.meta.env.MODE === 'development';
};

export const isProd = (): boolean => {
  return import.meta.env.PROD === true || import.meta.env.MODE === 'production';
};
