import { createApp } from 'vue'
import './styles/main.css'
import App from './App.vue'
import router from './router'
import { pinia } from './store'
import { useAuthStore } from './store/authStore'
import { isDev } from './utils/env'
import {
  handleUnhandledRejection,
  handleError,
  handleVueError
} from './utils/browserExtensionHandler'

const app = createApp(App)

// Install Pinia BEFORE using any stores
app.use(pinia)

// Initialize auth state (now using Pinia store internally)
// Initialize auth by creating the store instance
useAuthStore()


// Handle browser extension conflicts globally
window.addEventListener('unhandledrejection', handleUnhandledRejection);

window.addEventListener('error', handleError);

// Global error handler for browser extension conflicts
app.config.errorHandler = (err, instance, info) => {
  const result = handleVueError(err, info);
  
  // If handleVueError returned false, it means the error was handled
  if (result === false) {
    return;
  }
  
  // Log other errors normally
  if (isDev()) {
    console.error('Vue error:', err, info);
  }
};

app.use(router)
app.mount('#app')