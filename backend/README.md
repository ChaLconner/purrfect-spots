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
