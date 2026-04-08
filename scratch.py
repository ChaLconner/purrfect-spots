import asyncio
from unittest.mock import MagicMock
record = {"id": 1, "otp_hash": "different_hash", "attempts": 0, "max_attempts": 5, "expires_at": "2099-01-01T00:00:00Z"}
mock_res = MagicMock()
mock_res.fetchone.return_value = MagicMock(_mapping=record)
row = mock_res.fetchone()
print(f"row: {row}")
print(f"row as bool: {bool(row)}")
try:
    d = dict(row._mapping)
    print(f"dict(row._mapping): {d}")
    print(f"dict(row._mapping) as bool: {bool(d)}")
except Exception as e:
    print(f"Exception: {e}")
