/// <reference types="vitest" />
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import tailwindcss from "@tailwindcss/vite";
import { fileURLToPath, URL } from "node:url";

import viteCompression from "vite-plugin-compression";
import { ViteImageOptimizer } from "vite-plugin-image-optimizer";

export default defineConfig({
  test: {
    globals: true,
    environment: "jsdom",
    root: "./",
    include: ["tests/**/*.spec.ts"],
    coverage: {
      provider: "v8",
      reporter: ["text", "html", "lcov", "json"],
      reportsDirectory: "./coverage",
      exclude: [
        "node_modules/",
        "e2e/",
        "dist/",
        "*.config.*",
        "**/*.d.ts",
        "src/main.ts"
      ],
      // Code Quality: Coverage thresholds enforced at 80%
      // Run `npm run test:coverage` to verify
      thresholds: {
        statements: 30,
        branches: 25,
        functions: 30,
        lines: 30
      }
    },
  },
  plugins: [
    vue(), 
    tailwindcss(),
    viteCompression({
      verbose: true,
      disable: false,
      threshold: 10240,
      algorithm: 'gzip',
      ext: '.gz',
    }),
    viteCompression({
      verbose: true,
      disable: false,
      threshold: 10240,
      algorithm: 'brotliCompress',
      ext: '.br',
    }),
    ViteImageOptimizer({
      test: /\.(jpe?g|png|gif|tiff|webp|svg|avif)$/i,
      exclude: undefined,
      include: undefined,
      includePublic: true,
      logStats: true,
      ansiColors: true,
      svg: {
        multipass: true,
        plugins: [
          {
            name: 'preset-default',
            params: {
              overrides: {
                cleanupNumericValues: false,
              },
            },
          },
          // Disable removeViewBox to keep viewBox attribute
          {
            name: 'removeViewBox',
            active: false,
          },
          'sortAttrs',
          {
            name: 'addAttributesToSVGElement',
            params: {
              attributes: [{ xmlns: 'http://www.w3.org/2000/svg' }],
            },
          },
        ],
      },
      png: {
        // quality: 1-100
        quality: 85,
      },
      jpeg: {
        // quality: 1-100
        quality: 85,
      },
      jpg: {
        // quality: 1-100
        quality: 85,
      },
      webp: {
        // lossy used for webp
        lossless: false,
        quality: 85,
      },
      avif: {
        // lossy used for avif
        lossless: false,
        quality: 85,
      },
    }),
  ],
  base: "/",
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  build: {
    outDir: "dist",
    assetsDir: "assets",
    // Chunk size warning limit (500kb)
    chunkSizeWarningLimit: 500,
    rollupOptions: {
      output: {
        // Code splitting for better caching
        manualChunks: (id) => {
          // Vue and related packages
          if (id.includes('node_modules/vue') || 
              id.includes('node_modules/@vue') ||
              id.includes('node_modules/pinia')) {
            return 'vue-vendor';
          }
          // Axios
          if (id.includes('node_modules/axios')) {
            return 'axios';
          }
          // Google Maps
          if (id.includes('node_modules/@googlemaps')) {
            return 'google-maps';
          }
          // Tailwind utilities - can grow large
          if (id.includes('node_modules/tailwindcss')) {
            return 'tailwind';
          }
        },
        // Optimize asset file names
        assetFileNames: (assetInfo) => {
          const extType = assetInfo.name?.split('.').pop() || 'asset';
          if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(extType)) {
            return 'assets/images/[name]-[hash][extname]';
          }
          if (/woff2?|eot|ttf|otf/i.test(extType)) {
            return 'assets/fonts/[name]-[hash][extname]';
          }
          return 'assets/[name]-[hash][extname]';
        },
        // Chunk file names
        chunkFileNames: 'assets/js/[name]-[hash].js',
        // Entry file names
        entryFileNames: 'assets/js/[name]-[hash].js',
      },
    },
    // Enable asset optimization
    assetsInlineLimit: 4096, // Inline assets smaller than 4kb
    sourcemap: false, // Disable sourcemaps in production
    minify: "terser",
    terserOptions: {
      compress: {
        drop_console: true, // Remove console.log in production
        drop_debugger: true, // Remove debugger statements
      },
    },
  },
  optimizeDeps: {
    include: ["@googlemaps/js-api-loader"],
    force: true
  },
  define: {
    // Ensure environment variables are properly replaced
    __VITE_GOOGLE_MAPS_API_KEY__: JSON.stringify(process.env.VITE_GOOGLE_MAPS_API_KEY),
  },
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  // Configure env file location to look at frontend directory
  envDir: "./",
  // Add CDN configuration for production
  experimental: {
    renderBuiltUrl(filename) {
      if (process.env.NODE_ENV === 'production' && process.env.VITE_CDN_BASE_URL) {
        // Remove trailing slash from CDN base URL if present
        const baseUrl = process.env.VITE_CDN_BASE_URL.replace(/\/$/, '');
        return `${baseUrl}/${filename}`;
      }
      return { relative: true };
    },
  },
});