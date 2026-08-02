CREATE OR REPLACE FUNCTION increment_treats(user_id UUID, amount INT)
RETURNS VOID AS $$
BEGIN
  UPDATE users SET treat_balance = treat_balance + amount WHERE id = user_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION decrement_treats(user_id UUID, amount INT)
RETURNS VOID AS $$
BEGIN
  UPDATE users SET treat_balance = treat_balance - amount WHERE id = user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
