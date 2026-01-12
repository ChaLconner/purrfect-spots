# 🐱 Purrfect Spots Backend

FastAPI backend for Purrfect Spots application - Cat photo sharing and location finder app

## 🏗️ Project Structure

```
backend/
├── main.py              # Main FastAPI application file
├── app.py               # Server startup file
├── fastapi_app.py       # Server startup file (backup)
├── requirements.txt     # Python dependencies
├── .env.example         # Example environment variables file
└── README_API.md        # API usage guide
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

# Edit information in .env to be correct
# - AWS_ACCESS_KEY_ID: AWS Access Key
# - AWS_SECRET_ACCESS_KEY: AWS Secret Key
# - AWS_REGION: AWS Region (e.g., ap-southeast-1)
# - AWS_S3_BUCKET: S3 Bucket name (e.g., meow-spot-images)
```

### 3. Start Server
```bash
# Method 1: Run with main.py
python main.py

# Method 2: Run with app.py
python app.py

# Method 3: Run with fastapi_app.py
python fastapi_app.py

# Method 4: Run directly with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
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
- **Secure Upload**: Use presigned URLs to prevent insecure uploads
- **Unique Keys**: Use UUID to prevent file duplication
- **Content Type Validation**: Validate file types

### 🌐 API Features
- **RESTful API**: Standard API
- **Interactive Documentation**: Automatic API documentation with Swagger UI
- **Error Handling**: Appropriate error management

## 📋 API Endpoints

### 🔍 System
- `GET /` - API main page
- `GET /health` - Check system health

### 📤 Upload
- `POST /api/presigned-url` - Create presigned URL for image upload

## 💡 Usage Examples

### Create Presigned URL
```bash
curl -X POST "http://localhost:8000/api/presigned-url" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "cat.jpg",
    "content_type": "image/jpeg"
  }'
```

**Response:**
```json
{
  "upload_url": "https://s3.amazonaws.com/...",
  "public_url": "https://meow-spot-images.s3.ap-southeast-1.amazonaws.com/cats/uuid.jpg",
  "key": "cats/uuid.jpg"
}
```

### Upload Image
```javascript
// Frontend JavaScript
const response = await fetch('/api/presigned-url', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    filename: file.name,
    content_type: file.type
  })
});

const { upload_url, public_url } = await response.json();

// Upload file directly to S3
await fetch(upload_url, {
  method: 'PUT',
  body: file,
  headers: { 'Content-Type': file.type }
});

// Use public_url to display image
```

## 🛠️ Development

### Code Structure
- **main.py**: Single file with everything, simple
- **Minimal Dependencies**: Use only necessary dependencies
- **AWS S3 Integration**: Connect directly to S3

### Design Principles
- **Simplicity**: Designed to be simple and easy to understand
- **Performance**: Use presigned URLs for performance
- **Security**: Prevent insecure uploads

## 🔄 Integration

### Frontend Integration
```javascript
// Example API call from Frontend
const createPresignedUrl = async (file) => {
  const response = await fetch('http://localhost:8000/api/presigned-url', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      filename: file.name,
      content_type: file.type
    })
  });
  return response.json();
};
```

## 🐛 Troubleshooting

### Common Problems
1. **Cannot connect to S3**: Check AWS credentials in .env
2. **Presigned URL expired**: URL has 5-minute lifetime, must use immediately
3. **CORS Error**: May need to add CORS middleware

### Operation Logs
```bash
# View operation logs
python main.py
```

## 📚 Additional Documentation

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [Presigned URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/presigned-urls.html)

## 🤝 Support

If you have problems or questions, you can view API documentation at http://localhost:8000/docs
