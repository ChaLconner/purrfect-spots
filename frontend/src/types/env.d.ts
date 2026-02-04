/// <reference types="vite/client" />

declare global {
  interface ImportMetaEnv {
    readonly VITE_GOOGLE_CLIENT_ID: string;
    readonly VITE_GOOGLE_CLIENT_ID_SECRET: string;
    readonly VITE_API_BASE_URL: string;
    readonly VITE_GOOGLE_MAPS_API_KEY: string;
    readonly VITE_CDN_BASE_URL: string;
    readonly VITE_MAX_IMAGE_WIDTH: string;
    readonly VITE_MAX_IMAGE_HEIGHT: string;
    readonly VITE_IMAGE_QUALITY: string;
    readonly VITE_MAX_FILE_SIZE: string;
    readonly NODE_ENV: string;
    readonly MODE: string;
    readonly DEV: boolean;
    readonly PROD: boolean;
  }

  interface ImportMeta {
    readonly env: ImportMetaEnv;
  }
}

export {};
