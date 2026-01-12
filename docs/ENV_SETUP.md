# Environment Variables Setup Guide

This guide explains how to configure environment variables for the **Purrfect Spots** project.

## 📁 File Structure

```
purrfect-spots/
├── .env.example                 # Master template (all variables)
├── ENV_SETUP.md                 # This file
│
├── backend/
│   ├── .env                     # Backend secrets (gitignored)
│   └── .env.example             # Backend template
│
└── frontend/
    ├── .env                     # Base config (gitignored)
    ├── .env.local               # Local overrides (gitignored)
    ├── .env.development         # Dev settings (gitignored)
    ├── .env.production          # Prod settings (gitignored)
    └── .env.example             # Frontend template
```

## 🔄 Loading Order

### Frontend (Vite)

Vite loads environment files in the following order. **Later files override earlier ones**:

| Priority | File                    | Description                    |
|----------|-------------------------|--------------------------------|
| 1        | `.env`                  | Base configuration             |
| 2        | `.env.local`            | Local overrides (all modes)    |
| 3        | `.env.[mode]`           | Mode-specific (development/production) |
| 4        | `.env.[mode].local`     | Mode-specific local overrides  |

> **Note**: Frontend variables must be prefixed with `VITE_` to be exposed to the client.

### Backend (Python)

The backend loads a single `.env` file. Use different values for development vs production by:
1. Using separate `.env` files per environment, OR
2. Setting environment variables directly in your hosting platform (recommended for production)

---

## ⚡ Quick Setup

### Development Setup

1. **Frontend**:
   ```bash
   cd frontend
   cp .env.example .env
   # Edit .env with your development values
   ```

2. **Backend**:
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env with your development values
   ```

### Production Setup (Vercel)

For Vercel deployments, set environment variables in the Vercel Dashboard:

1. Go to Project Settings → Environment Variables
2. Add each variable from `.env.example`
3. Use production values (production URLs, disable debug mode, etc.)

---

## 🔧 Required Variables

### Frontend Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_GOOGLE_CLIENT_ID` | Google OAuth Client ID | `xxx.apps.googleusercontent.com` |
| `VITE_API_BASE_URL` | Backend API URL | `http://localhost:8000` (dev) |
| `VITE_GOOGLE_MAPS_API_KEY` | Google Maps API Key | `AIza...` |

### Backend Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID | `xxx.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | Google OAuth Secret | `GOCSPX-...` |
| `JWT_SECRET` | JWT signing key | Random 256-bit string |
| `SUPABASE_URL` | Supabase project URL | `https://xxx.supabase.co` |
| `SUPABASE_KEY` | Supabase anon key | `eyJ...` |
| `DATABASE_URL` | PostgreSQL connection | `postgresql://user:pass@host/db` |
| `CORS_ORIGINS` | Allowed frontend origins | `http://localhost:5173` |

---

## 🔐 Security Best Practices

1. **Never commit `.env` files** - They are gitignored by default
2. **Use different credentials** for development and production
3. **Rotate secrets regularly** - Especially after any potential exposure
4. **Restrict API keys** - Limit to specific domains/IPs when possible
5. **Use HTTPS** in production
6. **Generate strong secrets**:
   ```bash
   # Generate a secure JWT_SECRET
   openssl rand -hex 32
   ```

---

## 🌍 Environment-Specific Configuration

### Development
```env
# Backend
DEBUG=True
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Frontend
VITE_API_BASE_URL=http://localhost:8000
VITE_DEBUG_MODE=true
```

### Production
```env
# Backend
DEBUG=False
ENVIRONMENT=production
CORS_ORIGINS=https://purrfect-spots.vercel.app

# Frontend
VITE_API_BASE_URL=https://purrfect-spots-backend.vercel.app
VITE_DEBUG_MODE=false
```

---

## ❓ Troubleshooting

### Frontend variables not loading?
- Ensure variables are prefixed with `VITE_`
- Restart the dev server after changing `.env` files
- Check file naming (e.g., `.env.development` not `.env.dev`)

### Backend can't find variables?
- Check the `.env` file is in the `backend/` directory
- Ensure `python-dotenv` is installed
- Verify no syntax errors in the `.env` file

### CORS errors?
- Add your frontend URL to `CORS_ORIGINS` in backend `.env`
- Ensure URLs don't have trailing slashes
