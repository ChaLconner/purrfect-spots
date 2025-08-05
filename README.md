# 🐱 Purrfect Spots

A modern cat photo sharing platform with AI-powered cat detection, built with Vue.js, FastAPI, and Supabase.

## ✨ Features

- 📸 **Smart Upload** - Upload cat photos with AI-powered cat detection using Google AI Studio
- �️ **Cat Validation** - Automatically validates uploaded images contain cats
- �️ **Location Tagging** - Add GPS coordinates and location names to photos  
- �️ **Photo Gallery** - Browse all cat photos in a beautiful masonry gallery
- 👤 **User Profiles** - Personal profiles with bio and photo management
- � **Secure Auth** - Google OAuth and manual registration with Supabase
- 📱 **Responsive Design** - Works perfectly on desktop and mobile
- ☁️ **Cloud Storage** - Images stored securely in AWS S3

## 🏗️ Tech Stack

### Frontend
- **Vue.js 3** with Composition API
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **Vite** for fast development

### Backend  
- **FastAPI** for high-performance API
- **Google AI Studio** for cat detection
- **Supabase** for database and auth
- **AWS S3** for image storage
- **JWT** for secure sessions

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- AWS S3 bucket
- Supabase project
- Google OAuth credentials
- Google AI Studio API key

### 1. Clone Repository
```bash
git clone https://github.com/ChaLconner/purrfect-spots.git
cd purrfect-spots
```

### 2. Setup Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
uvicorn main:app --reload
```

### 3. Setup Frontend
```bash
cd frontend  
npm install
cp .env.example .env
# Edit .env with your API URLs
npm run dev
```

### 4. Access Application
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### ⚙️ Backend
- **Flask** - Python web framework
- **AWS S3** - เก็บไฟล์รูปภาพ
- **boto3** - เชื่อมต่อ AWS

## � โครงสร้างโปรเจค

```
purrfect-spots/
├── 🎨 frontend/        # Vue.js app
│   ├── src/components/ # คอมโพเนนต์
│   ├── src/router/     # การนำทาง
│   └── package.json
├── ⚙️ backend/         # Flask API
│   ├── app.py         # แอปหลัก
│   ├── api_handlers.py # API endpoints
│   └── requirements.txt
└── 🚀 start_new.bat   # รันแอป
```

## � API แบบง่าย

### � Endpoints หลัก

| วิธี | URL | ทำอะไร |
|------|-----|--------|
| GET | `/images` | ดูรูปภาพทั้งหมด |
| GET | `/locations` | ดูตำแหน่งทั้งหมด |
| POST | `/upload` | อัปโหลดรูปใหม่ |

### 💡 ตัวอย่างการใช้งาน
```bash
# อัปโหลดรูปแมว
curl -X POST http://localhost:5000/upload \
  -F "file=@cat.jpg" \
  -F "location=วัดพระสิงห์ เชียงใหม่" \
  -F "description=แมวน่ารัก"
```
---

สร้างด้วย ❤️ สำหรับคนรักแมวทั่วโลก 🐱
