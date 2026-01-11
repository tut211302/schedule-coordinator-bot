import os
from datetime import datetime, timedelta
from typing import Any, Optional

import aiohttp


class GoogleOAuthClient:
    """Client for Google OAuth 2.0 operations"""

    def __init__(self):
        self.client_id = os.getenv("GOOGLE_CLIENT_ID", "")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
        self.redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "")

        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            raise ValueError(
                "Missing Google OAuth environment variables: "
                "GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI"
            )

        self.auth_endpoint = "https://oauth2.googleapis.com/token"
        self.userinfo_endpoint = "https://www.googleapis.com/oauth2/v2/userinfo"
        self.auth_url_base = "https://accounts.google.com/o/oauth2/v2/auth"

    def get_auth_url(self, state: str) -> str:
        """
        Generate Google OAuth authorization URL.

        Args:
            state: CSRF protection state parameter

        Returns:
            Authorization URL for redirect
        """
        # Scopes for calendar access
        scopes = "openid profile email https://www.googleapis.com/auth/calendar.readonly"

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": scopes,
            "state": state,
            "access_type": "offline",  # Request refresh token
            "prompt": "consent",  # Force consent screen to ensure refresh token
        }

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.auth_url_base}?{query_string}"

    async def exchange_code_for_token(self, code: str) -> dict[str, Any]:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from OAuth callback

        Returns:
            Token response with access_token, refresh_token, expires_in

        Raises:
            Exception: If token exchange fails
        """
        data = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.auth_endpoint, data=data) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"Token exchange failed: {resp.status} {error_text}")

                    token_response = await resp.json()
                    return token_response
        except Exception as e:
            raise Exception(f"Token exchange error: {str(e)}")

    async def refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token from previous auth

        Returns:
            New token response with access_token, expires_in

        Raises:
            Exception: If refresh fails
        """
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.auth_endpoint, data=data) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"Token refresh failed: {resp.status} {error_text}")

                    return await resp.json()
        except Exception as e:
            raise Exception(f"Token refresh error: {str(e)}")

    @staticmethod
    def calculate_expiry_time(expires_in: int) -> datetime:
        """
        Calculate token expiry datetime.

        Args:
            expires_in: Token lifetime in seconds

        Returns:
            Expiry datetime
        """
        return datetime.utcnow() + timedelta(seconds=expires_in)


# Global instance
_google_client: Optional[GoogleOAuthClient] = None


def get_google_client() -> GoogleOAuthClient:
    """Get or create Google OAuth client instance"""
    global _google_client
    if _google_client is None:
        _google_client = GoogleOAuthClient()
    return _google_client
