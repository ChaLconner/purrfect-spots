import io
import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image

from app.config import config
from app.main import app
from app.middleware.auth_middleware import get_current_user
from app.routes.admin.settings import encryption_service
from app.schemas.user import User
from app.services.queue_service import QueueMessage, QueueService
from app.services.quota_service import QuotaServiceUnavailable
from app.services.redis_service import redis_service
from app.utils.image_utils import optimize_image
from app.utils.upload_verification import (
    create_upload_verification_token,
    verify_upload_verification_token,
)


@pytest.fixture
def override_admin():
    app.dependency_overrides[get_current_user] = lambda: User(
        id="00000000-0000-4000-a000-000000000111",
        email="admin@example.com",
        name="Admin User",
        role="admin",
        permissions=["*"],
    )
    yield
    app.dependency_overrides.pop(get_current_user, None)


class AtomicRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.calls: list[dict[str, Any]] = []

    async def set(self, key: str, value: str, *, nx: bool = False, ex: int | None = None) -> bool:
        self.calls.append({"key": key, "value": value, "nx": nx, "ex": ex})
        if nx and key in self.values:
            return False
        self.values[key] = value
        return True


class DeadLetterRedis:
    def __init__(self) -> None:
        self.xadd_calls: list[dict[str, Any]] = []
        self.xtrim_calls: list[dict[str, Any]] = []
        self.expire_calls: list[dict[str, Any]] = []

    async def xadd(self, stream: str, fields: dict[str, str], **kwargs: Any) -> str:
        self.xadd_calls.append({"stream": stream, "fields": fields, "kwargs": kwargs})
        return "2-0"

    async def xtrim(self, stream: str, **kwargs: Any) -> int:
        self.xtrim_calls.append({"stream": stream, "kwargs": kwargs})
        return 0

    async def expire(self, stream: str, ttl: int) -> bool:
        self.expire_calls.append({"stream": stream, "ttl": ttl})
        return True

    async def xack(self, *_args: Any, **_kwargs: Any) -> int:
        return 1

    async def xdel(self, *_args: Any, **_kwargs: Any) -> int:
        return 1


@pytest.mark.asyncio
async def test_upload_verification_token_is_consumed_once_with_shared_atomic_state(monkeypatch) -> None:
    fake_redis = AtomicRedis()
    monkeypatch.setattr(redis_service, "client", fake_redis)

    detection = {
        "has_cats": True,
        "cat_count": 1,
        "confidence": 0.95,
        "suitable_for_cat_spot": True,
        "cats_detected": [],
    }
    content = b"canonical-image-bytes"
    token = create_upload_verification_token(content, "user-1", detection)

    first = await verify_upload_verification_token(token, content, "user-1")
    second = await verify_upload_verification_token(token, content, "user-1")

    assert first == detection
    assert second is None
    assert len(fake_redis.calls) == 2
    assert all(call["nx"] is True for call in fake_redis.calls)


@pytest.mark.asyncio
async def test_upload_verification_token_fails_closed_without_shared_store(monkeypatch) -> None:
    monkeypatch.setattr(redis_service, "client", None)

    detection = {
        "has_cats": True,
        "cat_count": 1,
        "confidence": 0.95,
        "suitable_for_cat_spot": True,
        "cats_detected": [],
    }
    content = b"canonical-image-bytes"
    token = create_upload_verification_token(content, "user-1", detection)

    assert await verify_upload_verification_token(token, content, "user-1") is None


@pytest.mark.asyncio
async def test_upload_quota_admission_uses_reservation_instead_of_rechecking_after_work() -> None:
    from app.routes.upload import _reserve_or_check_upload_quota

    quota_service = MagicMock()
    quota_service.reserve_upload_quota = AsyncMock(return_value="reservation-1")
    quota_service.check_quota = AsyncMock(side_effect=AssertionError("legacy quota check must not run"))

    reservation_id, uses_reservation = await _reserve_or_check_upload_quota(quota_service, "user-1", False)

    assert reservation_id == "reservation-1"
    assert uses_reservation is True
    quota_service.reserve_upload_quota.assert_awaited_once_with("user-1", False)


