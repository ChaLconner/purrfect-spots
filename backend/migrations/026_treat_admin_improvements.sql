-- Migration: Admin Treats Improvements
-- Adds RPC functions for atomic treat granting and aggregated stats

-- 1. Atomic admin grant function (avoids read-then-write race condition)
CREATE OR REPLACE FUNCTION admin_grant_treats(
    p_user_id UUID,
    p_amount INT
)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    IF p_amount < 1 OR p_amount > 10000 THEN
        RAISE EXCEPTION 'Amount must be between 1 and 10000';
    END IF;

    UPDATE users
    SET treat_balance = treat_balance + p_amount
    WHERE id = p_user_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'User not found';
    END IF;
END;
$$;

-- 2. Aggregated treat stats (single query instead of fetching all rows)
CREATE OR REPLACE FUNCTION get_treat_admin_stats()
RETURNS TABLE (
    total_in_circulation BIGINT,
    total_given_to_cats BIGINT,
    user_count_with_balance BIGINT
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        COALESCE(SUM(treat_balance), 0)::BIGINT AS total_in_circulation,
        COALESCE(SUM(total_treats_received), 0)::BIGINT AS total_given_to_cats,
        COUNT(*) FILTER (WHERE treat_balance > 0)::BIGINT AS user_count_with_balance
    FROM users;
$$;
