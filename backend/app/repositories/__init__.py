"""
Repositories package for data access abstraction layer
"""

from app.repositories.base_repository import BaseRepository
from app.repositories.user_repository import UserRepository

__all__ = ["BaseRepository", "UserRepository"]
