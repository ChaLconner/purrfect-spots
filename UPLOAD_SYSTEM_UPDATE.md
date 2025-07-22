# การอัปเดตระบบ User-specific Uploads

## การเปลี่ยนแปลงที่ทำไป

### 1. Database Schema (Backend)
- สร้าง migration ไฟล์ใหม่ `004_create_cat_photos_table.sql`
- เพิ่ม column `user_id` ในตาราง `cat_photos` เพื่อระบุเจ้าของรูปภาพ
- เพิ่ม foreign key ที่เชื่อม `user_id` กับตาราง `users`
- เพิ่ม RLS (Row Level Security) policies:
  - ทุกคนสามารถดูรูปได้ (SELECT)
  - เฉพาะเจ้าของรูปเท่านั้นที่สามารถ INSERT, UPDATE, DELETE ได้

### 2. Backend API Changes
- **Upload Route** (`/upload/cat`):
  - เพิ่ม authentication requirement โดยใช้ `get_current_user` dependency
  - เพิ่ม `user_id` ลงในข้อมูลที่บันทึกเมื่ออัปโหลดรูป
  
- **Profile Route** (`/profile/uploads`):
  - ปรับปรุง route ที่มีอยู่แล้วให้ทำงานกับ schema ใหม่
  - แก้ไข field mapping (`image_url` แทน `url`)
  - เพิ่มข้อมูล `location_name`, `latitude`, `longitude`

### 3. Frontend Changes
- **Upload Component** (`Upload.vue`):
  - มีการตรวจสอบการยืนยันตัวตนแล้ว
  - ใช้ `getAuthHeader()` ส่ง Authorization header
  - Redirect ไป login หากไม่ได้ยืนยันตัวตน

- **Profile View** (`ProfileView.vue`):
  - แท็บ "My Uploads" แสดงเฉพาะรูปที่ user ปัจจุบันอัปโหลด
  - เรียก API `/profile/uploads` ด้วย authentication
  - แสดงรูปในรูปแบบ grid พร้อมข้อมูล location และวันที่
  - เพิ่ม loading state และ error handling
  - Modal แสดงรูปแบบเต็มพร้อมข้อมูลรายละเอียด

- **Profile Service** (`profileService.ts`):
  - ปรับปรุง `getUserUploads()` method ให้เรียกใช้ endpoint ที่ถูกต้อง
  - เพิ่ม interface สำหรับ Upload type ที่มี fields เพิ่มเติม

### 4. หน้า "My Uploads View" ถูกยกเลิก
- ลบไฟล์ `MyUploadsView.vue` ออก
- ลบ route `/my-uploads` 
- ลบลิงค์จาก navigation
- ใช้แท็บใน ProfileView แทน

## วิธีการใช้งาน

### สำหรับผู้ใช้:
1. **ล็อกอิน**: ผู้ใช้ต้องล็อกอินก่อนจึงจะสามารถอัปโหลดรูปได้
2. **อัปโหลดรูป**: ไปที่หน้า Upload และอัปโหลดรูปแมว
3. **ดูรูปของตนเอง**: ไปที่ Profile → แท็บ "My Uploads"

### สำหรับ Developer:
1. **รัน Migration**: ต้องรัน SQL ใน `004_create_cat_photos_table.sql` ใน Supabase
2. **ตั้งค่า Authentication**: ตรวจสอบให้แน่ใจว่า JWT tokens ทำงานถูกต้อง
3. **RLS Policies**: Supabase จะ enforce policies ตามที่กำหนด

## Migration SQL Command

```bash
# รันสคริปต์นี้เพื่อดู SQL commands
./run_migration.sh
# หรือ (Windows)
run_migration.bat
```

## API Endpoints

### POST `/upload/cat`
- **Authentication**: Required
- **Description**: อัปโหลดรูปแมวพร้อม metadata
- **Auto-add**: `user_id` จาก authenticated user

### GET `/profile/uploads`
- **Authentication**: Required  
- **Description**: ดึงรูปที่ user ปัจจุบันอัปโหลด
- **Response**: Array ของรูปภาพพร้อมข้อมูล location

## การทำงานของ RLS (Row Level Security)

- **SELECT**: ทุกคนสามารถดูรูปทั้งหมดได้ (สำหรับหน้า Map และ Gallery)
- **INSERT**: เฉพาะ authenticated user สามารถ insert ได้ (และต้องเป็น user_id ของตนเอง)
- **UPDATE/DELETE**: เฉพาะเจ้าของรูป (user_id ตรงกัน) ถึงจะแก้ไขหรือลบได้

## Frontend Features

### Profile View - My Uploads Tab:
- **Loading State**: แสดงสปินเนอร์ขณะโหลดข้อมูล
- **Error Handling**: แสดงข้อความผิดพลาดและปุ่มลองใหม่
- **Empty State**: แสดงข้อความและปุ่มไปหน้าอัปโหลดเมื่อไม่มีรูป
- **Grid Layout**: แสดงรูปแบบ responsive grid
- **Image Modal**: คลิกรูปเพื่อดูแบบเต็มพร้อมข้อมูลรายละเอียด
- **Upload Info**: แสดงจำนวนรูป, ชื่อสถานที่, วันที่อัปโหลด

### Upload Component:
- **Authentication Check**: ตรวจสอบการล็อกอินก่อนอัปโหลด
- **Auto Redirect**: นำไปหน้าล็อกอินหากยังไม่ได้ยืนยันตัวตน
- **Success Handling**: รีเฟรชหน้าหลังอัปโหลดสำเร็จ

## การทดสอบระบบ

```bash
# รัน backend
cd backend
python -m uvicorn main:app --reload

# รัน frontend (terminal ใหม่)
cd frontend  
npm run dev

# ทดสอบ API (หลังจากมี JWT token)
./test_profile_api.sh
# หรือ (Windows)
test_profile_api.bat
```

รูปแบบการทำงานนี้ทำให้ระบบมีความปลอดภัยมากขึ้น และผู้ใช้สามารถจัดการรูปของตนเองได้อย่างสะดวกผ่านหน้า Profile
