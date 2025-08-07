# PurrFect Spots - Deployment Guide

## 🚀 Production Deployment (Updated)

### Frontend Deployment (Vercel/Netlify)

#### Prerequisites
- Node.js 18+ installed
- Git repository connected to Vercel/Netlify

#### Environment Variables Required
```bash
VITE_GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
VITE_API_BASE_URL=https://your-backend-domain.onrender.com
```

#### Manual Deployment Steps

1. **Build the project**
   ```bash
   cd frontend
   npm ci
   npm run build:prod
   ```

2. **Deploy to Vercel**
   ```bash
   # Install Vercel CLI
   npm i -g vercel
   
   # Deploy
   vercel --prod
   ```

3. **Deploy to Netlify**
   ```bash
   # Install Netlify CLI
   npm i -g netlify-cli
   
   # Deploy
   netlify deploy --prod --dir=dist
   ```

#### Automated Deployment
```bash
cd frontend
chmod +x deploy.sh
./deploy.sh
```

### Backend Deployment (Render)

#### Environment Variables Required
```bash
# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret

# JWT
JWT_SECRET=your_jwt_secret_key

# Google AI
GOOGLE_AI_API_KEY=your_google_ai_api_key

# AWS S3
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=ap-southeast-1
AWS_S3_BUCKET=your_s3_bucket_name

# CORS (optional)
CORS_ORIGINS=https://your-frontend-domain.vercel.app

# Application
DEBUG=False
PORT=8000
```

#### Deploy to Render
1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Use these settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Python 3.11

## 🔧 Troubleshooting

### Common Issues

1. **CORS Errors**
   - Make sure `CORS_ORIGINS` includes your frontend domain
   - Check that frontend uses correct API URL

2. **Environment Variables Not Loading**
   - Verify `.env.production` exists and has correct values
   - Check Vercel/Netlify environment variable settings

3. **API Connection Issues**
   - Verify backend is deployed and accessible
   - Check `VITE_API_BASE_URL` points to correct backend URL
   - Test API endpoints manually

4. **Build Failures**
   - Run `npm run type-check` to find TypeScript errors
   - Check for missing dependencies with `npm ci`

### Health Check URLs
- **Backend**: `https://your-backend.onrender.com/health`
- **Frontend**: `https://your-frontend.vercel.app`

## 📈 Performance Optimization

### Bundle Size Optimization
- All debug console.logs removed for production
- Tree-shaking enabled in Vite
- Code splitting for better performance

### Current Build Stats
```
dist/index.html                    0.78 kB
dist/assets/index-*.css           48.80 kB
dist/assets/index-*.js           308.61 kB (gzipped: 100.23 kB)
```

## 🔄 Code Cleanup Completed

### Frontend Optimizations Done
- ✅ Removed debug console.logs from all components
- ✅ Centralized API configuration in `/config/api.ts`
- ✅ Updated all services to use centralized API functions
- ✅ Created production environment variables
- ✅ Added deployment scripts
- ✅ Optimized bundle size (reduced from 311kB to 308kB)

### Files Cleaned
- `src/config/api.ts` - Clean, production-ready API config
- `src/services/authService.ts` - Removed debug logs, kept error handling
- `src/components/Gallery.vue` - Minimal logging, clean code
- `src/components/Map.vue` - Optimized error handling
- Removed `debug.html` development file

## 🚀 Ready for Production

The codebase is now clean and ready for production deployment with:
- Minimal logging overhead
- Consistent API URL handling
- Proper error handling without debug noise
- Optimized bundle size
- Environment-specific configurations
