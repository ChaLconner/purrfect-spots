CREATE OR REPLACE VIEW admin_comment_list AS
SELECT 
    c.id,
    c.content,
    c.user_id,
    c.photo_id,
    c.created_at,
    u.name as user_display_name,
    u.username as user_username,
    u.picture as user_avatar,
    (SELECT count(*) FROM reports r WHERE r.comment_id = c.id AND r.status = 'pending') as report_count
FROM photo_comments c
LEFT JOIN users u ON c.user_id = u.id;

