-- Function for atomic purchase handling (Idempotency + Balance Update)
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
    RETURN json_build_object('success', true, 'message', 'Transaction already processed', 'duplicate', true);
  END IF;

  -- 2. Update User Balance
  UPDATE users 
  SET treat_balance = treat_balance + p_amount
  WHERE id = p_user_id
  RETURNING treat_balance INTO v_new_balance;

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
