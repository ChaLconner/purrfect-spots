"""
Data Encryption Service for Purrfect Spots

Provides encryption/decryption for sensitive configuration values
and personal data stored in the database.

Uses Fernet symmetric encryption (AES-128-CBC) for field-level encryption.
"""

import base64
import os
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv

from logger import logger

# Load .env from backend directory
load_dotenv()


class EncryptionService:
    """
    Service for encrypting and decrypting sensitive data.

    Uses Fernet symmetric encryption which provides:
    - Confidentiality: Data is encrypted with AES-128-CBC
    - Integrity: HMAC-SHA256 ensures data hasn't been tampered with
    - Authenticity: Only holders of the key can decrypt

    Key Management:
    - ENCRYPTION_KEY environment variable (base64-encoded Fernet key)
    - If not set, generates a new key (WARNING: data will be lost on restart)
    """

    def __init__(self) -> None:
        self._fernet: Fernet | None = None
        self._key_initialized = False

    def _initialize(self) -> None:
        """Initialize the Fernet cipher with the encryption key."""
        if self._key_initialized:
            return

        key = os.getenv("ENCRYPTION_KEY")

        if not key:
            # Generate a new key for development
            import warnings

            key = Fernet.generate_key().decode()
            warnings.warn(
                f"ENCRYPTION_KEY not set. Generated a development key: {key[:20]}...\n"
                "Add this to your .env file to persist encrypted data across restarts.",
                UserWarning,
                stacklevel=2,
            )
            os.environ["ENCRYPTION_KEY"] = key

        try:
            # Ensure key is properly formatted
            if len(key) == 44 and key.endswith("="):
                self._fernet = Fernet(key.encode())
            else:
                # Try to decode as base64
                decoded = base64.urlsafe_b64decode(key)
                if len(decoded) != 32:
                    raise ValueError("Encryption key must be 32 bytes (44 base64 characters)")
                self._fernet = Fernet(key.encode() if len(key) == 44 else base64.urlsafe_b64encode(decoded))
        except Exception as e:
            logger.error(f"Failed to initialize encryption service: {e}")
            raise

        self._key_initialized = True

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a string value.

        Args:
            plaintext: The string to encrypt

        Returns:
            Base64-encoded encrypted string
        """
        self._initialize()
        if not self._fernet:
            raise RuntimeError("Encryption service not initialized")

        try:
            encrypted = self._fernet.encrypt(plaintext.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt an encrypted string value.

        Args:
            ciphertext: The base64-encoded encrypted string

        Returns:
            Decrypted plaintext string
        """
        self._initialize()
        if not self._fernet:
            raise RuntimeError("Encryption service not initialized")

        try:
            decrypted = self._fernet.decrypt(ciphertext.encode())
            return decrypted.decode()
        except InvalidToken:
            logger.error("Decryption failed: Invalid token (key mismatch or corrupted data)")
            raise ValueError("Cannot decrypt data: invalid encryption key or corrupted data")
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

    def encrypt_value(self, value: Any, value_type: str) -> dict:
        """
        Encrypt a value and return metadata for storage.

        Args:
            value: The value to encrypt (will be converted to string)
            value_type: The original type ('string', 'boolean', 'integer', 'json', 'float')

        Returns:
            Dictionary with encrypted_value and original_type
        """
        str_value = str(value)
        encrypted = self.encrypt(str_value)

        return {
            "encrypted_value": encrypted,
            "original_type": value_type,
        }

    def decrypt_value(self, encrypted_data: Any) -> Any:
        """
        Decrypt a value and restore its original type.

        Args:
            encrypted_data: Dictionary with encrypted_value and original_type

        Returns:
            Decrypted value in its original type
        """
        if not isinstance(encrypted_data, dict):
            # If it's already a plain string, return as-is
            return encrypted_data

        encrypted_value = encrypted_data.get("encrypted_value")
        original_type = encrypted_data.get("original_type", "string")

        if not encrypted_value:
            return encrypted_data

        decrypted = self.decrypt(encrypted_value)

        # Restore original type
        if original_type == "boolean":
            return decrypted.lower() in ("true", "1", "yes")
        if original_type == "integer":
            return int(decrypted)
        if original_type == "float":
            return float(decrypted)
        if original_type == "json":
            import json

            return json.loads(decrypted)
        return decrypted

    @staticmethod
    def generate_key() -> str:
        """Generate a new encryption key for initial setup."""
        return Fernet.generate_key().decode()


# Singleton instance
encryption_service = EncryptionService()
