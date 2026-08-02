-- 1. เพิ่มฟิลด์สมาชิกและยอดขนมในตาราง users
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS is_pro BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS stripe_customer_id TEXT,
ADD COLUMN IF NOT EXISTS subscription_end_date TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS treat_balance INTEGER DEFAULT 0;

-- 2. ตาราง saved_spots (Pro feature: บันทึกจุดโปรด)
CREATE TABLE IF NOT EXISTS saved_spots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  photo_id UUID NOT NULL REFERENCES cat_photos(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  UNIQUE(user_id, photo_id)
);
CREATE INDEX IF NOT EXISTS idx_saved_spots_user ON saved_spots(user_id);

-- 3. ตาราง treats_transactions (ประวัติการให้/ซื้อขนม)
CREATE TABLE IF NOT EXISTS treats_transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  from_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  to_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  photo_id UUID REFERENCES cat_photos(id) ON DELETE SET NULL,
  amount INTEGER NOT NULL,
  transaction_type VARCHAR(20) NOT NULL, -- 'purchase', 'give', 'receive'
  stripe_payment_id TEXT,
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_treats_from ON treats_transactions(from_user_id);
CREATE INDEX IF NOT EXISTS idx_treats_to ON treats_transactions(to_user_id);

-- 4. RLS Policies
ALTER TABLE saved_spots ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage own saved spots" ON saved_spots
  FOR ALL USING (auth.uid() = user_id);

ALTER TABLE treats_transactions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view own transactions" ON treats_transactions
  FOR SELECT USING (auth.uid() = from_user_id OR auth.uid() = to_user_id);
