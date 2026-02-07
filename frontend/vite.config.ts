/// <reference types="vitest" />
import { defineConfig } from "vitest/config";
import vue from "@vitejs/plugin-vue";
import tailwindcss from "@tailwindcss/vite";
import { fileURLToPath, URL } from "node:url";

import viteCompression from "vite-plugin-compression";
import { ViteImageOptimizer } from "vite-plugin-image-optimizer";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  test: {
    globals: true,
    environment: "jsdom",
    root: "./",
    include: ["tests/**/*.spec.ts"],
    setupFiles: ["./tests/setup.ts"],
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
      // Code Quality: Coverage thresholds (Phase 1: 50%)
      // Run `npm run test:coverage` to verify
      thresholds: {
        statements: 50,
        branches: 40,
        functions: 50,
        lines: 50
      }
    },
  },
  plugins: [
    vue(), 
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['cat-icon.png', 'default-avatar.svg'],
      manifest: {
        name: 'Purrfect Spots',
        short_name: 'PurrfectSpots',
        description: 'Discover and share cat-friendly locations with AI-powered cat detection',
        theme_color: '#6b8e7d',
        background_color: '#ffffff',
        display: 'standalone',
        orientation: 'portrait',
        icons: [
          {
            src: 'cat-icon.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: 'cat-icon.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ]
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}']
      }
    }),
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
});