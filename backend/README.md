# 🐱 Purrfect Spots Backend

FastAPI backend for Purrfect Spots application - Cat photo sharing and location finder app

## 🏗️ Project Structure

```
backend/
├── app/                 # Importable application package
│   ├── main.py          # FastAPI application entrypoint
│   ├── dependencies.py  # Dependency injection
│   ├── schemas/         # Pydantic models
│   ├── services/        # Business logic
│   ├── routes/          # API endpoints
│   └── utils/           # Helper functions
├── api/                 # Serverless deployment adapter
├── scripts/             # Backend maintenance scripts
├── tests/               # Unit and integration tests
├── requirements.txt     # Python dependencies
├── .env.example         # Example environment variables file
└── README.md            # Backend guide
```

## 🚀 Installation and Getting Started

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Set Environment Variables
```bash
# Copy .env.example file to .env
cp .env.example .env

# Edit .env with valid credentials for:
# - AWS S3
# - Supabase
# - Google OAuth
# - Google Cloud Vision
```

### 3. Start Server
```bash
# Development mode with auto-reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Check Operation
Open browser to:
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## 🔧 Key Features

### 📁 File Management
- **AWS S3**: Cloud image storage
- **Presigned URLs**: Create URLs for direct upload to S3
- **Public Access**: Images can be accessed publicly

### 🔐 Security
- **OAuth 2.0**: Google Authentication
- **JWT**: Token-based session management
- **Secure Uploads**: Content type validation
- **RLS**: Supabase Row Level Security (managed via service role)

### 🌐 API Features
- **RESTful API**: Standard API
- **Interactive Documentation**: Automatic API documentation with Swagger UI
- **Error Handling**: Appropriate error management

### External API Worker

Stripe webhook persistence and non-admission Google Vision analysis use Redis
Streams when the queue flags are enabled. The API verifies the Stripe
signature, stores a bounded queue envelope, and returns a retryable `503` if
Redis is unavailable. The worker reclaims stale consumer-group entries and
moves exhausted jobs to a dead-letter stream.

```bash
# Local/Docker: starts the API, worker, and Redis dependencies.
docker compose up -d backend backend-worker redis
```

`POST /api/v1/detect/cats` remains synchronous and fail-closed because its
Vision result creates the upload verification token. `spot-analysis` and
`combined` may return `202` with a `job_id`; the frontend polls
`GET /api/v1/detect/jobs/{job_id}`.

Vercel runs the API as serverless functions and does not run this long-lived
worker. Keep the queue flags disabled there until `app.worker` is deployed on
a long-lived host with the same `QUEUE_REDIS_URL`; then create the Stripe
event destination for `/api/v1/subscription/webhook` and configure the
generated signing secret in the runtime environment.

## 📋 API Endpoints

### 🔍 System
- `GET /` - API main page
- `GET /health` - Check system health

### 📤 Upload
- `POST /api/upload/presigned-url` - Create presigned URL for image upload

### 🤖 AI
- `POST /api/detect` - Detect cat in image

## 📚 Additional Documentation

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [Supabase Documentation](https://supabase.com/docs)

## 🤝 Support

If you have problems or questions, you can view API documentation at http://localhost:8000/docs
