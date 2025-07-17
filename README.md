# 🐱 PurrfectSpots

A modern cat spotting and sharing platform built with Vue.js, FastAPI, and Supabase.

## ✨ Features

- 📸 **Image Upload** - Upload cat photos with location data
- 🗺️ **Interactive Maps** - View cat locations on interactive maps
- 🖼️ **Gallery** - Browse all cat photos in a beautiful gallery
- 📍 **Location System** - GPS coordinates and place names
- 🔐 **Google OAuth** - Secure authentication with Google
- 👤 **User Profiles** - Manage user profiles and data
- 🛡️ **Security** - JWT-based authentication system
- 📱 **Responsive** - Works on desktop and mobile devices

## 🏗️ Architecture

```
purrfect-spots/
├── frontend/           # Vue.js frontend
├── backend/            # FastAPI backend
└── README.md          # This file
```

## � Quick Start

### Prerequisites
- **Node.js 18+** and npm
- **Python 3.8+** and pip
- **Supabase** account and project
- **Google OAuth 2.0** credentials
```env
# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=purrfect-spots-bucket
```

### 3. เปิดใช้งาน
- **เว็บไซต์**: http://localhost:5173
- **API**: http://localhost:5000

## � เทคโนโลยีที่ใช้

### 🎨 Frontend
- **Vue.js 3** - JavaScript framework
- **Vite** - Build tool ที่เร็วมาก
- **Leaflet** - แผนที่แบบโต้ตอบ
- **Tailwind CSS** - Styling

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
| DELETE | `/delete/<filename>` | ลบรูป |

### 💡 ตัวอย่างการใช้งาน
```bash
# อัปโหลดรูปแมว
curl -X POST http://localhost:5000/upload \
  -F "file=@cat.jpg" \
  -F "location=วัดพระสิงห์ เชียงใหม่" \
  -F "description=แมวน่ารัก"
```

## �️ การพัฒนา (สำหรับโปรแกรมเมอร์)

### Backend
```bash
cd backend
pip install -r requirements.txt
python app.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 📋 Requirements

- **Python 3.8+** 
- **Node.js 16+**
- **AWS S3 bucket** (ฟรีได้ที่ AWS)

## 🚨 แก้ปัญหาเบื้องต้น

1. **ไม่สามารถอัปโหลดรูปได้** → ตรวจสอบการตั้งค่า AWS
2. **แผนที่ไม่แสดง** → ตรวจสอบ internet connection
3. **เซิร์ฟเวอร์ไม่ทำงาน** → ดูใน console เพื่อหาข้อผิดพลาด

## � สนับสนุน

หากมีปัญหาหรือข้อสงสัย:
1. ดูที่ console logs
2. ตรวจสอบการตั้งค่า AWS
3. อ่าน API documentation ใน `backend/README_API.md`

---

สร้างด้วย ❤️ สำหรับคนรักแมวทั่วโลก 🐱
