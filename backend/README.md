# 🐱 Purrfect Spots Backend

FastAPI backend สำหรับแอปพลิเคชัน Purrfect Spots - แอปแชร์รูปแมวและตำแหน่งที่พบแมว

## 🏗️ โครงสร้างโปรเจ็กต์

```
backend/
├── main.py              # ไฟล์หลักของ FastAPI application
├── app.py               # ไฟล์สำหรับรันเซิร์ฟเวอร์
├── fastapi_app.py       # ไฟล์สำหรับรันเซิร์ฟเวอร์ (สำรอง)
├── database.py          # การตั้งค่าฐานข้อมูล และ session management
├── models.py            # SQLAlchemy models และ Pydantic schemas
├── routes.py            # API routes และ endpoints
├── utils.py             # Helper functions และ utilities
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
# - DATABASE_URL: URL ของฐานข้อมูล PostgreSQL
# - AWS_ACCESS_KEY_ID: AWS Access Key
# - AWS_SECRET_ACCESS_KEY: AWS Secret Key
# - AWS_REGION: AWS Region
# - S3_BUCKET_NAME: ชื่อ S3 Bucket
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

### 📊 Database
- **SQLAlchemy ORM**: การจัดการฐานข้อมูลแบบ Object-Relational Mapping
- **PostgreSQL**: ฐานข้อมูลหลัก (รองรับ Supabase)
- **Auto Migration**: สร้างตารางฐานข้อมูลอัตโนมัติ

### 🔐 Authentication & Security
- **CORS**: การจัดการ Cross-Origin Resource Sharing
- **Input Validation**: ตรวจสอบข้อมูลด้วย Pydantic
- **Error Handling**: การจัดการข้อผิดพลาดแบบครบถ้วน

### 📁 File Management
- **AWS S3**: การจัดเก็บรูปภาพบน cloud
- **Image Optimization**: ปรับปรุงคุณภาพรูปภาพอัตโนมัติ
- **File Upload**: รองรับการอัปโหลดไฟล์หลายรูปแบบ

### 🌐 API Features
- **RESTful API**: API ที่เป็นมาตรฐาน
- **Interactive Documentation**: เอกสาร API อัตโนมัติด้วย Swagger UI
- **Sample Data**: ข้อมูลตัวอย่างเมื่อไม่มีการตั้งค่า S3

## 📋 API Endpoints

### 🔍 ระบบ
- `GET /` - หน้าหลัก API
- `GET /health` - ตรวจสอบสุขภาพระบบ

### 📸 รูปภาพ
- `GET /images` - ดูรูปภาพทั้งหมดจากฐานข้อมูล
- `GET /images/{image_id}` - ดูรูปภาพเฉพาะ
- `POST /images` - เพิ่มข้อมูลรูปภาพ
- `DELETE /images/{filename}` - ลบรูปภาพ

### 🗺️ ตำแหน่ง
- `GET /locations` - ดูตำแหน่งทั้งหมด
- `GET /images_list` - ดูรายการรูปภาพใน S3

### 📤 อัปโหลด
- `POST /upload` - อัปโหลดรูปภาพ
- `POST /generate-presigned-url` - สร้าง URL สำหรับอัปโหลดโดยตรง

## 🛠️ การพัฒนา

### โครงสร้างโค้ด
- **main.py**: ไฟล์หลักของ FastAPI application
- **database.py**: การตั้งค่าฐานข้อมูล
- **models.py**: SQLAlchemy models และ Pydantic schemas
- **routes.py**: API routes แยกออกจาก main application
- **utils.py**: Helper functions และ utilities

### หลักการออกแบบ
- **Separation of Concerns**: แยกส่วนการทำงานออกจากกัน
- **Modular Design**: ออกแบบแบบโมดูลาร์
- **Error Handling**: จัดการข้อผิดพลาดอย่างเหมาะสม
- **Logging**: บันทึกการทำงานของระบบ

## 🔄 Integration

### Frontend Integration
```javascript
// ตัวอย่างการเรียกใช้ API จาก Frontend
const response = await fetch('http://localhost:8000/locations');
const locations = await response.json();
```

### Database Schema
```sql
-- ตารางเก็บข้อมูลรูปภาพ
CREATE TABLE cat_images (
    id VARCHAR(36) PRIMARY KEY,
    s3_key VARCHAR NOT NULL,
    url VARCHAR NOT NULL,
    location VARCHAR,
    description VARCHAR,
    latitude FLOAT,
    longitude FLOAT,
    original_name VARCHAR,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🐛 การแก้ไขปัญหา

### ปัญหาทั่วไป
1. **ไม่สามารถเชื่อมต่อฐานข้อมูล**: ตรวจสอบ DATABASE_URL ใน .env
2. **ไม่สามารถอัปโหลดรูปภาพ**: ตรวจสอบการตั้งค่า AWS S3
3. **CORS Error**: ตรวจสอบการตั้งค่า CORS ใน main.py

### Log การทำงาน
```bash
# ดู log การทำงาน
tail -f uvicorn.log
```

## 📚 เอกสารเพิ่มเติม

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [Supabase Documentation](https://supabase.com/docs)

## 🤝 การสนับสนุน

หากมีปัญหาหรือข้อสงสัย สามารถสอบถามได้ที่ README_API.md สำหรับตัวอย่างการใช้งาน API