@pytest.mark.asyncio
async def test_upload_quota_admission_fails_closed_when_reservation_backend_is_unavailable() -> None:
    from fastapi import HTTPException

    from app.routes.upload import _reserve_or_check_upload_quota

    quota_service = MagicMock()
    quota_service.reserve_upload_quota = AsyncMock(side_effect=QuotaServiceUnavailable("unavailable"))

    with pytest.raises(HTTPException) as exc_info:
        await _reserve_or_check_upload_quota(quota_service, "user-1", False)

    assert exc_info.value.status_code == 503


def test_gif_optimization_reencodes_and_removes_comment_metadata() -> None:
    image = Image.new("RGB", (20, 20), color="white")
    image.putpixel((0, 0), (255, 0, 0))
    buffer = io.BytesIO()
    image.save(buffer, format="GIF", comment=b"PRIVATE-METADATA-TEST")
    original = buffer.getvalue()

    optimized, content_type = optimize_image(original, "image/gif")

    assert content_type == "image/gif"
    assert optimized != original
    with Image.open(io.BytesIO(optimized)) as sanitized:
        assert sanitized.info.get("comment") is None


def test_image_optimization_failure_is_rejected_instead_of_returning_raw_bytes() -> None:
    with pytest.raises(ValueError, match="Image optimization failed"):
        optimize_image(b"not an image", "image/jpeg")


def test_encrypted_settings_are_masked_before_the_response(client, override_admin, mock_supabase_admin) -> None:
    mock_supabase_admin.execute.return_value = MagicMock(
        data=[
            {
                "key": "smtp_password",
                "value": {"encrypted_value": "ciphertext", "original_type": "string"},
                "type": "string",
                "description": "SMTP password",
                "category": "infrastructure",
                "is_public": False,
                "is_encrypted": True,
                "requires_approval": False,
                "updated_at": "2026-03-28T00:00:00Z",
                "updated_by": None,
            }
        ]
    )

    with (
        patch(
            "app.routes.admin.settings.get_async_supabase_admin_client",
            new_callable=AsyncMock,
            return_value=mock_supabase_admin,
        ),
        patch.object(
            encryption_service, "decrypt_value", side_effect=AssertionError("plaintext must stay server-side")
        ),
    ):
        response = client.get("/api/v1/admin/settings?cache_bust=security-test")

    assert response.status_code == 200
    assert response.json()[0]["value"] is None
    assert response.json()[0]["is_encrypted"] is True


def test_encrypted_setting_replacement_cannot_be_empty(client, override_admin, mock_supabase_admin) -> None:
    mock_supabase_admin.execute.return_value = MagicMock(
        data={
            "value": {"encrypted_value": "ciphertext"},
            "requires_approval": False,
            "type": "string",
            "is_encrypted": True,
        }
    )

    with patch(
        "app.routes.admin.settings.get_async_supabase_admin_client",
        new_callable=AsyncMock,
        return_value=mock_supabase_admin,
    ):
        response = client.put("/api/v1/admin/settings/smtp_password", json={"value": "  "})

    assert response.status_code == 400
    assert "encrypted" in response.json()["detail"].lower()


def test_encrypted_setting_update_masks_response_value(client, override_admin, mock_supabase_admin) -> None:
    mock_supabase_admin.execute.side_effect = [
        MagicMock(
            data={
                "value": {"encrypted_value": "old-ciphertext"},
                "requires_approval": False,
                "type": "string",
                "is_encrypted": True,
            }
        ),
        MagicMock(
            data={
                "key": "smtp_password",
                "value": {"encrypted_value": "new-ciphertext"},
                "type": "string",
                "is_encrypted": True,
                "requires_approval": False,
                "updated_at": "2026-03-28T00:00:00Z",
                "updated_by": "00000000-0000-4000-a000-000000000111",
            }
        ),
        MagicMock(),
    ]

    with (
        patch(
            "app.routes.admin.settings.get_async_supabase_admin_client",
            new_callable=AsyncMock,
            return_value=mock_supabase_admin,
        ),
        patch.object(
            encryption_service,
            "encrypt_value",
            return_value={"encrypted_value": "new-ciphertext"},
        ),
    ):
        response = client.put("/api/v1/admin/settings/smtp_password", json={"value": "new-secret"})

    assert response.status_code == 200
    assert response.json()["value"] is None


