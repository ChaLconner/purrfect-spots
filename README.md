# 🐱 Purrfect Spots

แอปพลิเคชันสำหรับค้นหาและแชร์รูปภาพแมวพร้อมตำแหน่งที่ตั้ง สร้างด้วย Vue.js + FastAPI + Supabase + AWS S3 พร้อมระบบ OAuth Google

## ✨ คุณสมบัติ

- 📸 **อัปโหลดรูปภาพ**: อัปโหลดรูปแมวพร้อมข้อมูลตำแหน่งที่ตั้ง
- 🗺️ **แผนที่แบบโต้ตอบ**: ดูตำแหน่งแมวบนแผนที่
- 🖼️ **แกลเลอรี่**: เรียกดูรูปภาพแมวทั้งหมด
- 📍 **ระบบตำแหน่ง**: รองรับพิกัด GPS และชื่อสถานที่
- 🔐 **OAuth Authentication**: เข้าสู่ระบบด้วย Google (ฟรี!)
- 👤 **User Profiles**: จัดการโปรไฟล์ผู้ใช้
- 🛡️ **Security**: ระบบรักษาความปลอดภัยด้วย JWT
- 🌏 **หลายภาษา**: รองรับภาษาไทยและอังกฤษ
- 📱 **Responsive**: ใช้งานได้ทั้งคอมพิวเตอร์และมือถือ

## 🚀 Quick Start

### 1. ดาวน์โหลดโปรเจค
```bash
git clone <repository-url>
cd purrfect-spots
```

### 2. ตั้งค่า OAuth Google
📖 ดู [OAuth Setup Guide](OAuth_Setup_Guide.md) สำหรับขั้นตอนการตั้งค่าแบบละเอียด

### 3. ตั้งค่า Environment Variables

#### Backend (.env):
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
