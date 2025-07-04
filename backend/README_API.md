# 🔌 Purrfect Spots API

คู่มือการใช้งาน API สำหรับแอปแชร์รูปแมว - เข้าใจง่าย ใช้งานง่าย!

## 🚀 เริ่มต้นใช้งาน

```bash
cd backend
pip install -r requirements.txt
python app.py
```

✅ เซิร์ฟเวอร์จะรันที่: `http://localhost:5000`

## 📋 API Endpoints (ทั้งหมด)

### 🩺 ตรวจสอบระบบ

| URL | Method | ทำอะไร |
|-----|--------|--------|
| `/health` | GET | ตรวจสอบว่าเซิร์ฟเวอร์ทำงานไหม |
| `/config` | GET | ดูการตั้งค่า AWS |

### 📸 จัดการรูปภาพ

| URL | Method | ทำอะไร |
|-----|--------|--------|
| `/images` | GET | ดูรูปภาพทั้งหมด |
| `/locations` | GET | ดูตำแหน่งทั้งหมด |
| `/upload` | POST | อัปโหลดรูปใหม่ |
| `/delete/<filename>` | DELETE | ลบรูป |

## 💡 ตัวอย่างการใช้งาน

### 1. ✅ ตรวจสอบเซิร์ฟเวอร์
```bash
curl http://localhost:5000/health
```

**ผลลัพธ์:**
```json
{
  "status": "healthy",
  "message": "Server is running"
}
```

**Response:**
```json
{
### 2. 📸 อัปโหลดรูปแมว
```bash
curl -X POST http://localhost:5000/upload \
  -F "file=@cat.jpg" \
  -F "location=วัดพระสิงห์ เชียงใหม่" \
  -F "description=แมวน่ารัก" \
  -F "latitude=18.7883" \
  -F "longitude=98.9853"
```

**ได้อะไรกลับมา:**
```json
{
  "message": "อัปโหลดสำเร็จ!",
  "filename": "cat_20240120_103000_abc12345.jpg",
  "url": "https://purrfect-spots-bucket.s3.us-east-1.amazonaws.com/...",
  "metadata": {
    "location": "วัดพระสิงห์ เชียงใหม่",
    "description": "แมวน่ารัก"
  }
}
```

### 3. 🖼️ ดูรูปทั้งหมด
```bash
curl http://localhost:5000/images
```

**ได้อะไรกลับมา:**
```json
{
  "images": [
    {
      "filename": "cat_20240120_103000_abc12345.jpg",
      "url": "https://...",
      "size": 256000,
      "metadata": {
        "location": "วัดพระสิงห์ เชียงใหม่",
        "description": "แมวน่ารัก"
      }
    }
  ]
}
```

### 4. 🗺️ ดูตำแหน่งทั้งหมด
```bash
curl http://localhost:5000/locations
```

### 5. 🗑️ ลบรูป
```bash
curl -X DELETE http://localhost:5000/delete/cat_20240120_103000_abc12345.jpg
```

## 🔧 การตั้งค่า AWS

สร้างไฟล์ `.env` และใส่ข้อมูลนี้:

```env
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=purrfect-spots-bucket
```

## 🚨 แก้ปัญหา

### ปัญหาที่พบบ่อย:
1. **500 Error** → ตรวจสอบการตั้งค่า AWS
2. **File too large** → ไฟล์ใหญ่เกิน 16MB
3. **Invalid file type** → รองรับแค่ jpg, png, gif
4. **Missing location** → ต้องใส่ location ด้วย

### ไฟล์ที่รองรับ:
- `.jpg`, `.jpeg`, `.png`, `.gif`
- ขนาดไม่เกิน 16MB

## 🔍 ตรวจสอบการทำงาน

```bash
# ตรวจสอบเซิร์ฟเวอร์
curl http://localhost:5000/health

# ตรวจสอบการตั้งค่า AWS
curl http://localhost:5000/config
```

---

Made with ❤️ for 🐱 lovers!


## 🔒 File Upload Restrictions

- **รองรับไฟล์**: PNG, JPG, JPEG, GIF, WEBP
- **ขนาดไฟล์สูงสุด**: 16MB
- **การปรับขนาด**: รูปภาพจะถูกปรับขนาดอัตโนมัติเป็น 1920x1080 (ถ้าใหญ่กว่า)
- **คุณภาพ**: JPEG quality 85% สำหรับ optimization

## 🚨 Error Responses

| HTTP Code | Description | Example |
|-----------|-------------|---------|
| `400` | Bad Request | `{"error": "No file provided"}` |
| `404` | Not Found | `{"error": "Endpoint not found"}` |
| `413` | Payload Too Large | `{"error": "File too large. Maximum size is 16MB"}` |
| `500` | Server Error | `{"error": "S3 is not configured"}` |

## 🛠️ Features

- ✅ **Unicode Support**: รองรับภาษาไทยใน metadata
- ✅ **Image Optimization**: ปรับขนาดและคุณภาพรูปภาพ
- ✅ **Unique Filenames**: สร้างชื่อไฟล์ unique ด้วย timestamp + UUID
- ✅ **CORS Support**: รองรับการเรียกใช้จาก frontend
- ✅ **Error Handling**: จัดการ error ครบถ้วน
- ✅ **AWS Integration**: เชื่อมต่อกับ S3 bucket จริง

## 🔍 Logging

Server จะแสดง log ข้อมูล:
- การเชื่อมต่อ AWS S3
- การอัปโหลดและลบไฟล์
- Error และ warning
- API request details

ตัวอย่าง log:
```
INFO:aws_config:S3 client initialized successfully
INFO:aws_config:Using bucket: purrfect-spots-bucket
INFO:aws_config:✅ S3 connection test passed
INFO:api_handlers:Successfully uploaded cat_20240120_103000_abc12345.jpg to S3
```
