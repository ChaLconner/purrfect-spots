from typing import Any

from utils.security import protect_public_coordinates


def protect_photo_location(photo: dict[str, Any]) -> dict[str, Any]:
    """
    Apply coordinate fuzzing to protect user privacy.
    Uses deterministic fuzzing based on photo ID to ensure markers don't jump.
    """
    fuzzed = photo.copy()
    lat = fuzzed.get("latitude")
    lng = fuzzed.get("longitude")
    photo_id = str(fuzzed.get("id", ""))

    if lat is not None and lng is not None:
        p_lat, p_lng = protect_public_coordinates(float(lat), float(lng), seed=photo_id)
        fuzzed["latitude"] = p_lat
        fuzzed["longitude"] = p_lng

    return fuzzed


def protect_photo_locations(photos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Apply coordinate fuzzing to a list of photos."""
    return [protect_photo_location(photo) for photo in photos]
