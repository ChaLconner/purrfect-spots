import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router'
import { initializeAuth } from './store/auth'
import { isDev } from './utils/env'
import {
  handleUnhandledRejection,
  handleError,
  handleVueError
} from './utils/browserExtensionHandler'

// Initialize auth state
initializeAuth()


// Handle browser extension conflicts globally
window.addEventListener('unhandledrejection', handleUnhandledRejection);

window.addEventListener('error', handleError);

const app = createApp(App)

// Global error handler for browser extension conflicts
app.config.errorHandler = (err, instance, info) => {
  const result = handleVueError(err, instance, info);
  
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