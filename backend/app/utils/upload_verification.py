import hashlib
import hmac
import threading
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from app.config import config

TOKEN_ALGORITHM = "HS256"
TOKEN_PURPOSE = "cat-upload-verification"
TOKEN_TTL = timedelta(minutes=5)

_spent_tokens_lock = threading.Lock()
_spent_tokens: set[str] = set()


def _content_digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def create_upload_verification_token(content: bytes, user_id: str, detection: dict[str, Any]) -> str:
    now = datetime.now(UTC)
    payload = {
        "jti": uuid.uuid4().hex,
        "sub": user_id,
        "purpose": TOKEN_PURPOSE,
        "sha256": _content_digest(content),
        "cat_detection": {
            "has_cats": bool(detection.get("has_cats")),
            "cat_count": int(detection.get("cat_count", 0)),
            "confidence": float(detection.get("confidence", 0)),
            "suitable_for_cat_spot": bool(detection.get("suitable_for_cat_spot", False)),
            "cats_detected": detection.get("cats_detected", []),
        },
        "iat": now,
        "exp": now + TOKEN_TTL,
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm=TOKEN_ALGORITHM)


def verify_upload_verification_token(
    token: str, content: bytes, user_id: str, burn: bool = True
) -> dict[str, Any] | None:
    try:
        payload = jwt.decode(
            token,
            config.JWT_SECRET,
            algorithms=[TOKEN_ALGORITHM],
            leeway=10,
            options={"require": ["exp", "iat", "sub", "purpose", "sha256", "cat_detection"]},
        )
    except jwt.PyJWTError:
        return None

    if payload.get("purpose") != TOKEN_PURPOSE or payload.get("sub") != user_id:
        return None
    if not hmac.compare_digest(str(payload.get("sha256", "")), _content_digest(content)):
        return None

    jti = payload.get("jti")
    with _spent_tokens_lock:
        if jti and jti in _spent_tokens:
            return None

        detection = payload.get("cat_detection")
        if not isinstance(detection, dict) or detection.get("has_cats") is not True:
            return None

        if burn and jti:
            _spent_tokens.add(jti)

    return detection
