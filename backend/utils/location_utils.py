import secrets
from typing import Any


def protect_photo_location(photo: dict[str, Any]) -> dict[str, Any]:
    """
    Apply coordinate fuzzing to protect user privacy.
    Offsets latitude and longitude by a random small amount (~100m).
    """
    fuzzed = photo.copy()
    cryptogen = secrets.SystemRandom()
    if "latitude" in fuzzed and fuzzed["latitude"] is not None:
        # Roughly 100-200m fuzzing (0.001 deg is ~111m)
        offset_lat = (cryptogen.random() - 0.5) * 0.002
        fuzzed["latitude"] = float(fuzzed["latitude"]) + offset_lat

    if "longitude" in fuzzed and fuzzed["longitude"] is not None:
        offset_lng = (cryptogen.random() - 0.5) * 0.002
        fuzzed["longitude"] = float(fuzzed["longitude"]) + offset_lng

    return fuzzed


def protect_photo_locations(photos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Apply coordinate fuzzing to a list of photos."""
    return [protect_photo_location(photo) for photo in photos]
