# 🐱 Purrfect Spots

An application for cat lovers who want to share suitable places to take cats, with an automatic cat detection system using AI.

## ✨ Key Features

- 📸 **Upload Cat Photos** - Share cat photos you've found
- 🗺️ **Interactive Map** - View cat locations in real-time on Google Maps
- 🤖 **AI Cat Detection** - Use Google Vision API to confirm that the photo contains real cats
- 🖼️ **Beautiful Gallery** - View all cat photos in gallery format
- 🔐 **Authentication** - Support login with Google OAuth
- 📱 **Responsive Design** - Works on both mobile and desktop
- 🌏 **Multi-language** - Full language support

## 🛠️ Technologies Used

### Frontend
- **Vue.js 3** - JavaScript framework
- **TypeScript** - Type-safe JavaScript
- **Vite** - High-speed build tool
- **Pinia** - State Management
- **Vue Router** - Application navigation
- **Tailwind CSS** - Styling framework
- **Google Maps API** - Interactive maps

### Backend
- **FastAPI** - Python web framework
- **Supabase** - Database and Authentication
- **AWS S3** - Image storage
- **Google Vision API** - AI cat detection
- **Google OAuth** - Authentication
- **JWT** - Token-based authentication

## 🚀 Installation and Setup

### 1. Environment Setup

Please follow the detailed guide in [docs/ENV_SETUP.md](./docs/ENV_SETUP.md) to configure environment variables for both Frontend and Backend.

**Summary:**
- **Frontend**: Copy `frontend/.env.example` to `frontend/.env`
- **Backend**: Copy `backend/.env.example` to `backend/.env`

### 2. Install and run Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

The server will run at http://localhost:8000

### 3. Install and run Frontend

```bash
cd frontend
npm install
npm run dev
```

The application will run at http://localhost:5173

## 📁 Project Structure

```
purrfect-spots/
├── docs/                  # Documentation and Guides
├── backend/               # FastAPI backend
│   ├── main.py            # Main FastAPI application file
│   ├── routes/            # API routes
│   ├── services/          # Business logic
│   ├── schemas/           # Pydantic models
│   ├── custom_middleware/ # Middleware
│   ├── keys/              # Service account keys
│   └── requirements.txt   # Python dependencies
├── frontend/              # Vue.js frontend
│   ├── src/
│   │   ├── components/    # Vue components
│   │   ├── views/         # Page views
│   │   ├── services/      # API services
│   │   ├── store/         # Pinia state
│   │   ├── router/        # Vue Router
│   │   └── composables/   # Vue Composables
│   └── package.json       # Frontend dependencies
├── PROJECT_REVIEW.md      # Project status and review
└── README.md              # This file
```

## 🔗 Main API Endpoints

### Authentication
- `POST /api/auth/google` - Google OAuth login
- `POST /api/auth/refresh` - Refresh token
- `GET /api/users/me` - User profile

### Upload and Cat Detection
- `POST /api/upload/presigned-url` - Get S3 upload URL
- `POST /api/detect` - Detect cat in image

### Data
- `GET /api/images` - Gallery images
- `GET /api/locations` - Map locations

## 📚 Documentation

Detailed documentation can be found in the `docs/` folder:

- [Environment Setup](./docs/ENV_SETUP.md)
- [Database Schema](./docs/DATABASE_SCHEMA.md)
- [Deployment Secrets](./docs/DEPLOYMENT_SECRETS_SETUP.md)
- [Runbook](./docs/RUNBOOK.md)

Also check sub-project READMEs:
- [Backend README](./backend/README.md)
- [Frontend README](./frontend/README.md)

## 🌐 Deployment

### Frontend (Vercel)
```bash
cd frontend
npm run build
npm run deploy
```

### Backend (Vercel/Cloud)
See `docs/PRODUCTION_SETUP.md` for details.

## 🤝 Support

If you have problems:
1. Check `docs/ENV_SETUP.md` for configuration.
2. Verify API keys in `backend/.env` and `frontend/.env`.
3. Check `backend/README_API.md` for specific API details.

---

Made with ❤️ for all cat lovers 🐱