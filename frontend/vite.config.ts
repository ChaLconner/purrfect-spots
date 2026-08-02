/// <reference types="vitest" />
import { defineConfig } from 'vitest/config';
import vue from '@vitejs/plugin-vue';
import { fileURLToPath, URL } from 'node:url';

export default defineConfig(async ({ mode }) => {
  const isTest = mode === 'test' || process.env.VITEST === 'true';
  const plugins = [vue()];

  const normalizeModuleId = (id: string): string => id.replace(/\\/g, '/');
  const matchesNodeModulePackage = (id: string, packageName: string): boolean => {
    const normalizedId = normalizeModuleId(id);
    return (
      normalizedId.includes(`/node_modules/${packageName}/`) ||
      normalizedId.endsWith(`/node_modules/${packageName}`)
    );
  };
  const matchesAnyPackage = (id: string, packageNames: string[]): boolean =>
    packageNames.some((packageName) => matchesNodeModulePackage(id, packageName));

  if (!isTest) {
    const { default: tailwindcss } = await import('@tailwindcss/vite');
    const { default: viteCompression } = await import('vite-plugin-compression');
    const { ViteImageOptimizer } = await import('vite-plugin-image-optimizer');

    plugins.push(
      tailwindcss(),
      viteCompression({
        verbose: true,
        disable: false,
        threshold: 10240,
        algorithm: 'gzip',
        ext: '.gz',
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
    );
  }

  return {
    test: {
      globals: true,
      environment: 'jsdom',
      env: {
        VITE_SUPABASE_URL: 'http://localhost:54321',
        VITE_SUPABASE_ANON_KEY: 'test-anon-key',
      },
      root: './',
      include: ['tests/**/*.spec.ts'],
      setupFiles: ['./tests/setup.ts'],
      server: {
        deps: {
          inline: ['@vue/test-utils'],
        },
      },
      coverage: {
        provider: 'v8',
        reporter: ['text', 'html', 'lcov', 'json'],
        reportsDirectory: './coverage',
        exclude: [
          'node_modules/',
          'e2e/',
          'dist/',
          '*.config.*',
          '**/*.d.ts',
          'src/main.ts',
          'src/theme/mapStyles.ts',
          'src/components/ui/index.ts',
        ],
        // Code Quality: Coverage thresholds (Phase 1: 50%)
        // Run `npm run test:coverage` to verify
        thresholds: {
          statements: 70,
          branches: 55,
          functions: 70,
          lines: 70,
        },
      },
    },
    plugins,
    base: '/',
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
      dedupe: [
        'vue',
        'vue-router',
        'pinia',
        '@vue/runtime-core',
        '@vue/runtime-dom',
        '@vue/reactivity',
        '@vue/shared',
      ],
    },
    optimizeDeps: {
      include: [
        'vue',
        'vue-router',
        'pinia',
        '@vue/runtime-core',
        '@vue/runtime-dom',
        '@vue/reactivity',
        '@vue/shared',
      ],
    },
    build: {
      outDir: 'dist',
      assetsDir: 'assets',
      modulePreload: {
        // Keep large Supabase SDK out of the first navigation's preload set;
        // route/auth code requests it when actually used.
        resolveDependencies: (_filename, deps) => deps.filter((dep) => !dep.includes('supabase-')),
      },
      // Keep per-chunk warnings useful; initial entry budget is enforced in CI.
      chunkSizeWarningLimit: 250,
      cssCodeSplit: true,
      manifest: true,
      reportCompressedSize: false,
      rollupOptions: {
        output: {
          manualChunks: (id) => {
            const normalizedId = normalizeModuleId(id);

            if (
              matchesAnyPackage(normalizedId, [
                'vue',
                '@vue/runtime-core',
                '@vue/runtime-dom',
                '@vue/reactivity',
                '@vue/shared',
                'vue-router',
                'pinia',
              ])
            ) {
              return 'vue-vendor';
            }
            if (matchesAnyPackage(normalizedId, ['@sentry/vue', '@sentry/core', '@sentry/browser'])) {
              return 'sentry';
            }
            if (matchesNodeModulePackage(normalizedId, '@googlemaps')) {
              return 'google-maps';
            }
            if (matchesNodeModulePackage(normalizedId, '@supabase')) {
              return 'supabase';
            }
            if (matchesAnyPackage(normalizedId, ['lucide-vue-next'])) {
              return 'icons-vendor';
            }
          },
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
          chunkFileNames: 'assets/js/[name]-[hash].js',
          entryFileNames: 'assets/js/[name]-[hash].js',
        },
      },
      assetsInlineLimit: 2048,
      sourcemap: false,
      minify: 'esbuild',
    },
    esbuild: {
      legalComments: 'none',
    },
    define: {
      __VITE_GOOGLE_MAPS_API_KEY__: JSON.stringify(process.env.VITE_GOOGLE_MAPS_API_KEY),
    },
    server: {
      proxy: {
        '/api': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true,
        },
      },
    },
    envDir: './',
  };
});
