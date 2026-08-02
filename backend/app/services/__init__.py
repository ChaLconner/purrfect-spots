"""
Backend Services Package

Export all main service classes and singleton instances for clean importing across the application:
- AuthService
- UserService
- GalleryService
- PasswordService, password_service
- TokenService, get_token_service
- EmailService, email_service
- FeatureFlagService, feature_flags
- NotificationService
- OTPService
- SearchService
- SeoService
- SocialService
- TreatsService
- QuotaService
- StorageService
- CatDetectionService
"""

from app.services.auth_service import AuthService
from app.services.cat_detection_service import CatDetectionService
from app.services.email_service import EmailService, email_service
from app.services.feature_flags import FeatureFlagService, feature_flags
from app.services.gallery_service import GalleryService
from app.services.notification_service import NotificationService
from app.services.otp_service import OTPService
from app.services.password_service import PasswordService, password_service
from app.services.quota_service import QuotaService
from app.services.search_service import SearchService
from app.services.seo_service import SeoService
from app.services.social_service import SocialService
from app.services.storage_service import StorageService
from app.services.token_service import TokenService, get_token_service
from app.services.treats_service import TreatsService
from app.services.user_service import UserService

__all__ = [
    # Core services
    "AuthService",
    "UserService",
    "GalleryService",
    # Password management
    "PasswordService",
    "password_service",
    # Token management
    "TokenService",
    "get_token_service",
    # Email service
    "EmailService",
    "email_service",
    # Feature flags
    "FeatureFlagService",
    "feature_flags",
    # Domain services
    "CatDetectionService",
    "NotificationService",
    "OTPService",
    "QuotaService",
    "SearchService",
    "SeoService",
    "SocialService",
    "StorageService",
    "TreatsService",
]
