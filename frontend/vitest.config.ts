/// <reference types="vitest" />
import { defineConfig } from 'vitest/config';
import vue from '@vitejs/plugin-vue';
import { fileURLToPath, URL } from 'node:url';

export default defineConfig({
  plugins: [vue()],
  resolve: {
    preserveSymlinks: true,
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
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
        'src/utils/imageWorker.ts',
        'src/utils/imageUtils.ts',
        'src/utils/api.ts',
        'src/theme/mapStyles.ts',
        'src/composables/useMapMarkers.ts',
        'src/components/ui/OptimizedImage.vue',
        'src/components/ui/ReportModal.vue',
        'src/components/ui/PasswordStrengthMeter.vue',
        'src/components/ui/EmailVerificationRequiredModal.vue',
        'src/components/ui/BaseInput.vue',
        'src/components/ui/index.ts',
        'src/components/map/',
        'src/components/social/LikeButton.vue',
        'src/store/toast.ts',
        'src/views/MapView.vue',
        'src/views/GalleryView.vue',
        'src/views/ProfileView.vue',
        'src/views/admin/AdminReports.vue',
      ],
      thresholds: {
        statements: 70,
        branches: 70,
        functions: 70,
        lines: 70,
      },
    },
  },
});
