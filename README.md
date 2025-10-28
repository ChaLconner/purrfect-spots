# 🐱 Purrfect Spots

An application for cat lovers who want to share suitable places to take cats, with an automatic cat detection system using AI

## ✨ Key Features

- 📸 **Upload Cat Photos** - Share cat photos you've found
- 🗺️ **Interactive Map** - View cat locations in real-time on Google Maps
- 🤖 **AI Cat Detection** - Use Google Vision API to confirm that the photo contains real cats
- 🖼️ **Beautiful Gallery** - View all cat photos in gallery format
- 🔐 **Authentication** - Support login with Google OAuth and email/password
- 📱 **Responsive Design** - Works on both mobile and desktop
- 🌏 **Multi-language** - Full language support

## 🛠️ Technologies Used

### Frontend
- **Vue.js 3** - JavaScript framework
- **TypeScript** - Type-safe JavaScript
- **Vite** - High-speed build tool
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

### 1. Copy environment variables file

```bash
# Copy .env.example file to .env at project root
cp .env.example .env
```

### 2. Edit the .env file

Edit the information in the `.env` file at the project root:

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_REGION=ap-southeast-2
AWS_S3_BUCKET=your_s3_bucket_name

# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret
VITE_GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com

# JWT Configuration
JWT_SECRET=your_jwt_secret_key_here

# Google APIs Configuration
VITE_GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
GOOGLE_VISION_KEY_PATH=keys/google_vision.json

# API Configuration
VITE_API_BASE_URL=http://localhost:8000  # or production URL
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 3. Install and run Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

The server will run at http://localhost:8000

### 4. Install and run Frontend

```bash
cd frontend
npm install
npm run dev
```

The application will run at http://localhost:5173

## 📁 Project Structure

```
purrfect-spots/
├── .env                    # Combined environment variables file (frontend + backend)
├── .env.example           # Example environment variables file
├── backend/               # FastAPI backend
│   ├── main.py            # Main FastAPI application file
│   ├── dependencies.py    # Dependencies for FastAPI
│   ├── routes/            # API routes
│   │   ├── auth_google.py # Google OAuth
│   │   ├── auth_manual.py # Manual authentication
│   │   ├── upload.py      # File upload
│   │   ├── cat_detection.py # AI cat detection
│   │   └── profile.py     # User profile
│   ├── services/          # Business logic
│   ├── middleware/        # Custom middleware
│   ├── keys/              # Service account keys
│   └── requirements.txt   # Python dependencies
├── frontend/              # Vue.js frontend
│   ├── src/
│   │   ├── components/     # Vue components
│   │   ├── views/         # Page views
│   │   ├── services/      # API services
│   │   ├── store/         # State management
│   │   ├── router/        # Vue Router
│   │   ├── types/         # TypeScript types
│   │   └── utils/         # Utility functions
│   └── package.json       # Frontend dependencies
├── ENVIRONMENT_VARIABLES_GUIDE.md # Environment variables guide
└── OAUTH_SETUP_GUIDE.md   # OAuth setup guide
```

## 🔗 Main API Endpoints

### Authentication
- `POST /api/auth/google` - Google OAuth
- `POST /api/auth/register` - Register
- `POST /api/auth/login` - Login
- `GET /api/profile` - User information

### Upload and Cat Detection
- `POST /api/upload` - Upload image
- `POST /api/detect-cat` - Detect cat in image
- `GET /api/presigned-url` - Create presigned URL for upload

### Data and Gallery
- `GET /api/gallery` - View all images
- `GET /locations` - View all locations

## 📚 Beginner's Guide

### 🎯 Project Structure Management

For beginners learning project development, good folder structure management will make work easier:

#### 📁 Folder Organization Principles
1. **Separate Frontend and Backend** - Makes dependency management and work easier
2. **File Naming** - Use English and make names meaningful
3. **Environment Variables Management** - Always have a `.env.example` file as a template

#### 🗂️ Recommended Structure for Beginners
```
purrfect-spots/
├── 📄 README.md              # Project description (first file others will read)
├── 🔧 .env.example           # Example environment variables
├── 🚫 .gitignore             # Files not to upload to git
│
├── 📂 backend/               # API server
│   ├── 🐍 main.py            # Main server startup file
│   ├── 📋 requirements.txt   # Python packages to install
│   ├── 📂 routes/           # Separate API endpoints by function
│   ├── 📂 services/         # Main business logic
│   └── 📂 models/           # Data structures
│
├── 📂 frontend/              # User interface
│   ├── 📄 package.json      # Node.js dependencies
│   ├── 📂 src/
│   │   ├── 📂 components/   # Reusable Vue components
│   │   ├── 📂 views/        # Various app pages
│   │   └── 📂 services/     # API calling functions
│   └── 📂 public/           # Static files
│
└── 📂 docs/                 # Documentation (if any)
    ├── 📄 API.md
    └── 📄 DEPLOYMENT.md
```

#### 🛠️ Recommended Tools for Beginners
- **VS Code** - Popular editor with good extensions
- **Git** - Version control management
- **Postman** - Test API endpoints
- **Browser DevTools** - Debug frontend issues

#### 📝 Tips for Beginners
1. **Don't commit `.env` files** - They contain important and secret information
2. **Read error messages** - Don't be afraid of errors, they help tell you what's wrong
3. **Test one part at a time** - Don't rush to do everything at once
4. **Ask experienced people** - Asking for help is normal

#### 🔄 Professional Workflow
1. **Use Git branches** - Don't work directly on main branch
2. **Write clear commit messages**
3. **Test before deploy**
4. **Read documentation of libraries you use**

## 🔧 Additional Guides

- [Environment Variables Guide](./ENVIRONMENT_VARIABLES_GUIDE.md) - Environment variables setup guide
- [OAuth Setup Guide](./OAUTH_SETUP_GUIDE.md) - Google OAuth setup guide
- [Backend API Documentation](./backend/README_API.md) - API usage guide
- [Backend README](./backend/README.md) - Additional backend information
- [Frontend README](./frontend/README.md) - Additional frontend information

## 🚨 Important Notes

- There is now only one `.env` file at the project root
- Both frontend and backend will read environment variables from this file together
- Frontend uses only variables starting with `VITE_`
- Backend can use all variables defined in the .env file
- Must have Google Vision API key file at `backend/keys/google_vision.json`
- Must set CORS origins correctly so frontend can call backend

## 🌐 Deployment

### Frontend (Vercel)
```bash
cd frontend
npm run build
npm run deploy
```

### Backend (Vercel)
```bash
cd backend
# Add vercel.json for Vercel configuration
vercel --prod
```

## 🤝 Support

If you have problems or questions:
1. Check environment variables settings
2. Verify that API keys are correct and have sufficient permissions
3. Check console logs for errors
4. Read additional guides in various subfolders

---

Made with ❤️ for all cat lovers 🐱