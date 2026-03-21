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
        except Exception:
            logger.debug("Password verification failed")
            return False

    def validate_complexity(self, password: str) -> bool:
        """
        Validate password complexity:
        - At least 8 characters
        - Includes uppercase, lowercase, numbers, and special characters
        """
        if len(password) < self.MIN_PASSWORD_LENGTH:
            return False

        import re

        # Regex for uppercase, lowercase, digit, and special char
        has_upper = re.search(r"[A-Z]", password)
        has_lower = re.search(r"[a-z]", password)
        has_digit = re.search(r"\d", password)
        has_special = re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)

        return all([has_upper, has_lower, has_digit, has_special])

    async def is_password_pwned(self, password: str) -> bool:
        """
        Check if password has been leaked in data breaches using HIBP API.
        Uses k-Anonymity to preserve privacy (only sends first 5 chars of SHA-1 hash).
        """
        try:
            # SHA1 is required by the HIBP k-Anonymity API protocol.
            # We ONLY use this hash for data breach checks, NEVER for storage or authentication.
            # usedforsecurity=False explicitly marks this as non-cryptographic usage.
            encoded_pwd = password.encode("utf-8")
            # nosemgrep: python.lang.security.insecure-hash-algorithms.insecure-hash-algorithm-sha1
            # codeql[py/weak-sensitive-data-hashing, py/weak-cryptographic-algorithm] Justification: SHA1 is strictly required by the HIBP k-anonymity API protocol.
            sha1_algo = hashlib.sha1(encoded_pwd, usedforsecurity=False)  # nosec B324 # NOSONAR
            sha1_password = sha1_algo.hexdigest().upper()
            prefix = sha1_password[:5]
            suffix = sha1_password[5:]

            async with httpx.AsyncClient() as client:
                response = await client.get(f"https://api.pwnedpasswords.com/range/{prefix}", timeout=2.0)
                if response.status_code == 200:
                    lines = response.text.splitlines()
                    for line in lines:
                        if line.startswith(suffix):
                            return True
        except Exception:
            logger.warning("HIBP check failed (skipping)")
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
