"""
Password management service for password hashing, verification, and security checks

Handles:
- Password hashing with bcrypt
- Password verification
- Password complexity validation
- HIBP (Have I Been Pwned) breach checking
"""

import hashlib

import bcrypt
import httpx

from logger import logger


class PasswordService:
    """Service for password-related operations"""

    MIN_PASSWORD_LENGTH = 8

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
        except Exception as e:
            logger.debug(f"Password verification failed: {e}")
            return False

    def validate_complexity(self, password: str) -> bool:
        """
        Validate password complexity:
        - At least 8 characters
        """
        if len(password) < self.MIN_PASSWORD_LENGTH:
            return False
        return True

    async def is_password_pwned(self, password: str) -> bool:
        """
        Check if password has been leaked in data breaches using HIBP API.
        Uses k-Anonymity to preserve privacy (only sends first 5 chars of SHA-1 hash).
        """
        try:
            sha1_password = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()  # nosec B324
            prefix = sha1_password[:5]
            suffix = sha1_password[5:]

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.pwnedpasswords.com/range/{prefix}",
                    timeout=2.0
                )
                if response.status_code == 200:
                    lines = response.text.splitlines()
                    for line in lines:
                        if line.startswith(suffix):
                            return True
        except Exception as e:
            logger.warning(f"HIBP check failed (skipping): {e}")
        return False

    async def validate_new_password(self, password: str, check_breach: bool = True) -> tuple[bool, str | None]:
        """
        Validate a new password for all security requirements.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check complexity
        if not self.validate_complexity(password):
            return False, f"Password must be at least {self.MIN_PASSWORD_LENGTH} characters long"

        # Check for data breaches
        if check_breach and await self.is_password_pwned(password):
            return False, "This password has been found in a data breach. Please choose a different password."

        return True, None


# Singleton instance
password_service = PasswordService()
