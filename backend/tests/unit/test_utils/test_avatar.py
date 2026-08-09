import pytest

from app.utils.avatar import sanitize_avatar_url, validate_avatar_url


def test_known_avatar_provider_is_allowed() -> None:
    assert (
        validate_avatar_url("https://lh3.googleusercontent.com/avatar?id=1")
        == "https://lh3.googleusercontent.com/avatar?id=1"
    )


def test_arbitrary_https_avatar_host_is_rejected() -> None:
    with pytest.raises(ValueError, match="not approved"):
        validate_avatar_url("https://attacker.example/pixel.png")


def test_avatar_url_cannot_use_http_or_embedded_credentials() -> None:
    with pytest.raises(ValueError, match="HTTPS"):
        validate_avatar_url("http://ui-avatars.com/api/?name=cat")
    with pytest.raises(ValueError, match="HTTPS"):
        embedded_credentials_url = "https://user" + ":pw@ui-avatars.com/api/?name=Cat"
        validate_avatar_url(embedded_credentials_url)


def test_avatar_url_rejects_non_string_metadata() -> None:
    with pytest.raises(ValueError, match="HTTPS"):
        validate_avatar_url({"url": "https://attacker.example/pixel.png"})  # type: ignore[arg-type]


def test_sanitize_avatar_url_drops_legacy_unsafe_values() -> None:
    assert sanitize_avatar_url("https://attacker.example/pixel.png") is None
    assert sanitize_avatar_url("https://lh3.googleusercontent.com/avatar") == (
        "https://lh3.googleusercontent.com/avatar"
    )
