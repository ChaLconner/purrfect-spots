import os
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet

from app.services.encryption_service import EncryptionService


def test_json_values_round_trip_without_python_repr_corruption() -> None:
    service = EncryptionService()
    value = {"nested": [1, True, "แมว"], "name": "spot"}
    test_fernet_key = Fernet.generate_key().decode()

    with patch.dict(os.environ, {"ENVIRONMENT": "testing", "ENCRYPTION_KEY": test_fernet_key}):
        encrypted = service.encrypt_value(value, "json")
        restored = service.decrypt_value(encrypted)

    assert restored == value


def test_missing_key_fails_in_production() -> None:
    service = EncryptionService()

    with (
        patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=True),
        pytest.raises(RuntimeError, match="ENCRYPTION_KEY must be configured"),
    ):
        service.encrypt("secret")
