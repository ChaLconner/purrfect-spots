
-- 1. ลบ Policy อันตรายและซ้ำซ้อนใน cat_photos
DROP POLICY IF EXISTS "Enable read access for all users" ON public.cat_photos;

-- 2. Clean up Policy ใน users (เก็บไว้เฉพาะอันที่ปลอดภัยและจำเป็น)
-- ลบอันที่เปิดเผยข้อมูลเกินไป หรือซ้ำซ้อน
DROP POLICY IF EXISTS "Service can select users" ON public.users;
DROP POLICY IF EXISTS "Service can insert users" ON public.users;
DROP POLICY IF EXISTS "Users can read own data" ON public.users;
DROP POLICY IF EXISTS "Users can update own data" ON public.users;

-- ตรวจสอบและสร้าง Policy มาตรฐานสำหรับ users ถ้ายังไม่มี (ใช้ 'IF NOT EXISTS' ไม่ได้กับ CREATE POLICY ตรงๆ เลยต้อง Drop ก่อนเพื่อความชัวร์จากข้างบน แล้วเหลือชุด 'Allow ...' ไว้ หรือสร้างใหม่ถ้ายึดชุดนั้นเป็นหลัก)
-- จากข้อมูลเดิม ชุด 'Allow select own data' (Authenticated) ปลอดภัยกว่า 'Users can read own data' (Public)
-- ดังนั้นเราจะเก็บชุด 'Allow ...' ไว้ และอาจไม่ต้องทำอะไรเพิ่มกับ users ถ้าชุดนั้นยังอยู่
-- แต่เพื่อความชัวร์ เราจะ Drop ชุด 'Allow' แล้วสร้างใหม่ให้เป็นมาตรฐานเดียว (Best Practice naming)

DROP POLICY IF EXISTS "Allow insert own data" ON public.users;
DROP POLICY IF EXISTS "Allow select own data" ON public.users;
DROP POLICY IF EXISTS "Allow update own data" ON public.users;

-- สร้างใหม่: Users ดูข้อมูลตัวเองได้เท่านั้น
CREATE POLICY "users_read_own" ON public.users
FOR SELECT USING (auth.uid() = id);

-- สร้างใหม่: Users แก้ไขข้อมูลตัวเองได้เท่านั้น
CREATE POLICY "users_update_own" ON public.users
FOR UPDATE USING (auth.uid() = id);

-- หมายเหตุ: Insert มักจะทำผ่าน Trigger จาก Auth หรือถ้าจะให้ insert เองได้ต้องเช็ค id
CREATE POLICY "users_insert_own" ON public.users
FOR INSERT WITH CHECK (auth.uid() = id);


-- 3. เพิ่ม Index ที่ขาดหายไป
CREATE INDEX IF NOT EXISTS idx_token_blacklist_user_id ON public.token_blacklist(user_id);
-- เพิ่ม Index สำหรับ Foreign Key ต่างๆ เพื่อความเร็วในการ Join
CREATE INDEX IF NOT EXISTS idx_cat_photos_user_id ON public.cat_photos(user_id);