def test_encrypted_setting_history_masks_database_values(client, override_admin, mock_supabase_admin) -> None:
    mock_supabase_admin.maybe_single.return_value = mock_supabase_admin
    mock_supabase_admin.execute.side_effect = [
        MagicMock(data={"is_encrypted": True}),
        MagicMock(
            data=[
                {
                    "id": "00000000-0000-4000-a000-000000000222",
                    "config_key": "smtp_password",
                    "old_value": {"encrypted_value": "old-ciphertext"},
                    "new_value": {"encrypted_value": "new-ciphertext"},
                    "changed_by": None,
                    "change_reason": "updated",
                    "created_at": "2026-03-28T00:00:00Z",
                    "user": None,
                }
            ]
        ),
    ]

    with patch(
        "app.routes.admin.settings.get_async_supabase_admin_client",
        new_callable=AsyncMock,
        return_value=mock_supabase_admin,
    ):
        response = client.get("/api/v1/admin/settings/history/smtp_password")

    assert response.status_code == 200
    assert response.json()[0]["old_value"] is None
    assert response.json()[0]["new_value"] is None


def test_setting_history_masks_values_when_config_metadata_is_missing(
    client, override_admin, mock_supabase_admin
) -> None:
    mock_supabase_admin.maybe_single.return_value = mock_supabase_admin
    mock_supabase_admin.execute.side_effect = [
        MagicMock(data=None),
        MagicMock(
            data=[
                {
                    "id": "00000000-0000-4000-a000-000000000222",
                    "config_key": "deleted_setting",
                    "old_value": "legacy-value",
                    "new_value": "replacement-value",
                    "changed_by": None,
                    "change_reason": "updated",
                    "created_at": "2026-03-28T00:00:00Z",
                    "user": None,
                }
            ]
        ),
    ]

    with patch(
        "app.routes.admin.settings.get_async_supabase_admin_client",
        new_callable=AsyncMock,
        return_value=mock_supabase_admin,
    ):
        response = client.get("/api/v1/admin/settings/history/deleted_setting")

    assert response.status_code == 200
    assert response.json()[0]["old_value"] is None
    assert response.json()[0]["new_value"] is None


@pytest.mark.asyncio
async def test_dead_letter_redacts_stripe_event_and_applies_retention_controls() -> None:
    service = QueueService()
    fake_redis = DeadLetterRedis()
    service.client = fake_redis  # type: ignore[assignment]
    message = QueueMessage(
        stream=service.STRIPE_STREAM,
        message_id="1-0",
        fields={
            "event_id": "evt_test_1",
            "event_type": "invoice.paid",
            "event": json.dumps({"data": {"object": {"customer_email": "person@example.com"}}}),
        },
    )

    await service.dead_letter(message, service.STRIPE_GROUP, "permanent failure")

    assert len(fake_redis.xadd_calls) == 1
    stored = json.loads(fake_redis.xadd_calls[0]["fields"]["message"])
    assert stored["fields"] == {"event_id": "evt_test_1", "event_type": "invoice.paid"}
    assert "event" not in stored["fields"]
    assert fake_redis.xadd_calls[0]["kwargs"]["maxlen"] == config.QUEUE_DEAD_LETTER_MAXLEN
    assert fake_redis.xtrim_calls[0]["kwargs"]["minid"]
    assert fake_redis.expire_calls[0]["ttl"] == config.QUEUE_DEAD_LETTER_TTL_SECONDS
