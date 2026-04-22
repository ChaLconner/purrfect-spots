# 🎨 Purrfect Spots Frontend

Frontend of the cat photo sharing app - Beautiful and easy to use!

## ✨ Features

- 📱 **Responsive Design** - Works on both mobile and desktop
- 🗺️ **Interactive Map** - View cat locations in real-time
- 🖼️ **Beautiful Gallery** - View photos in modal format
- 📍 **Location Detection** - GPS support
- 🌏 **Multi-language** - Full language support
- 🤖 **AI Integration** - Display cat detection results

## 🛠️ Technologies

- **Vue.js 3** - JavaScript framework
- **TypeScript** - Type-safe JavaScript
- **Vite** - Very fast build tool
- **Pinia** - State management
- **Vue Router** - Navigation
- **Tailwind CSS** - Beautiful styling
- **Google Maps** - Interactive maps

## 🧩 Structure

- **src/components/** - Reusable components (NavBar, Gallery, Map, etc.)
- **src/views/** - Page views (Home, Upload, Profile, etc.)
- **src/services/** - API communication
- **src/store/** - State management (Pinia)
- **src/composables/** - Reusable logic (Hooks)

## 🚀 Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

## 🔗 API Integration

Connects to the FastAPI backend through the frontend's same-origin `/api` proxy in development:
- **Auth**: Google OAuth & JWT
- **Photos**: Upload and gallery listing
- **Locations**: Geolocation data
- **AI**: Cat detection results

---

Made with ❤️ and Vue.js 🐱
