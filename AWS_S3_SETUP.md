# AWS S3 Setup Instructions for Purrfect Spots

## การตั้งค่า AWS S3 สำหรับ Purrfect Spots

### 1. สร้าง AWS Account
- ไปที่ [AWS Console](https://aws.amazon.com/)
- สร้าง account ใหม่หรือเข้าสู่ระบบ

### 2. สร้าง S3 Bucket

1. เข้าไปที่ AWS Console
2. ค้นหา "S3" ในช่องค้นหา
3. คลิก "Create bucket"
4. ตั้งค่าดังนี้:
   - **Bucket name**: เช่น `purrfect-spots-images-yourname`
   - **Region**: เลือก region ที่ใกล้ที่สุด (เช่น `ap-southeast-1` สำหรับ Singapore)
   - **Block Public Access**: ✅ ปิดการป้องกัน (เพื่อให้เข้าถึงรูปภาพได้)
   - **Bucket Versioning**: Disable (ถ้าไม่ต้องการเก็บ version)
   - **Server-side encryption**: Enable (แนะนำ)

### 3. ตั้งค่า Bucket Policy

1. ไปที่ bucket ที่สร้างแล้ว
2. คลิกแท็บ "Permissions"
3. เลื่อนไปที่ "Bucket policy"
4. คลิก "Edit" แล้วใส่ policy นี้:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*"
        }
    ]
}
```

**⚠️ สำคัญ**: เปลี่ยน `YOUR-BUCKET-NAME` เป็นชื่อ bucket ของคุณ

### 4. สร้าง IAM User

1. ไปที่ IAM service ใน AWS Console
2. คลิก "Users" จากเมนูด้านซ้าย
3. คลิก "Create user"
4. ตั้งชื่อ user เช่น `purrfect-spots-user`
5. เลือก "Attach policies directly"
6. คลิก "Create policy" แล้วใส่ policy นี้:

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
                "arn:aws:s3:::YOUR-BUCKET-NAME",
                "arn:aws:s3:::YOUR-BUCKET-NAME/*"
            ]
        }
    ]
}
```

7. ตั้งชื่อ policy เช่น `PurrfectSpotsS3Policy`
8. กลับไปที่ user creation และเลือก policy ที่เพิ่งสร้าง

### 5. สร้าง Access Key

1. หลังจากสร้าง user แล้ว คลิกที่ user name
2. คลิกแท็บ "Security credentials"
3. คลิก "Create access key"
4. เลือก "Application running outside AWS"
5. **เก็บ Access Key ID และ Secret Access Key ไว้อย่างปลอดภัย**

### 6. ตั้งค่าใน Backend

1. ไปที่ folder `backend`
2. คัดลอกไฟล์ `.env.example` เป็น `.env`
3. แก้ไขค่าในไฟล์ `.env`:

```env
AWS_ACCESS_KEY_ID=your_access_key_id_here
AWS_SECRET_ACCESS_KEY=your_secret_access_key_here
AWS_REGION=ap-southeast-1
S3_BUCKET_NAME=your-bucket-name-here
```

### 7. ทดสอบการเชื่อมต่อ

1. รันเซิร์ฟเวอร์ backend:
```bash
cd backend
python app.py
```

2. เปิดเบราว์เซอร์ไปที่ `http://localhost:5000/health`
3. ควรเห็นข้อความ:
```json
{
    "status": "healthy",
    "s3_configured": true,
    "bucket_name": "your-bucket-name"
}
```

### 8. ข้อควรระวัง

- ⚠️ **อย่าเปิดเผย Access Key และ Secret Key**
- ⚠️ **อย่า commit ไฟล์ `.env` ไปใน git**
- ⚠️ **ตรวจสอบว่า bucket policy ถูกต้อง**
- ⚠️ **ตรวจสอบ region ให้ตรงกัน**

### 9. หากมีปัญหา

#### ปัญหาที่พบบ่อย:
1. **403 Forbidden**: ตรวจสอบ bucket policy และ IAM permissions
2. **404 Not Found**: ตรวจสอบชื่อ bucket และ region
3. **CORS Error**: ตรวจสอบ CORS configuration ใน S3 bucket

#### CORS Configuration สำหรับ S3:
```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
        "AllowedOrigins": ["*"],
        "ExposeHeaders": ["ETag"]
    }
]
```

### 10. ค่าใช้จ่าย

- S3 มีค่าใช้จ่ายตาม:
  - จำนวนการเก็บข้อมูล (GB/เดือน)
  - จำนวนคำขอ (requests)
  - การโอนข้อมูล (data transfer)

- สำหรับการทดสอบ ค่าใช้จ่ายจะน้อยมาก
- ใช้ [AWS Pricing Calculator](https://calculator.aws/) เพื่อคำนวณค่าใช้จ่าย

### 11. Best Practices

1. **ตั้งชื่อ bucket ให้ unique**: ใช้ชื่อที่ไม่ซ้ำกับใครในโลก
2. **ใช้ lifecycle policies**: ลบไฟล์เก่าอัตโนมัติ
3. **Monitor costs**: ติดตามค่าใช้จ่ายใน AWS Console
4. **Enable versioning**: เก็บ version ของไฟล์ (ถ้าต้องการ)
5. **Use CloudFront**: สำหรับ CDN (ถ้าต้องการความเร็ว)

---

🐱 **Happy coding with Purrfect Spots!** 🐱
