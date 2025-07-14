# OAuth Google Setup Guide

## 📋 สิ่งที่ต้องเตรียม

### 1. Google Cloud Console Setup

#### สร้าง Google OAuth 2.0 Client ID
1. ไปที่ [Google Cloud Console](https://console.cloud.google.com/)
2. สร้าง Project ใหม่หรือเลือก Project ที่มีอยู่
3. เปิดใช้งาน **Google+ API** และ **Google Identity Toolkit API**
4. ไปที่ **Credentials** > **Create Credentials** > **OAuth 2.0 Client IDs**
5. เลือก **Web application**
6. กำหนด:
   - **Authorized JavaScript origins**: `http://localhost:5173`
   - **Authorized redirect URIs**: `http://localhost:5173`
7. บันทึก **Client ID** ที่ได้มา

### 2. Supabase Setup

#### สร้าง Database Tables
1. ไปที่ Supabase Dashboard
2. เปิด **SQL Editor**
3. รันไฟล์ `backend/migrations/001_create_users_table.sql`

#### ตั้งค่า Environment Variables
1. ใน Supabase Dashboard หา:
   - **SUPABASE_URL**: ใน Settings > API
   - **SUPABASE_SERVICE_ROLE_KEY**: ใน Settings > API (Service Role secret)

### 3. Backend Configuration

สร้างไฟล์ `.env` ใน `backend/` folder:

```env
# AWS Configuration (เดิม)
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION=ap-southeast-1
AWS_S3_BUCKET=purrfect-spots-bucket

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com

# JWT Configuration
JWT_SECRET=your_super_secret_jwt_key_here_make_it_long_and_random
```

### 4. Frontend Configuration

สร้างไฟล์ `.env` ใน `frontend/` folder:

```env
# Google OAuth Configuration
VITE_GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com

# API Base URL
VITE_API_BASE_URL=http://localhost:8000
```

## 🚀 การรันระบบ

### 1. Install Dependencies

#### Backend:
```bash
cd backend
pip install -r requirements.txt
```

#### Frontend:
```bash
cd frontend
npm install
```

### 2. รันแอปพลิเคชัน

#### Backend:
```bash
cd backend
python app.py
```

#### Frontend:
```bash
cd frontend
npm run dev
```

## ✨ Features ที่เพิ่มเข้ามา

### 🔐 Authentication System
- **Google OAuth 2.0**: เข้าสู่ระบบด้วย Google (ฟรี)
- **JWT Tokens**: จัดการ session อย่างปลอดภัย
- **User Profiles**: ข้อมูลผู้ใช้และรูปโปรไฟล์
- **Route Protection**: ป้องกัน routes ที่ต้องการการเข้าสู่ระบบ

### 🗂️ Folder Structure ใหม่

```
backend/
├── auth/                 # Authentication routes
├── middleware/           # Auth middleware
├── models/              # Data models
├── services/            # Business logic
└── migrations/          # Database migrations

frontend/
├── src/
│   ├── services/        # API services
│   ├── store/           # State management
│   ├── types/           # TypeScript types
│   └── components/
│       └── common/      # Reusable components
│           ├── GoogleOAuthButton.vue
│           ├── LoginModal.vue
│           └── LoadingSpinner.vue
```

### 🔄 API Endpoints ใหม่

- `POST /auth/google` - Login with Google OAuth
- `GET /auth/me` - Get current user info
- `POST /auth/logout` - Logout user

### 🎨 UI Components ใหม่

- **LoginModal**: Modal สำหรับเข้าสู่ระบบ
- **GoogleOAuthButton**: ปุ่ม Google Sign-In
- **User Menu**: เมนูผู้ใช้ใน NavBar
- **Loading States**: แสดงสถานะการโหลด

## 🛡️ Security Features

- **JWT Token Validation**
- **OAuth Token Verification**
- **Row Level Security (RLS)** ใน Supabase
- **CORS Protection**
- **Input Validation**

## 📱 Responsive Design

- รองรับทุกขนาดหน้าจอ
- Mobile-first approach
- Touch-friendly interface

## 🔍 ขั้นตอนการทดสอบ

1. เปิด `http://localhost:5173`
2. คลิก "เข้าสู่ระบบ"
3. เลือก Google Account
4. ตรวจสอบว่าชื่อและรูปโปรไฟล์แสดงใน NavBar
5. ทดสอบ Logout
6. ตรวจสอบ API endpoints ใน Network tab

## 💡 Tips

- ใช้ **Google Client ID** ที่ถูกต้องใน production
- เปลี่ยน `JWT_SECRET` เป็นค่าที่ปลอดภัยใน production
- ตั้งค่า CORS อย่างเหมาะสมใน production
- ใช้ HTTPS ใน production environment
