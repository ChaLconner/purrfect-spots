-- Migration 010: Optimize give_treat_atomic RPC
-- Returns to_user_id in the result to eliminate an extra DB query for notifications

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
  -- 1. Get photo owner and verify photo exists
  SELECT user_id INTO v_to_user_id FROM cat_photos WHERE id = p_photo_id;
  
  IF v_to_user_id IS NULL THEN
    RETURN json_build_object('success', false, 'error', 'Photo not found');
  END IF;

  -- 2. Check valid transaction (not self)
  IF p_from_user_id = v_to_user_id THEN
    RETURN json_build_object('success', false, 'error', 'Cannot give treats to yourself');
  END IF;

  -- 3. Lock sender row for update to prevent race conditions
  SELECT treat_balance INTO v_from_balance
  FROM users WHERE id = p_from_user_id FOR UPDATE;
  
  -- 4. Check balance
  IF v_from_balance < p_amount THEN
    RETURN json_build_object('success', false, 'error', 'Insufficient treats');
  END IF;
  
  -- 5. Perform updates atomically
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
  
  -- Return to_user_id so application layer can send notification without extra query
  RETURN json_build_object(
    'success', true, 
    'new_balance', v_from_balance - p_amount,
    'to_user_id', v_to_user_id
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Ensure purchase_treats_atomic also handles edge cases
CREATE OR REPLACE FUNCTION purchase_treats_atomic(
  p_user_id UUID,
  p_amount INTEGER,
  p_description TEXT,
  p_stripe_session_id TEXT
)
RETURNS JSON AS $$
DECLARE
  v_new_balance INTEGER;
BEGIN
  -- 1. Check if transaction already exists (Idempotency)
  IF EXISTS (SELECT 1 FROM treats_transactions WHERE stripe_session_id = p_stripe_session_id) THEN
    -- Return existing balance for idempotent response
    SELECT treat_balance INTO v_new_balance FROM users WHERE id = p_user_id;
    RETURN json_build_object('success', true, 'message', 'Transaction already processed', 'duplicate', true, 'new_balance', v_new_balance);
  END IF;

  -- 2. Lock and Update User Balance
  UPDATE users 
  SET treat_balance = treat_balance + p_amount
  WHERE id = p_user_id
  RETURNING treat_balance INTO v_new_balance;

  IF v_new_balance IS NULL THEN
    RETURN json_build_object('success', false, 'error', 'User not found');
  END IF;

  -- 3. Insert Transaction Record
  INSERT INTO treats_transactions (
    to_user_id, 
    amount, 
    transaction_type, 
    description, 
    stripe_session_id
  ) VALUES (
    p_user_id,
    p_amount,
    'purchase',
    p_description,
    p_stripe_session_id
  );

  RETURN json_build_object('success', true, 'new_balance', v_new_balance, 'duplicate', false);

EXCEPTION WHEN OTHERS THEN
  RETURN json_build_object('success', false, 'error', SQLERRM);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
