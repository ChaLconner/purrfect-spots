# Supabase Auth Pattern Implementation

## การเปลี่ยนแปลงหลัก

### 1. ใช้ auth.uid() เป็น Primary Key
- **เก่า**: ใช้ `google_id` (string ตัวเลข) เป็น primary key
- **ใหม่**: ใช้ `user["sub"]` (UUID) จาก Supabase JWT เป็น primary key

### 2. JWT Token Format (Supabase Compatible)
```json
{
  "sub": "uuid-here",           // auth.uid()
  "email": "user@example.com",
  "user_metadata": {
    "name": "User Name",
    "avatar_url": "https://...",
    "provider_id": "google-id"   // optional
  },
  "app_metadata": {
    "provider": "google"
  }
}
```

### 3. Upsert Pattern ที่ถูกต้อง
```python
supabase.table("users").upsert({
    "id": user_id,                        # ← auth.uid() จาก JWT
    "email": user["email"],
    "name": user["user_metadata"]["name"],
    "picture": user["user_metadata"]["avatar_url"],
    "google_id": user["user_metadata"].get("provider_id"),  # optional
}, on_conflict="id").execute()
```

## ไฟล์ที่แก้ไข

### auth_service.py
- `create_or_get_user()`: ใช้ `user_data.get('id')` หรือ `user_data.get('sub')` เป็น primary key
- `exchange_google_code()`: สร้าง UUID สำหรับ auth.uid() แทนการใช้ google_id
- `create_access_token()`: ส่ง user_metadata ในรูปแบบ Supabase

### auth_google.py
- `/sync-user`: ใช้ pattern ที่ถูกต้องในการ upsert
- ลบ endpoint ซ้ำกัน
- ใช้ `user["sub"]` เป็น user_id

### auth_middleware.py
- รองรับ Supabase JWKS verification
- Fallback ไปใช้ custom token
- ส่ง user data จาก JWT payload

## การทดสอบ

1. ลองใช้ Google OAuth login
2. ตรวจสอบว่า JWT มี user_metadata
3. เรียก `/sync-user` endpoint
4. ยืนยันว่าข้อมูลถูก upsert ด้วย auth.uid()

## Database Schema

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,           -- auth.uid() จาก Supabase
    email VARCHAR NOT NULL,
    name VARCHAR,
    picture VARCHAR,
    google_id VARCHAR,             -- reference เก่า (optional)
    bio TEXT,
    password_hash VARCHAR,         -- สำหรับ email/password users
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

## การใช้งาน

### Frontend (OAuth Callback)
```typescript
// หลัง OAuth success
const token = response.access_token;
await AuthService.syncUser(token);
```

### Backend (JWT Creation)
```python
# สร้าง JWT พร้อม user_metadata
jwt_token = auth_service.create_access_token(user_uuid, {
    "email": email,
    "name": name, 
    "picture": picture,
    "google_id": google_sub
})
```
