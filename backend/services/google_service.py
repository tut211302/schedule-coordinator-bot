"""
Google OAuth 2.0 service functions for Calendar integration.
"""

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import id_token
import google.auth.transport.requests
from typing import Optional, Tuple, Dict, Any
from datetime import datetime
from config import settings


# OAuth 2.0 scopes for Google Calendar access
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid"
]


def get_google_auth_flow(state: Optional[str] = None) -> Flow:
    """
    Create a Google OAuth 2.0 flow instance.
    
    Args:
        state: Optional state parameter (e.g., line_user_id) to pass through OAuth flow
        
    Returns:
        Configured Flow instance
    """
    client_config = {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
    )
    
    if state:
        flow.state = state
    
    return flow


def get_auth_url(line_user_id: str) -> str:
    """
    Generate Google OAuth authorization URL.
    
    Args:
        line_user_id: LINE user ID to bind with Google account
        
    Returns:
        Authorization URL to redirect user to
    """
    flow = get_google_auth_flow()
    
    auth_url, _ = flow.authorization_url(
        prompt="consent",  # Always show consent screen
        access_type="offline",  # Required to get refresh token
        include_granted_scopes="true",
        state=line_user_id  # ← ここで明示的にstateを渡す
    )
    
    return auth_url


def exchange_code_for_tokens(code: str, state: str) -> Dict[str, Any]:
    """
    Exchange authorization code for access and refresh tokens.
    
    Args:
        code: Authorization code from Google callback
        state: State parameter (line_user_id) passed through OAuth flow
        
    Returns:
        Dict containing:
            - google_id: Google account ID
            - email: Google email address
            - access_token: OAuth access token
            - refresh_token: OAuth refresh token (may be None)
            - expiry: Token expiration datetime
            
    Raises:
        Exception: If token exchange or verification fails
    """
    flow = get_google_auth_flow(state=state)
    
    # Exchange code for tokens
    flow.fetch_token(code=code)
    credentials = flow.credentials
    
    # Verify ID token to get user info
    id_info = id_token.verify_oauth2_token(
        credentials.id_token,
        google.auth.transport.requests.Request(),
        settings.GOOGLE_CLIENT_ID
    )
    
    return {
        "google_id": id_info.get("sub"),
        "email": id_info.get("email"),
        "access_token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "expiry": credentials.expiry
    }


def refresh_access_token(refresh_token: str) -> Tuple[str, Optional[datetime]]:
    """
    Refresh an expired access token using the refresh token.
    
    Args:
        refresh_token: OAuth refresh token
        
    Returns:
        Tuple of (new_access_token, new_expiry)
        
    Raises:
        Exception: If refresh fails
    """
    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
    )
    
    # Refresh the token
    request = GoogleAuthRequest()
    credentials.refresh(request)
    
    return credentials.token, credentials.expiry


def get_valid_credentials(
    access_token: str,
    refresh_token: Optional[str],
    token_expiry: Optional[datetime]
) -> Optional[Credentials]:
    """
    Get valid credentials, refreshing if necessary.
    
    Args:
        access_token: Current access token
        refresh_token: Refresh token for getting new access token
        token_expiry: Expiration time of current access token
        
    Returns:
        Valid Credentials object or None if unable to get valid credentials
    """
    credentials = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        expiry=token_expiry
    )
    
    # Check if token is expired or about to expire
    if credentials.expired and credentials.refresh_token:
        try:
            request = GoogleAuthRequest()
            credentials.refresh(request)
        except Exception as e:
            print(f"[Google] Failed to refresh token: {e}")
            return None
    
    return credentials if credentials.valid else None
