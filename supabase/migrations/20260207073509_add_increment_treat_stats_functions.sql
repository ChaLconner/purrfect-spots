CREATE OR REPLACE FUNCTION increment_total_treats_received(user_id uuid, amount int)
RETURNS void
LANGUAGE sql
SECURITY DEFINER
AS $$
  UPDATE users
  SET total_treats_received = COALESCE(total_treats_received, 0) + amount
  WHERE id = user_id;
$$;

CREATE OR REPLACE FUNCTION increment_total_treats_given(user_id uuid, amount int)
RETURNS void
LANGUAGE sql
SECURITY DEFINER
AS $$
  UPDATE users
  SET total_treats_given = COALESCE(total_treats_given, 0) + amount
  WHERE id = user_id;
$$;
