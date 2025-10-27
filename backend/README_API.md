# 🔌 Purrfect Spots API

API usage guide for cat photo sharing app - Easy to understand, easy to use!

## 🚀 Getting Started

```bash
cd backend
pip install -r requirements.txt
python main.py
```

✅ Server will run at: `http://localhost:8000`

## 📋 API Endpoints

### 🩺 ตรวจสอบระบบ

| URL | Method | ทำอะไร |
|-----|--------|--------|
| `/` | GET | หน้าหลัก API |
| `/health` | GET | ตรวจสอบว่าเซิร์ฟเวอร์ทำงานไหม |

### 📸 จัดการรูปภาพ

| URL | Method | ทำอะไร |
|-----|--------|--------|
| `/api/presigned-url` | POST | สร้าง presigned URL สำหรับอัปโหลดรูปภาพ |

## 💡 Usage Examples

### 1. ✅ Check Server
```bash
curl http://localhost:8000/health
```

**Result:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T00:00:00"
}
```

### 2. 🔄 Create Presigned URL
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
  "upload_url": "https://s3.amazonaws.com/meow-spot-images/...",
  "public_url": "https://meow-spot-images.s3.ap-southeast-1.amazonaws.com/cats/uuid.jpg",
  "key": "cats/uuid.jpg"
}
```

### 3. 🔄 Upload Image
```javascript
// Frontend JavaScript
const uploadImage = async (file) => {
  // 1. Request presigned URL
  const response = await fetch('/api/presigned-url', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      filename: file.name,
      content_type: file.type
    })
  });
  
  const { upload_url, public_url } = await response.json();
  
  // 2. Upload file directly to S3
  await fetch(upload_url, {
    method: 'PUT',
    body: file,
    headers: { 'Content-Type': file.type }
  });
  
  // 3. Use public_url to display image
  return public_url;
};
```
### 2. 📸 Upload Cat Photo
```bash
curl -X POST http://localhost:5000/upload \
  -F "file=@cat.jpg" \
  -F "location=Wat Phra Singh, Chiang Mai" \
  -F "description=Cute cat" \
  -F "latitude=18.7883" \
  -F "longitude=98.9853"
```

**What you get back:**
```json
{
  "message": "Upload successful!",
  "filename": "cat_20240120_103000_abc12345.jpg",
  "url": "https://purrfect-spots-bucket.s3.us-east-1.amazonaws.com/...",
  "metadata": {
    "location": "Wat Phra Singh, Chiang Mai",
    "description": "Cute cat"
  }
}
```

### 3. 🖼️ View All Images
```bash
curl http://localhost:5000/images
```

**What you get back:**
```json
{
  "images": [
    {
      "filename": "cat_20240120_103000_abc12345.jpg",
      "url": "https://...",
      "size": 256000,
      "metadata": {
        "location": "Wat Phra Singh, Chiang Mai",
        "description": "Cute cat"
      }
    }
  ]
}
```

### 4. 🗺️ View All Locations
```bash
curl http://localhost:5000/locations
```

### 5. 🗑️ Delete Image
```bash
curl -X DELETE http://localhost:5000/delete/cat_20240120_103000_abc12345.jpg
```

## 🔧 AWS Configuration

Create a `.env` file and add this information:

```env
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=purrfect-spots-bucket
```

## 🚨 Troubleshooting

### Common Problems:
1. **500 Error** → Check AWS configuration
2. **File too large** → File larger than 16MB
3. **Invalid file type** → Only supports jpg, png, gif
4. **Missing location** → Must include location

### Supported Files:
- `.jpg`, `.jpeg`, `.png`, `.gif`
- Maximum size 16MB

## 🔍 Check Operation

```bash
# Check server
curl http://localhost:5000/health

# Check AWS configuration
curl http://localhost:5000/config
```

---

Made with ❤️ for 🐱 lovers!


## 🔒 File Upload Restrictions

- **Supported Files**: PNG, JPG, JPEG, GIF, WEBP
- **Maximum File Size**: 16MB
- **Resizing**: Images will be automatically resized to 1920x1080 (if larger)
- **Quality**: JPEG quality 85% for optimization

## 🚨 Error Responses

| HTTP Code | Description | Example |
|-----------|-------------|---------|
| `400` | Bad Request | `{"error": "No file provided"}` |
| `404` | Not Found | `{"error": "Endpoint not found"}` |
| `413` | Payload Too Large | `{"error": "File too large. Maximum size is 16MB"}` |
| `500` | Server Error | `{"error": "S3 is not configured"}` |

## 🛠️ Features

- ✅ **Unicode Support**: Supports Thai language in metadata
- ✅ **Image Optimization**: Resize and optimize image quality
- ✅ **Unique Filenames**: Create unique filenames with timestamp + UUID
- ✅ **CORS Support**: Support calls from frontend
- ✅ **Error Handling**: Complete error management
- ✅ **AWS Integration**: Connect to real S3 bucket

## 🔍 Logging

Server will display log information:
- AWS S3 connection
- File upload and deletion
- Errors and warnings
- API request details

Example log:
```
INFO:aws_config:S3 client initialized successfully
INFO:aws_config:Using bucket: purrfect-spots-bucket
INFO:aws_config:✅ S3 connection test passed
INFO:api_handlers:Successfully uploaded cat_20240120_103000_abc12345.jpg to S3
```
