-- 1. Add columns to users if not exist (for leaderboard)
ALTER TABLE users ADD COLUMN IF NOT EXISTS total_treats_given INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS total_treats_received INTEGER DEFAULT 0;

-- 2. Add columns to treats_transactions
ALTER TABLE treats_transactions ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE treats_transactions ADD COLUMN IF NOT EXISTS stripe_session_id TEXT;
-- Add unique constraint for idempotency on stripe_session_id
-- We use a DO block to safely add constraint only if it doesn't exist (though strictly speaking usually we just try/catch or drop/add)
-- Simpler approach: Drop if exists then Add
ALTER TABLE treats_transactions DROP CONSTRAINT IF EXISTS treats_transactions_stripe_session_id_key;
ALTER TABLE treats_transactions ADD CONSTRAINT treats_transactions_stripe_session_id_key UNIQUE (stripe_session_id);

-- 3. Create Atomic Function for Giving Treats
CREATE OR REPLACE FUNCTION give_treat_atomic(
  p_from_user_id UUID,
  p_photo_id UUID,
  p_amount INTEGER
)
RETURNS JSON AS $$
DECLARE
  v_from_balance INTEGER;
  v_to_user_id UUID;
BEGIN
  -- 3.1 Get photo owner and verify photo exists
  SELECT user_id INTO v_to_user_id FROM cat_photos WHERE id = p_photo_id;
  
  IF v_to_user_id IS NULL THEN
    RETURN json_build_object('success', false, 'error', 'Photo not found');
  END IF;

  -- 3.2 Check valid transaction (not self)
  IF p_from_user_id = v_to_user_id THEN
    RETURN json_build_object('success', false, 'error', 'Cannot give treats to yourself');
  END IF;

  -- 3.3 Lock sender row for update to prevent race conditions
  SELECT treat_balance INTO v_from_balance
  FROM users WHERE id = p_from_user_id FOR UPDATE;
  
  -- 3.4 Check balance
  IF v_from_balance < p_amount THEN
    RETURN json_build_object('success', false, 'error', 'Insufficient treats');
  END IF;
  
  -- 3.5 Perform updates
  -- Deduct from sender
  UPDATE users 
  SET treat_balance = treat_balance - p_amount,
      total_treats_given = COALESCE(total_treats_given, 0) + p_amount
  WHERE id = p_from_user_id;
  
  -- Add to receiver
  UPDATE users 
  SET treat_balance = treat_balance + p_amount,
      total_treats_received = COALESCE(total_treats_received, 0) + p_amount
  WHERE id = v_to_user_id;
  
  -- Log transaction
  INSERT INTO treats_transactions (from_user_id, to_user_id, photo_id, amount, transaction_type, description)
  VALUES (p_from_user_id, v_to_user_id, p_photo_id, p_amount, 'give', 'Gave treats to photo');
  
  RETURN json_build_object('success', true, 'new_balance', v_from_balance - p_amount);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
