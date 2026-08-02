CREATE OR REPLACE FUNCTION public.give_treat_atomic(p_from_user_id uuid, p_photo_id uuid, p_amount integer)
 RETURNS json
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public', 'pg_temp'
AS $function$
DECLARE
  v_from_balance INTEGER;
  v_to_user_id UUID;
  v_auth_user_id UUID;
BEGIN
  -- 1. SECURITY: Verify caller identity
  v_auth_user_id := auth.uid();
  IF v_auth_user_id IS NULL OR p_from_user_id <> v_auth_user_id THEN
    RETURN json_build_object('success', false, 'error', 'Unauthenticated or identity mismatch');
  END IF;

  -- 2. VALIDATION: Amount must be positive
  IF p_amount <= 0 THEN
    RETURN json_build_object('success', false, 'error', 'Amount must be greater than zero');
  END IF;

  -- 3. VALIDATION: Verify photo exists and get owner
  SELECT user_id INTO v_to_user_id FROM cat_photos WHERE id = p_photo_id;
  
  IF v_to_user_id IS NULL THEN
    RETURN json_build_object('success', false, 'error', 'Photo not found');
  END IF;

  -- 4. VALIDATION: Check valid transaction (not self)
  IF p_from_user_id = v_to_user_id THEN
    RETURN json_build_object('success', false, 'error', 'Cannot give treats to yourself');
  END IF;

  -- 5. TRANSACTIONAL: Lock sender row for update to prevent race conditions
  -- Important: Lock is held until transaction end
  SELECT treat_balance INTO v_from_balance
  FROM users WHERE id = p_from_user_id FOR UPDATE;
  
  -- 6. VALIDATION: Check balance
  IF v_from_balance < p_amount THEN
    RETURN json_build_object('success', false, 'error', 'Insufficient treats');
  END IF;
  
  -- 7. EXECUTION: Perform updates
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
  
  -- 8. AUDIT: Log transaction
  -- Note: treats_transactions table should have RLS to prevent direct tampering
  INSERT INTO treats_transactions (from_user_id, to_user_id, photo_id, amount, transaction_type, description)
  VALUES (p_from_user_id, v_to_user_id, p_photo_id, p_amount, 'give', 'Gave treats to photo');
  
  RETURN json_build_object('success', true, 'new_balance', v_from_balance - p_amount);
END;
$function$;
