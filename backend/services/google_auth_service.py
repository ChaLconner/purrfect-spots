"""
Google Authentication Service

Handles Google OAuth 2.0 flow:
- Verifying ID tokens
- Exchanging auth codes for tokens via PKCE
"""

import uuid
from typing import Optional

import httpx
from google.auth.transport import requests
from google.oauth2 import id_token

from config import config
from logger import logger
from schemas.auth import LoginResponse
from user_models.user import UserResponse


class GoogleAuthService:
    def __init__(self):
        self.google_client_id = config.GOOGLE_CLIENT_ID
        self.google_client_secret = config.GOOGLE_CLIENT_SECRET

        if not self.google_client_id:
            logger.warning("[OAuth] GOOGLE_CLIENT_ID is not set!")
        if not self.google_client_secret:
            logger.warning("[OAuth] GOOGLE_CLIENT_SECRET is not set!")

    def verify_google_token(self, token: str) -> dict:
        """Verify Google OAuth token and return user info"""
        try:
            idinfo = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                self.google_client_id,
                clock_skew_in_seconds=10,
            )

            if idinfo["iss"] not in [
                "accounts.google.com",
                "https://accounts.google.com",
            ]:
                raise ValueError("Wrong issuer.")

            return {
                "google_id": idinfo["sub"],
                "email": idinfo["email"],
                "name": idinfo["name"],
                "picture": idinfo.get("picture", ""),
            }
        except ValueError as e:
            raise ValueError(f"Invalid token: {e!s}")

    async def exchange_google_code(self, code: str, code_verifier: str, redirect_uri: str) -> dict:
        """
        Exchange Google authorization code for access token using PKCE flow.
        Returns the raw token data and user info from Google.
        Does NOT handle user creation or JWT generation - that's for the caller.
        """
        try:
            if not code or not code_verifier or not redirect_uri:
                raise ValueError("Missing required OAuth parameters")

            token_url = "https://oauth2.googleapis.com/token"  # nosec B105
            data = {
                "client_id": self.google_client_id,
                "client_secret": self.google_client_secret,
                "code": code,
                "code_verifier": code_verifier,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            }
            headers = {"Content-Type": "application/x-www-form-urlencoded"}

            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, data=data, headers=headers)

                if response.status_code != 200:
                    logger.warning("[OAuth] External exchange unsuccessful")
                    raise ValueError("Token exchange failed")

                token_data = response.json()
                access_token = token_data.get("access_token")
                id_token_str = token_data.get("id_token")

                if not access_token or not id_token_str:
                    logger.error("[OAuth] Missing tokens in Google response")
                    raise ValueError("Missing tokens in response")

                # Verify ID token
                idinfo = id_token.verify_oauth2_token(
                    id_token_str,
                    requests.Request(),
                    self.google_client_id,
                    clock_skew_in_seconds=10,
                )

                return {
                    "access_token": access_token,
                    "id_token": id_token_str,
                    "user_info": {
                        "google_id": idinfo["sub"],
                        "email": idinfo["email"],
                        "name": idinfo["name"],
                        "picture": idinfo.get("picture", ""),
                    },
                }

        except ValueError as e:
            raise e
        except Exception as e:
            logger.error("[OAuth] Exchange execution error: %s", e)
            raise ValueError("Code exchange failed")


# Singleton
google_auth_service = GoogleAuthService()
