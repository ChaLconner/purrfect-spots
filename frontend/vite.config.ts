import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  base: "/",
  build: {
    outDir: "dist",
    assetsDir: "assets",
    rollupOptions: {
      output: {
        manualChunks: undefined,
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
    renderBuiltUrl(filename, { hostType }) {
      if (hostType === 'js' || hostType === 'css') {
        // For JS and CSS files, use relative paths
        return { relative: true };
      } else {
        // For other assets (images, fonts), use CDN in production
        if (process.env.NODE_ENV === 'production' && process.env.VITE_CDN_BASE_URL) {
          return {
            // Use CDN URL for assets
            js: `${process.env.VITE_CDN_BASE_URL}/${filename}`,
            css: `${process.env.VITE_CDN_BASE_URL}/${filename}`,
            asset: `${process.env.VITE_CDN_BASE_URL}/${filename}`,
          };
        }
        return { relative: true };
      }
    },
  },
});