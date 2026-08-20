"""Shared security policy constants."""

# New and changed passwords must be long enough to resist trivial guessing.
# Character-class rules are intentionally not enforced; passphrases are valid.
MIN_PASSWORD_LENGTH: int = 8
