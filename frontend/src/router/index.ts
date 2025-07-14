import { createRouter, createWebHistory } from 'vue-router'
import Map from '../components/Map.vue'
import Upload from '../components/Upload.vue'
import Gallery from '../components/Gallery.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Map
  },
  {
    path: '/upload',
    name: 'Upload', 
    component: Upload
  },
  {
    path: '/gallery',
    name: 'Gallery',
    component: Gallery
  },
  {
    path: '/auth/callback',
    name: 'AuthCallback',
    component: Map, // Redirect to home after auth
    meta: { isAuthCallback: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
