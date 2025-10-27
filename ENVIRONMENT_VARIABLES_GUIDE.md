# 📝 Environment Variables Management Guide

This guide provides comprehensive instructions for managing environment variables in the Purrfect Spots project.

## 📁 File Structure

```
purrfect-spots/
├── .env.example                 # Complete example for the entire project
├── frontend/
│   ├── .env                     # Development environment variables
│   ├── .env.production          # Production environment variables
│   └── .env.example             # Frontend-specific example
└── backend/
    ├── .env                     # Backend environment variables (not in repo)
    └── .env.example             # Backend-specific example
```

## 🚀 Quick Setup

### 1. Frontend Setup

```bash
# Copy the example file for development
cp frontend/.env.example frontend/.env

# For production, create a production file
cp frontend/.env.example frontend/.env.production
```

### 2. Backend Setup

```bash
# Copy the example file
cp backend/.env.example backend/.env
```

## 🔧 Configuration Details

### Frontend Environment Variables

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `VITE_GOOGLE_CLIENT_ID` | Google OAuth client ID | Yes | `your-client-id.apps.googleusercontent.com` |
| `VITE_GOOGLE_CLIENT_ID_SECRET` | Google OAuth client secret | Yes | `your-client-secret` |
| `VITE_API_BASE_URL` | Backend API URL | Yes | `http://localhost:8000` |
| `VITE_GOOGLE_MAPS_API_KEY` | Google Maps API key | Yes | `your-maps-api-key` |
| `GOOGLE_VISION_API_KEY` | Google Vision API key | Yes | `your-vision-api-key` |
| `VITE_DEBUG_MODE` | Enable debug mode | No | `true/false` |
| `VITE_LOG_LEVEL` | Logging level | No | `debug/info/warn/error` |

### Backend Environment Variables

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | Yes | `your-client-id.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret | Yes | `your-client-secret` |
| `JWT_SECRET` | JWT signing secret | Yes | `your-jwt-secret` |
| `SUPABASE_URL` | Supabase project URL | Yes | `https://your-project.supabase.co` |
| `SUPABASE_KEY` | Supabase anon key | Yes | `your-supabase-key` |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key | Yes | `your-service-role-key` |
| `AWS_ACCESS_KEY_ID` | AWS access key | Yes | `your-aws-access-key` |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | Yes | `your-aws-secret-key` |
| `AWS_REGION` | AWS region | Yes | `ap-southeast-2` |
| `AWS_S3_BUCKET` | S3 bucket name | Yes | `your-bucket-name` |
| `GOOGLE_AI_API_KEY` | Google AI API key | Optional | `your-ai-api-key` |
| `GOOGLE_VISION_KEY_PATH` | Path to Vision API key file | Yes | `keys/google_vision.json` |
| `CORS_ORIGINS` | Allowed CORS origins | Yes | `http://localhost:3000` |
| `PORT` | Server port | No | `8000` |
| `DEBUG` | Debug mode | No | `True/False` |
| `ENVIRONMENT` | Environment type | No | `development/production` |

## 🌍 Environment-Specific Configuration

### Development Environment

```env
# frontend/.env
VITE_API_BASE_URL=http://localhost:8000
VITE_DEBUG_MODE=true
VITE_LOG_LEVEL=debug

# backend/.env
DEBUG=True
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Production Environment

```env
# frontend/.env.production
VITE_API_BASE_URL=https://purrfect-spots-backend.vercel.app
VITE_DEBUG_MODE=false
VITE_LOG_LEVEL=error

# backend/.env
DEBUG=False
ENVIRONMENT=production
CORS_ORIGINS=https://purrfect-spots.vercel.app
```

## 🔐 Security Best Practices

### 1. Never Commit Real Credentials
- Always use placeholder values in `.env.example` files
- Add `.env` files to `.gitignore`
- Never commit actual API keys or secrets

### 2. Separate Environments
- Use different credentials for development and production
- Create separate API keys with appropriate restrictions
- Use environment-specific configuration files

### 3. Key Management
- Regularly rotate API keys and secrets
- Use strong, randomly generated secrets
- Store service account files securely

### 4. Access Control
- Restrict API keys to specific domains/IPs
- Use the principle of least privilege
- Monitor API usage for unusual activity

## 🛠️ Common Tasks

### Adding a New Environment Variable

1. Add the variable to the appropriate `.env.example` file
2. Document the variable in this guide
3. Update the code to use the new variable
4. Test in both development and production

### Switching Between Environments

```bash
# Development
npm run dev

# Production build
npm run build
npm run preview
```

### Updating API Keys

1. Generate new keys from the respective service provider
2. Update the appropriate `.env` files
3. Test the application to ensure everything works
4. Delete old keys from the service provider

## 🚨 Troubleshooting

### Common Issues

1. **Variables not loading**
   - Ensure `.env` file is in the correct directory
   - Check that variables have the correct prefix (`VITE_` for frontend)
   - Restart the development server

2. **CORS errors**
   - Verify `CORS_ORIGINS` includes your frontend URL
   - Check for trailing slashes in URLs
   - Ensure backend is running with the correct environment

3. **API key errors**
   - Verify API keys are correctly copied
   - Check API key restrictions and quotas
   - Ensure API is enabled in the respective console

### Debug Mode

Enable debug mode to get more detailed error messages:

```env
# Frontend
VITE_DEBUG_MODE=true
VITE_LOG_LEVEL=debug

# Backend
DEBUG=True
```

## 📚 Additional Resources

- [Vite Environment Variables](https://vitejs.dev/guide/env-and-mode.html)
- [Google Cloud Console](https://console.cloud.google.com/)
- [AWS IAM Console](https://console.aws.amazon.com/iam/)
- [Supabase Dashboard](https://supabase.com/dashboard)

## 🔄 Regular Maintenance

- Review and rotate API keys quarterly
- Update documentation when adding new variables
- Audit environment variables for unused entries
- Check for security advisories for connected services

---

**Note**: This guide should be updated whenever new environment variables are added or the project structure changes.