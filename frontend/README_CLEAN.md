# PurrfectSpots Frontend

Vue.js frontend application for PurrfectSpots - A cat spotting and sharing platform.

## Features

- **Vue 3** with Composition API
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **Vue Router** for navigation
- **Google OAuth 2.0** authentication
- **Interactive Maps** with Leaflet
- **Image Upload** and gallery
- **Responsive Design** for mobile and desktop

## Quick Start

### Prerequisites

- Node.js 18+ and npm
- Modern web browser

### Installation

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your configuration:
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   VITE_GOOGLE_CLIENT_ID=your_google_client_id
   ```

4. **Start development server:**
   ```bash
   npm run dev
   ```

The application will be available at `http://localhost:5173`

## Project Structure

```
frontend/
├── src/
│   ├── components/          # Vue components
│   ├── composables/         # Vue composables
│   ├── router/              # Vue Router configuration
│   ├── services/            # API services
│   ├── store/               # State management
│   ├── types/               # TypeScript definitions
│   └── views/               # Page components
├── public/                  # Static assets
└── package.json             # Dependencies and scripts
```

## Development

```bash
npm run dev        # Start development server
npm run build      # Build for production
npm run preview    # Preview production build
npm run type-check # TypeScript type checking
```
