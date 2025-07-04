# 🐱 Purrfect Spots

แอปพลิเคชัน web สำหรับแชร์รูปภาพแมวพร้อมพิกัดที่ถ่าย พร้อมกับการอัพโหลดไปยัง AWS S3

## ✨ Features

- 📸 อัพโหลดรูปภาพแมวพร้อมข้อมูลสถานที่
- 🗺️ บันทึกพิกัด GPS ของสถานที่ที่ถ่ายรูป
- 🖼️ แสดงรูปภาพในรูปแบบ gallery
- 🔍 ดูรูปภาพแบบ fullscreen modal
- 📍 แสดงแผนที่ (Map component)
- ☁️ จัดเก็บรูปภาพบน AWS S3
- 🎨 UI/UX ที่สวยงามด้วย Tailwind CSS
- 📱 Responsive design

## 🏗️ Architecture

```
purrfect-spots/
├── frontend/          # Vue.js 3 + Vite
├── backend/           # Flask + AWS S3
└── docs/              # Documentation
```

### Frontend
- **Vue.js 3** - Framework หลัก
- **Vite** - Build tool
- **Vue Router** - การนำทางระหว่างหน้า
- **Tailwind CSS** - Styling
- **Leaflet** - Maps integration

### Backend
- **Flask** - Python web framework
- **AWS S3** - Cloud storage
- **Boto3** - AWS SDK
- **PIL/Pillow** - Image processing
- **Flask-CORS** - Cross-origin requests

## 🚀 Quick Start

### Prerequisites
- Node.js (16+)
- Python (3.8+)
- AWS Account
- Git

### 1. Clone Repository
```bash
git clone <repository-url>
cd purrfect-spots
```

### 2. Setup Backend
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your AWS credentials
```

### 3. Setup Frontend
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 4. Start Backend
```bash
cd backend

# Run the Flask server
python app.py
```

### 5. Open Application
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:5000`

## ⚙️ Configuration

### AWS S3 Setup
1. สร้าง S3 bucket
2. ตั้งค่า bucket policy เพื่อ public access
3. สร้าง IAM user พร้อม permissions
4. ใส่ credentials ในไฟล์ `.env`

📋 ดูคำแนะนำทีละขั้นตอนใน [AWS_S3_SETUP.md](AWS_S3_SETUP.md)

### Environment Variables
```env
# Backend (.env)
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your_bucket_name
```

## 🔧 Development

### Frontend Development
```bash
cd frontend

# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Backend Development
```bash
cd backend

# Run with debug mode
python app.py

# Run tests
python test_backend.py

# Install new packages
pip install package_name
pip freeze > requirements.txt
```

## 📁 Project Structure

```
purrfect-spots/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── NavBar.vue
│   │   │   ├── Upload.vue
│   │   │   ├── Gallery.vue
│   │   │   └── Map.vue
│   │   ├── router/
│   │   ├── assets/
│   │   └── main.ts
│   ├── public/
│   └── package.json
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── requirements.txt
│   ├── test_backend.py
│   └── .env.example
└── README.md
```

## 🌐 API Endpoints

### Backend API
- `GET /health` - Health check
- `GET /config` - Configuration status
- `POST /upload` - Upload image
- `GET /images` - List all images
- `DELETE /delete/<filename>` - Delete image

### Upload API Example
```bash
curl -X POST \
  -F "file=@image.jpg" \
  -F "location=Bangkok" \
  -F "description=Cute cat" \
  -F "latitude=13.7563" \
  -F "longitude=100.5018" \
  http://localhost:5000/upload
```

## 🎨 UI Components

### NavBar
- Logo และชื่อแอป
- เมนูการนำทาง
- Responsive design

### Upload
- Drag & drop file upload
- Form สำหรับข้อมูลรูปภาพ
- GPS location picker
- Upload progress indicator

### Gallery
- Grid layout สำหรับรูปภาพ
- Image modal viewer
- Delete functionality
- Responsive grid

### Map
- Integration กับ Leaflet
- แสดงพิกัดรูปภาพ
- Interactive map

## 🔍 Testing

### Backend Testing
```bash
cd backend
python test_backend.py
```

### Frontend Testing
```bash
cd frontend
npm run test
```

## 📦 Deployment

### Frontend (Static Hosting)
```bash
npm run build
# Deploy dist/ folder to your hosting provider
```

### Backend (Cloud Deployment)
- Heroku
- AWS Lambda
- Google Cloud Run
- Digital Ocean

## 🛠️ Troubleshooting

### Common Issues

1. **CORS Error**
   - ตรวจสอบว่า backend เปิด CORS
   - ตรวจสอบ URL ของ API

2. **S3 Upload Failed**
   - ตรวจสอบ AWS credentials
   - ตรวจสอบ bucket policy
   - ตรวจสอบ IAM permissions

3. **Image Not Loading**
   - ตรวจสอบ bucket เป็น public
   - ตรวจสอบ CORS configuration

4. **Backend Not Starting**
   - ตรวจสอบ Python version
   - ตรวจสอบ virtual environment
   - ตรวจสอบ dependencies

## 📝 License

MIT License

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📞 Support

หากมีปัญหาหรือคำถาม:
1. ตรวจสอบ documentation
2. ดู troubleshooting guide
3. สร้าง issue ใน GitHub

---

🐱 **Happy coding with Purrfect Spots!** 🐱
