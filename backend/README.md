# Purrfect Spots Backend

Flask backend สำหรับ Purrfect Spots application พร้อมกับการเชื่อมต่อ AWS S3 สำหรับการอัพโหลดรูปภาพ

## การติดตั้ง

1. สร้าง virtual environment:
```bash
python -m venv venv
```

2. เปิดใช้งาน virtual environment:
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

3. ติดตั้ง dependencies:
```bash
pip install -r requirements.txt
```

4. ตั้งค่า environment variables:
```bash
cp .env.example .env
```

แก้ไขไฟล์ `.env` ด้วยข้อมูล AWS ของคุณ:
```
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your_s3_bucket_name
```

## การใช้งาน

### เริ่มต้นเซิร์ฟเวอร์
```bash
python app.py
```

เซิร์ฟเวอร์จะทำงานที่ `http://localhost:5000`

### API Endpoints

#### 1. Health Check
```
GET /health
```
ตรวจสอบสถานะเซิร์ฟเวอร์และการเชื่อมต่อ S3

#### 2. Upload Image
```
POST /upload
```
อัพโหลดรูปภาพไปยัง S3 bucket

**Parameters:**
- `file`: ไฟล์รูปภาพ (form-data)
- `location`: ชื่อสถานที่ (optional)
- `description`: คำอธิบาย (optional)  
- `latitude`: ละติจูด (optional)
- `longitude`: ลองจิจูด (optional)

**Response:**
```json
{
  "message": "Image uploaded successfully",
  "filename": "image_20250704_123456_abc123.jpg",
  "url": "https://your-bucket.s3.amazonaws.com/image_20250704_123456_abc123.jpg",
  "metadata": {
    "location": "Bangkok",
    "description": "Beautiful cat",
    "latitude": "13.7563",
    "longitude": "100.5018",
    "upload_timestamp": "2025-07-04T12:34:56",
    "original_filename": "cat.jpg"
  }
}
```

#### 3. List Images
```
GET /images
```
ดูรายการรูปภาพทั้งหมดใน S3 bucket

#### 4. Delete Image
```
DELETE /delete/<filename>
```
ลบรูปภาพจาก S3 bucket

#### 5. Get Configuration
```
GET /config
```
ดูสถานะการตั้งค่า AWS และ S3

## AWS S3 Setup

### 1. สร้าง S3 Bucket
1. เข้าไปที่ AWS Console
2. ไปที่ S3 service
3. สร้าง bucket ใหม่
4. ตั้งค่า bucket policy เพื่อให้สามารถเข้าถึงแบบ public ได้

### 2. สร้าง IAM User
1. ไปที่ IAM service
2. สร้าง User ใหม่
3. แนบ policy ต่อไปนี้:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::your-bucket-name",
                "arn:aws:s3:::your-bucket-name/*"
            ]
        }
    ]
}
```

### 3. Bucket Policy (สำหรับการเข้าถึงแบบ public)
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::your-bucket-name/*"
        }
    ]
}
```

## Features

- ✅ อัพโหลดรูปภาพไปยัง AWS S3
- ✅ ปรับขนาดและคุณภาพรูปภาพอัตโนมัติ
- ✅ สนับสนุนไฟล์ประเภท: PNG, JPG, JPEG, GIF, WebP
- ✅ เก็บ metadata ของรูปภาพ (สถานที่, คำอธิบาย, พิกัด)
- ✅ สร้างชื่อไฟล์ที่ไม่ซ้ำกัน
- ✅ CORS support สำหรับ frontend
- ✅ Error handling และ logging
- ✅ ตรวจสอบขนาดไฟล์ (สูงสุด 16MB)

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | AWS Access Key ID | - |
| `AWS_SECRET_ACCESS_KEY` | AWS Secret Access Key | - |
| `AWS_REGION` | AWS Region | us-east-1 |
| `S3_BUCKET_NAME` | S3 Bucket Name | - |
| `FLASK_ENV` | Flask Environment | development |
| `FLASK_DEBUG` | Flask Debug Mode | True |

## Error Handling

- **400 Bad Request**: ไฟล์ไม่ถูกส่งมา หรือไฟล์ประเภทไม่ถูกต้อง
- **413 Request Entity Too Large**: ไฟล์ขนาดใหญ่เกิน 16MB
- **500 Internal Server Error**: เกิดข้อผิดพลาดใน S3 หรือเซิร์ฟเวอร์

## การทดสอบด้วย curl

```bash
# Upload image
curl -X POST \
  -F "file=@/path/to/image.jpg" \
  -F "location=Bangkok" \
  -F "description=Beautiful cat" \
  -F "latitude=13.7563" \
  -F "longitude=100.5018" \
  http://localhost:5000/upload

# List images
curl http://localhost:5000/images

# Health check
curl http://localhost:5000/health
```
