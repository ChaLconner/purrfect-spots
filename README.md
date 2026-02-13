# 🐱 Purrfect Spots

**Connect. Share. Discover.**
The ultimate platform for cat lovers to find and share the perfect spots for their furry friends.

## 🏗️ Architecture

Purrfect Spots is a full-stack application built with:

- **Frontend**: Vue 3 + Vite + TypeScript (Single Page Application)
- **Backend**: Python FastAPI (Async)
- **Database**: Supabase (PostgreSQL)
- **Storage**: AWS S3 (via Supabase Storage)
- **Caching**: Redis (Rate Limiting & Data Caching)
- **AI**: Google Vision API (Cat Detection)
- **Infrastructure**: Docker & Nginx

### Key Components

- **Authentication**: JWT-based (Supabase Auth & Custom tokens).
- **Security**: Rate limiting (Redis-backed), CSRF protection, Helmet headers, Input sanitization.
- **Observability**: Sentry (Error Tracking), Jaeger (Tracing), Structured Logging.

## 🚀 Getting Started

### Prerequisites

- Docker & Docker Compose
- Node.js 20+ (for local frontend dev)
- Python 3.12+ (for local backend dev)

### Environment Setup

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
2. Fill in the required credentials (Supabase, Google Cloud, etc.).

### Running with Docker (Recommended)

```bash
docker-compose up -d --build
```
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs (Development only)

### Local Development

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## 🧪 Testing

We use `pytest` for backend and `vitest` for frontend.

**Run Backend Tests:**
```bash
cd backend
pytest
```

**Run Frontend Tests:**
```bash
cd frontend
npm run test:unit
```

## 📂 Project Structure

```
/backend          # FastAPI Application
  /middleware     # Auth, CSRF, Security middleware
  /routes         # API endpoints (v1)
  /services       # Business logic (Auth, Gallery, Storage)
  /utils          # Helpers (Security, Logging, Config)

/frontend         # Vue 3 Application
  /src/components # Reusable UI components
  /src/views      # Page views
  /src/stores     # Pinia state management
  /src/composables# Shared state logic
```

## 🔒 Security Measures

- **Rate Limiting**: Per-IP and per-User limits on all endpoints.
- **Input Validation**: Strict Pydantic models and manual sanitization.
- **XSS Protection**: Content-Security-Policy and input encoding.
- **CSRF**: Double Submit Cookie pattern.

## 🤝 Contributing

Please read [CODING_STANDARDS.md](CODING_STANDARDS.md) before contributing.