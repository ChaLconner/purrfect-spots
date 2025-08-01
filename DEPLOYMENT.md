# Deployment Guide for Purrfect Spots

## Prerequisites
- Python 3.11 (recommended for deployment compatibility)
- Node.js 18+
- AWS S3 bucket
- Supabase project
- Google OAuth credentials
- Google AI Studio API key

## Backend Deployment

### 1. Environment Setup
```bash
cd backend
cp .env.production.example .env.production
# Edit .env.production with your actual values
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Backend
```bash
# Development
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn main:app --host 0.0.0.0 --port $PORT --workers 4
```

## Frontend Deployment

### 1. Environment Setup
```bash
cd frontend
cp .env.production.example .env.production
# Edit .env.production with your actual values
```

### 2. Install Dependencies
```bash
npm install
```

### 3. Build and Deploy
```bash
# Build for production
npm run build

# Preview build locally
npm run preview

# Deploy the dist/ folder to your web server
```

## Platform-Specific Deployment

### Vercel (Frontend)
1. Connect your GitHub repository
2. Set environment variables in Vercel dashboard
3. Deploy automatically from main branch

### Render (Backend)
1. Connect your GitHub repository
2. Set environment variables in Render dashboard
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Python version will be automatically detected from `runtime.txt`
6. Alternative: Use `render.yaml` for Infrastructure as Code

### Railway (Backend)
1. Connect your GitHub repository
2. Set environment variables in Railway dashboard
3. Use start command from `Procfile`

### AWS EC2
1. Install Python 3.11 and Node.js
2. Clone repository
3. Set up environment variables
4. Use PM2 or systemd for process management
5. Configure nginx as reverse proxy

## Environment Variables Checklist

### Backend (.env.production)
- [ ] AWS_ACCESS_KEY_ID
- [ ] AWS_SECRET_ACCESS_KEY
- [ ] AWS_REGION
- [ ] AWS_S3_BUCKET
- [ ] SUPABASE_URL
- [ ] SUPABASE_SERVICE_ROLE_KEY
- [ ] GOOGLE_CLIENT_ID
- [ ] GOOGLE_CLIENT_SECRET
- [ ] JWT_SECRET
- [ ] GOOGLE_AI_API_KEY

### Frontend (.env.production)
- [ ] VITE_API_BASE_URL
- [ ] VITE_BACKEND_URL
- [ ] VITE_GOOGLE_CLIENT_ID
- [ ] VITE_SUPABASE_URL (if needed)
- [ ] VITE_SUPABASE_ANON_KEY (if needed)

## Security Notes
- Never commit .env files to git
- Use strong JWT secrets
- Ensure S3 bucket has proper CORS settings
- Set up proper CORS origins in backend
- Use HTTPS in production
