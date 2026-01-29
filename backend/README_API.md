# 🔌 Purrfect Spots API

API usage guide for cat photo sharing app.

## 🚀 Base URL

All API endpoints are available at: `http://localhost:8000`

## 📋 API Endpoints

### 🔍 System
| URL | Method | Description |
|-----|--------|-------------|
| `/` | GET | API Main Page |
| `/health` | GET | Health Check |

### 📸 Image Upload (Presigned URL)
The application uses **Presigned URLs** to upload images directly to AWS S3. This ensures performance and security.

| URL | Method | Description |
|-----|--------|-------------|
| `/api/upload/presigned-url` | POST | Generate a presigned URL for upload |

### 🤖 AI Detection
| URL | Method | Description |
|-----|--------|-------------|
| `/api/detect` | POST | Detect cats in an uploaded image |

### 🧭 Data & Locations
| URL | Method | Description |
|-----|--------|-------------|
| `/api/locations` | GET | Get all cat locations |
| `/api/images` | GET | Get all gallery images |

## 💡 Usage Examples

### 1. Check System Health
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-01T12:00:00Z"
}
```

### 2. Upload Flow

**Step 1: Get Presigned URL**
```bash
curl -X POST "http://localhost:8000/api/upload/presigned-url" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "cat.jpg",
    "content_type": "image/jpeg"
  }'
```

**Response:**
```json
{
  "upload_url": "https://s3.ap-southeast-1.amazonaws.com/bucket-name/cats/uuid.jpg?AWSAccessKeyId=...",
  "public_url": "https://bucket-name.s3.ap-southeast-1.amazonaws.com/cats/uuid.jpg",
  "key": "cats/uuid.jpg"
}
```

**Step 2: Upload File to S3 (Frontend)**
```javascript
// PUT request to the upload_url
await fetch(upload_url, {
  method: 'PUT',
  body: fileObject,
  headers: {
    'Content-Type': 'image/jpeg'
  }
});
```

**Step 3: Analyze Image**
```bash
curl -X POST "http://localhost:8000/api/detect" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "cats/uuid.jpg" 
  }'
```

## 🚨 Error Handling

| Code | Description |
|------|-------------|
| `400` | Bad Request (Missing fields) |
| `401` | Unauthorized (Invalid token) |
| `403` | Forbidden (Permission denied) |
| `500` | Server Error (Check logs) |
