# Vercel Deployment Guide for PurrFect Spots

## การเตรียมการก่อน Deploy

### 1. ติดตั้ง Vercel CLI
```bash
npm i -g vercel
```

### 2. เข้าสู่ระบบ Vercel
```bash
vercel login
```

## การ Deploy Backend (FastAPI)

### 1. เข้าไปที่โฟลเดอร์ backend
```bash
cd backend
```

### 2. Deploy ครั้งแรก
```bash
vercel --prod
```

### 3. ตั้งค่า Environment Variables ใน Vercel Dashboard
ไปที่ [Vercel Dashboard](https://vercel.com/dashboard) > เลือกโปรเจกต์ > Settings > Environment Variables

ตั้งค่าตัวแปรต่อไปนี้:
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`
- `JWT_SECRET`
- `DEBUG=False`
- `CORS_ORIGINS`
- `GOOGLE_AI_API_KEY` (ถ้าใช้)
- `AWS_ACCESS_KEY_ID` (ถ้าใช้ S3)
- `AWS_SECRET_ACCESS_KEY` (ถ้าใช้ S3)
- `AWS_S3_BUCKET_NAME` (ถ้าใช้ S3)
- `AWS_REGION` (ถ้าใช้ S3)

### 4. Redeploy หลังตั้งค่า Environment Variables
```bash
vercel --prod
```

## การ Deploy Frontend (Vue.js)

### 1. อัปเดต API URL
แก้ไขในไฟล์ `frontend/src/config/api.ts` หรือสร้างไฟล์ `.env.local`:
```
VITE_API_BASE_URL=https://your-backend-name.vercel.app
```

### 2. เข้าไปที่โฟลเดอร์ frontend
```bash
cd frontend
```

### 3. Deploy ครั้งแรก
```bash
vercel --prod
```

### 4. ตั้งค่า Environment Variables สำหรับ Frontend (ถ้าต้องการ)
ใน Vercel Dashboard > Settings > Environment Variables:
- `VITE_API_BASE_URL` (optional, ถ้าไม่ต้องการ hard-code)

## การอัปเดต CORS Settings

หลังจาก deploy frontend แล้ว ต้องอัปเดต CORS ใน backend:

1. ไปที่ Vercel Dashboard ของ backend
2. Settings > Environment Variables
3. อัปเดต `CORS_ORIGINS` เป็น URL ของ frontend เช่น:
   ```
   CORS_ORIGINS=https://your-frontend-name.vercel.app
   ```
4. Redeploy backend

## การอัปเดต Google OAuth Redirect URI

1. ไปที่ [Google Cloud Console](https://console.cloud.google.com/)
2. เลือกโปรเจกต์ > APIs & Services > Credentials
3. แก้ไข OAuth 2.0 Client ID
4. เพิ่ม Authorized redirect URIs:
   ```
   https://your-frontend-name.vercel.app/auth/callback
   ```

## คำสั่งที่มีประโยชน์

### Deploy ทั้ง Backend และ Frontend พร้อมกัน
```bash
# จาก root directory
npm run deploy:all  # (ถ้ามี script นี้)
```

### ดู logs ของการ deploy
```bash
vercel logs
```

### ดู domains ที่มี
```bash
vercel domains ls
```

### เพิ่ม custom domain
```bash
vercel domains add yourdomain.com
```

## การจัดการ Environment Variables

### ดู Environment Variables ปัจจุบัน
```bash
vercel env ls
```

### เพิ่ม Environment Variable
```bash
vercel env add VARIABLE_NAME
```

### ลบ Environment Variable
```bash
vercel env rm VARIABLE_NAME
```

## Troubleshooting

### Backend ไม่ทำงาน
1. ตรวจสอบ logs: `vercel logs`
2. ตรวจสอบ Environment Variables
3. ตรวจสอบว่า `requirements.txt` ครบถ้วน
4. ตรวจสอบ Python version ใน `runtime.txt` (ถ้ามี)

### Frontend ไม่เชื่อมต่อ Backend
1. ตรวจสอบ API URL ใน `src/config/api.ts`
2. ตรวจสอบ CORS settings ใน backend
3. ตรวจสอบ Network tab ใน browser

### OAuth ไม่ทำงาน
1. ตรวจสอบ redirect URI ใน Google Cloud Console
2. ตรวจสอบ Environment Variables: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
3. ตรวจสอบ `GOOGLE_REDIRECT_URI` ให้ตรงกับ frontend URL

## URLs สำคัญ

- Vercel Dashboard: https://vercel.com/dashboard
- Google Cloud Console: https://console.cloud.google.com/
- Supabase Dashboard: https://supabase.com/dashboard

## สิ่งที่เปลี่ยนจาก Render

1. **Backend Structure**: เพิ่มโฟลเดอร์ `api/` และไฟล์ `index.py`
2. **Build Configuration**: ใช้ `vercel.json` แทน `render.yaml`
3. **Environment Variables**: ตั้งผ่าน Vercel Dashboard
4. **Logs**: ใช้ `vercel logs` แทน Render dashboard
5. **Domains**: จัดการผ่าน Vercel CLI หรือ Dashboard

## ข้อดีของ Vercel

1. **Serverless**: Auto-scaling และประหยัดค่าใช้จ่าย
2. **Global CDN**: โหลดเร็วทั่วโลก
3. **Git Integration**: Auto-deploy จาก GitHub
4. **Preview Deployments**: Test ก่อน production
5. **Analytics**: ดู performance metrics

## ข้อจำกัดของ Vercel

1. **Function Timeout**: สูงสุด 60 วินาที (Hobby plan)
2. **Cold Start**: อาจช้าในการเริ่มต้น
3. **Bandwidth Limit**: 100GB/เดือน (Hobby plan)
4. **File Size**: อัปโหลดไฟล์ใหญ่อาจมีปัญหา

## Tips

1. ใช้ `vercel dev` สำหรับ local development
2. ตั้ง auto-deploy จาก GitHub repository
3. ใช้ preview deployments สำหรับ testing
4. Monitor usage ใน Dashboard เพื่อไม่เกิน limits
