-- Create a function to get leaderboard data based on time period
CREATE OR REPLACE FUNCTION get_leaderboard(p_period TEXT)
RETURNS TABLE (
    id UUID,
    name TEXT,
    username TEXT,
    picture TEXT,
    total_treats_received BIGINT
) AS $$
BEGIN
    IF p_period = 'all_time' THEN
        RETURN QUERY
        SELECT 
            u.id, 
            u.name, 
            u.username, 
            u.picture, 
            COALESCE(u.total_treats_received, 0)::BIGINT as total_treats_received
        FROM users u
        ORDER BY total_treats_received DESC
        LIMIT 10;
        
    ELSE
        RETURN QUERY
        SELECT 
            u.id, 
            u.name, 
            u.username, 
            u.picture, 
            COALESCE(SUM(t.amount), 0)::BIGINT as total_treats_received
        FROM treats_transactions t
        JOIN users u ON t.to_user_id = u.id
        WHERE t.transaction_type = 'give'
        AND (
            (p_period = 'weekly' AND t.created_at >= NOW() - INTERVAL '1 week')
            OR
            (p_period = 'monthly' AND t.created_at >= NOW() - INTERVAL '1 month')
        )
        GROUP BY u.id, u.name, u.username, u.picture
        ORDER BY total_treats_received DESC
        LIMIT 10;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
