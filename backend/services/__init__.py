"""
Backend Services Index

Export all services for easy importing:
- password_service: Password hashing, verification, and HIBP checking
- oauth_service: Google OAuth authentication
- user_service: User CRUD operations
- token_service: JWT token management
- email_service: Email sending operations
- gallery_service: Photo gallery operations
- cat_detection_service: Cat detection AI
- google_vision: Google Vision API integration
- storage_service: S3/Storage operations
- feature_flags: Feature flag management
"""

from services.email_service import EmailService, email_service
from services.feature_flags import FeatureFlagService, feature_flags
from services.password_service import PasswordService, password_service
from services.token_service import TokenService, get_token_service

__all__ = [
    # Password management
    "password_service",
    "PasswordService",
    # Token management
    "get_token_service",
    "TokenService",
    # Email service
    "email_service",
    "EmailService",
    # Feature flags
    "feature_flags",
    "FeatureFlagService",
]
