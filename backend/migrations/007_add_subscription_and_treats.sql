-- Add subscription columns to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_pro BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_customer_id TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_end_date TIMESTAMP WITH TIME ZONE;

-- Add treats balance to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS treat_balance INTEGER DEFAULT 0;

-- Create treats_transactions table
CREATE TABLE IF NOT EXISTS treats_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_user_id UUID REFERENCES users(id),
    to_user_id UUID REFERENCES users(id),
    photo_id UUID REFERENCES cat_photos(id),
    amount INTEGER NOT NULL,
    transaction_type TEXT NOT NULL, -- 'give', 'purchase', 'daily_bonus'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_treats_from_user ON treats_transactions(from_user_id);
CREATE INDEX IF NOT EXISTS idx_treats_to_user ON treats_transactions(to_user_id);

-- RPC for safe atomic updates and checking balance
CREATE OR REPLACE FUNCTION increment_treats(user_id UUID, amount INTEGER)
RETURNS VOID AS $$
BEGIN
  UPDATE users
  SET treat_balance = treat_balance + amount
  WHERE id = user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION decrement_treats(user_id UUID, amount INTEGER)
RETURNS VOID AS $$
BEGIN
  UPDATE users
  SET treat_balance = treat_balance - amount
  WHERE id = user_id AND treat_balance >= amount;
  
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Insufficient treat balance';
  END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
