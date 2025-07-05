import { createApp } from 'vue'
import './style.css'
import 'leaflet/dist/leaflet.css'
import App from './App.vue'
import router from './router'
import { LMap, LTileLayer, LMarker } from '@vue-leaflet/vue-leaflet'

const app = createApp(App)
app.component('l-map', LMap)
app.component('l-tile-layer', LTileLayer)
app.component('l-marker', LMarker)
app.use(router)
app.mount('#app')
