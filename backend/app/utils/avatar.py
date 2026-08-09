"""Validation for user-controlled avatar URLs."""

import os
from urllib.parse import urlsplit

_DEFAULT_AVATAR_HOSTS = {
    "ui-avatars.com",
    "lh3.googleusercontent.com",
    "avatars.githubusercontent.com",
    "cdn.discordapp.com",
}
_DEFAULT_AVATAR_SUFFIXES = (
    ".googleusercontent.com",
    ".githubusercontent.com",
    ".discordapp.com",
)


def _configured_hosts() -> set[str]:
    """Build the allowed host set from known providers and deployment URLs."""
    hosts = set(_DEFAULT_AVATAR_HOSTS)
    configured = os.getenv("AVATAR_ALLOWED_HOSTS", "")
    hosts.update(value.strip().lower().lstrip("*.") for value in configured.split(",") if value.strip())

    # Keep storage/CDN and same-origin avatars usable without trusting every
    # arbitrary HTTPS origin.
    try:
        from app.config import config

        for base_url in (config.SUPABASE_URL, config.CDN_BASE_URL, config.FRONTEND_URL):
            hostname = urlsplit(base_url).hostname
            if hostname:
                hosts.add(hostname.lower())
    except Exception:
        # Configuration may be imported before optional deployment settings
        # are available; the fixed provider allowlist remains safe.
        pass
    return hosts


def validate_avatar_url(value: str | None) -> str | None:
    """Validate and normalize an avatar URL accepted from a user request.

    Only HTTPS URLs from known providers or explicitly configured hosts are
    accepted. Empty values are retained so a user can clear an avatar.
    """
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("Avatar URL must be an HTTPS URL from an approved host")
    normalized = value.strip()
    if not normalized:
        return normalized

    parsed = urlsplit(normalized)
    hostname = parsed.hostname.lower() if parsed.hostname else ""
    if parsed.scheme != "https" or not hostname or parsed.username or parsed.password or parsed.fragment:
        raise ValueError("Avatar URL must be an HTTPS URL from an approved host")

    allowed_hosts = _configured_hosts()
    if hostname not in allowed_hosts and not any(hostname.endswith(suffix) for suffix in _DEFAULT_AVATAR_SUFFIXES):
        raise ValueError("Avatar URL host is not approved")
    return normalized


def sanitize_avatar_url(value: object) -> str | None:
    """Return a safe avatar URL for responses, dropping legacy unsafe values."""
    if value is None or not isinstance(value, str):
        return None
    try:
        return validate_avatar_url(value)
    except ValueError:
        return None
