# 🐱 Purrfect Spots Backend

FastAPI backend สำหรับแอปพลิเคชัน Purrfect Spots - แอปแชร์รูปแมวและตำแหน่งที่พบแมว

## 🏗️ โครงสร้างโปรเจ็กต์

```
backend/
├── main.py              # ไฟล์หลักของ FastAPI application
├── app.py               # ไฟล์สำหรับรันเซิร์ฟเวอร์
├── fastapi_app.py       # ไฟล์สำหรับรันเซิร์ฟเวอร์ (สำรอง)
├── requirements.txt     # Python dependencies
├── .env.example         # ตัวอย่างไฟล์ environment variables
└── README_API.md        # คู่มือการใช้งาน API
```

## 🚀 การติดตั้งและเริ่มต้นใช้งาน

### 1. ติดตั้ง Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. ตั้งค่า Environment Variables
```bash
# คัดลอกไฟล์ .env.example เป็น .env
cp .env.example .env

# แก้ไขข้อมูลใน .env ให้ถูกต้อง
# - AWS_ACCESS_KEY_ID: AWS Access Key
# - AWS_SECRET_ACCESS_KEY: AWS Secret Key
# - AWS_REGION: AWS Region (เช่น ap-southeast-1)
# - AWS_S3_BUCKET: ชื่อ S3 Bucket (เช่น meow-spot-images)
```

### 3. เริ่มต้นเซิร์ฟเวอร์
```bash
# วิธีที่ 1: รันด้วย main.py
python main.py

# วิธีที่ 2: รันด้วย app.py
python app.py

# วิธีที่ 3: รันด้วย fastapi_app.py
python fastapi_app.py

# วิธีที่ 4: รันด้วย uvicorn โดยตรง
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. ตรวจสอบการทำงาน
เปิดเบราว์เซอร์ไปที่:
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## 🔧 คุณสมบัติหลัก

### � File Management
- **AWS S3**: การจัดเก็บรูปภาพบน cloud
- **Presigned URLs**: สร้าง URL สำหรับอัปโหลดโดยตรงไปยัง S3
- **Public Access**: รูปภาพสามารถเข้าถึงได้แบบสาธารณะ

### 🔐 Security
- **Secure Upload**: ใช้ presigned URLs ป้องกันการอัปโหลดที่ไม่ปลอดภัย
- **Unique Keys**: ใช้ UUID ป้องกันการซ้ำกันของไฟล์
- **Content Type Validation**: ตรวจสอบประเภทไฟล์

### 🌐 API Features
- **RESTful API**: API ที่เป็นมาตรฐาน
- **Interactive Documentation**: เอกสาร API อัตโนมัติด้วย Swagger UI
- **Error Handling**: การจัดการข้อผิดพลาดอย่างเหมาะสม

## 📋 API Endpoints

### 🔍 ระบบ
- `GET /` - หน้าหลัก API
- `GET /health` - ตรวจสอบสุขภาพระบบ

### � อัปโหลด
- `POST /api/presigned-url` - สร้าง presigned URL สำหรับอัปโหลดรูปภาพ

## 💡 ตัวอย่างการใช้งาน

### สร้าง Presigned URL
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

### อัปโหลดรูปภาพ
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

// อัปโหลดไฟล์โดยตรงไปยัง S3
await fetch(upload_url, {
  method: 'PUT',
  body: file,
  headers: { 'Content-Type': file.type }
});

// ใช้ public_url เพื่อแสดงรูปภาพ
```

## 🛠️ การพัฒนา

### โครงสร้างโค้ด
- **main.py**: ไฟล์เดียวที่มีทุกอย่าง เรียบง่าย
- **Minimal Dependencies**: ใช้ dependencies เฉพาะที่จำเป็น
- **AWS S3 Integration**: เชื่อมต่อกับ S3 โดยตรง

### หลักการออกแบบ
- **Simplicity**: ออกแบบให้เรียบง่าย เข้าใจง่าย
- **Performance**: ใช้ presigned URLs เพื่อประสิทธิภาพ
- **Security**: ป้องกันการอัปโหลดที่ไม่ปลอดภัย

## 🔄 Integration

### Frontend Integration
```javascript
// ตัวอย่างการเรียกใช้ API จาก Frontend
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

## 🐛 การแก้ไขปัญหา

### ปัญหาทั่วไป
1. **ไม่สามารถเชื่อมต่อ S3**: ตรวจสอบ AWS credentials ใน .env
2. **Presigned URL หมดอายุ**: URL มีอายุ 5 นาที ต้องใช้ทันที
3. **CORS Error**: อาจต้องเพิ่ม CORS middleware

### Log การทำงาน
```bash
# ดู log การทำงาน
python main.py
```

## 📚 เอกสารเพิ่มเติม

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [Presigned URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/presigned-urls.html)

## 🤝 การสนับสนุน

หากมีปัญหาหรือข้อสงสัย สามารถดูเอกสาร API ได้ที่ http://localhost:8000/docs
