# 🔐 AWS IAM Policy สำหรับ Purrfect Spots

คุณต้องอัปเดต IAM Policy เพื่อให้ User สามารถเข้าถึง S3 bucket ได้อย่างครบถ้วน

## ⚠️ ปัญหาที่พบ
```
User: arn:aws:iam::246217239517:user/purrfect-spots-chal is not authorized to perform: s3:ListBucket
```

## 🔧 วิธีแก้ไข

### 1. เข้าไปที่ AWS Console
- ไปที่ IAM Service
- คลิก "Users" 
- คลิกที่ User: `purrfect-spots-chal`

### 2. อัปเดต Policy
คลิกแท็บ "Permissions" แล้วแก้ไข Policy เป็น:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket",
                "s3:GetBucketLocation"
            ],
            "Resource": "arn:aws:s3:::purrfect-spots-bucket"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:PutObjectAcl"
            ],
            "Resource": "arn:aws:s3:::purrfect-spots-bucket/*"
        }
    ]
}
```

### 3. สิทธิ์ที่จำเป็น
- `s3:ListBucket` - ดูรายการไฟล์ใน bucket
- `s3:GetBucketLocation` - ตรวจสอบตำแหน่ง bucket
- `s3:GetObject` - ดาวน์โหลดไฟล์
- `s3:PutObject` - อัปโหลดไฟล์
- `s3:DeleteObject` - ลบไฟล์
- `s3:PutObjectAcl` - ตั้งค่า public access

### 4. ทดสอบหลังจากอัปเดต
1. รีสตาร์ท backend server
2. ลองอัปโหลดรูปภาพใหม่
3. ตรวจสอบใน Gallery

## 🚨 หมายเหตุ
- Resource ต้องตรงกับชื่อ bucket ของคุณ: `purrfect-spots-bucket`
- หากชื่อ bucket ต่างกัน ให้เปลี่ยนในทั้ง 2 ที่
- Policy นี้จะให้สิทธิ์เฉพาะ bucket ที่ระบุเท่านั้น
