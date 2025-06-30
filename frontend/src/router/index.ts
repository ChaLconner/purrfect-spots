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
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
