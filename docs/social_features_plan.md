# Phase B: Social Features Implementation Plan

## Overview
Implement social interaction features allow users to engage with cat photos through Likes and Comments. This phase also includes database optimizations (counters) for performance.

## Database Changes
- **New Table**: `photo_likes`
  - `user_id` (UUID, FK)
  - `photo_id` (UUID, FK)
  - `created_at` (Timestamp)
  - PK: Composite (`user_id`, `photo_id`)
- **New Table**: `photo_comments`
  - `id` (UUID, PK)
  - `user_id` (UUID, FK)
  - `photo_id` (UUID, FK)
  - `content` (Text)
  - `created_at` (Timestamp)
  - `updated_at` (Timestamp)
- **Table Updates**: `cat_photos`
  - Add `likes_count` (Integer, Default 0)
  - Add `comments_count` (Integer, Default 0)
- **Functions & Triggers**:
  - Auto-increment/decrement counts on insert/delete for likes/comments.

## Backend (FastAPI)
- **Schemas** (`backend/schemas/social.py`):
  - `CommentCreate`, `CommentResponse`, `CommentUpdate`
  - `LikeResponse`
- **Service** (`backend/services/social_service.py`):
  - `toggle_like(user_id, photo_id)`
  - `add_comment(user_id, photo_id, content)`
  - `delete_comment(user_id, comment_id)`
  - `get_comments(photo_id)`
- **Routes** (`backend/routes/social.py`):
  - POST `/api/v1/social/photos/{id}/like`
  - POST `/api/v1/social/photos/{id}/comments`
  - GET `/api/v1/social/photos/{id}/comments`
  - DELETE `/api/v1/social/comments/{id}`

## Frontend (Vue)
- **Service** (`frontend/src/services/socialService.ts`)
- **Components**:
  - `LikeButton.vue`: Heart icon with animation.
  - `CommentList.vue`: List of comments with "Add Comment" input.
- **Integration**:
  - Update `GalleryModal` and `GalleryView` to display like/comment counts and include interaction components.
