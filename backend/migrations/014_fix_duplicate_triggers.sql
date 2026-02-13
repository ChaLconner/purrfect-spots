-- Migration: Remove duplicate trigger on photo_likes table
-- This fixes an issue where likes_count was being incremented twice

DROP TRIGGER IF EXISTS trigger_update_likes_count ON photo_likes;
