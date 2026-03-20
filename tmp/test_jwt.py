import jwt
from datetime import datetime, timedelta, UTC
import json

secret = 'test'
expire = datetime.now(UTC) + timedelta(hours=1)
# Use isoformat as current implementation does
to_encode = {
    'sub': 'user123',
    'exp': expire.isoformat(),
    'iat': datetime.now(UTC).isoformat()
}

print(f"To encode: {to_encode}")

# Encode
token = jwt.encode(to_encode, secret, algorithm='HS256')
print(f"Token: {token}")

# Decode
try:
    payload = jwt.decode(token, secret, algorithms=['HS256'])
    print(f"Decoded successfully: {payload}")
except Exception as e:
    print(f"Decoding failed: {type(e).__name__}: {str(e)}")
