-- Migration: Enable Realtime for notifications table
-- This allows Realtime listeners to receive events for the 'notifications' table

-- 1. Add 'notifications' table to 'supabase_realtime' publication
ALTER PUBLICATION supabase_realtime ADD TABLE notifications;
