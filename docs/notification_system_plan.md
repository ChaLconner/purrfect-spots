# Phase D: Notification System Implementation Plan

## Overview
Implement a comprehensive notification system to alert users about interactions (Likes, Comments, Treats) and system info.

## Database Changes
- **New Table**: `notifications`
  - `id` (UUID, PK)
  - `user_id` (UUID, FK) - Recipient
  - `actor_id` (UUID, FK, Nullable) - Sender
  - `type` (VARCHAR) - 'like', 'comment', 'treat', 'system'
  - `title` (TEXT)
  - `message` (TEXT)
  - `resource_id` (UUID, Nullable) - e.g., Photo ID
  - `resource_type` (VARCHAR) - e.g., 'photo'
  - `is_read` (BOOLEAN, Default False)
  - `created_at` (TIMESTAMPTZ)

## Backend (FastAPI)
- **Service** (`backend/services/notification_service.py`):
  - `create_notification(...)`
  - `get_notifications(user_id, limit, offset)`
  - `mark_as_read(notification_id)`
  - `mark_all_as_read(user_id)`
- **Integration**:
  - Update `SocialService` to trigger notifications on Like (first time) and Comment.
  - Update `TreatsService` to trigger notification on Treat received.
- **Routes** (`backend/routes/notifications.py`):
  - GET `/api/v1/notifications`
  - PUT `/api/v1/notifications/{id}/read`
  - PUT `/api/v1/notifications/read-all`

## Frontend (Vue)
- **Service** (`frontend/src/services/notificationService.ts`)
- **Store** (`frontend/src/store/notificationStore.ts`):
  - Handle fetching.
  - **Realtime**: Subscribe to Supabase `notifications` table for the current user.
- **Components**:
  - `NotificationBell.vue`: Icon with unread badge.
  - `NotificationDropdown.vue` or `NotificationList.vue`: Display list.
