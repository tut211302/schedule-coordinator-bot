import os
import secrets
from urllib.parse import urlencode, urlparse, urlunparse, parse_qsl

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from crud import user as crud_user
from schemas import user as schemas_user
from dependencies import get_db
from services.google_service import get_google_client

router = APIRouter()

# Simple in-memory state store for CSRF protection
# In production, use Redis or database
_state_store: dict[str, dict] = {}


def _normalize_redirect_url(raw_url: str | None) -> str:
    frontend_base = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")
    if not raw_url:
        return frontend_base
    if raw_url.startswith("/"):
        return frontend_base.rstrip("/") + raw_url
    if raw_url.startswith(frontend_base):
        return raw_url
    return frontend_base


def _append_query(url: str, key: str, value: str) -> str:
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query))
    query[key] = value
    new_query = urlencode(query)
    return urlunparse(parsed._replace(query=new_query))


@router.get("/login/{line_user_id}")
async def google_login(line_user_id: str, redirect_url: str | None = None, db: Session = Depends(get_db)):
    """
    Start Google OAuth flow.

    Args:
        line_user_id: LINE user ID who wants to connect Google Calendar

    Returns:
        Redirect to Google authorization page
    """
    # Verify user exists
    db_user = crud_user.get_user_by_line_user_id(db, line_user_id=line_user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Generate state token for CSRF protection
    state = secrets.token_urlsafe(32)
    _state_store[state] = {
        "line_user_id": line_user_id,
        "redirect_url": _normalize_redirect_url(redirect_url),
    }

    # Get Google OAuth client
    google_client = get_google_client()
    auth_url = google_client.get_auth_url(state)

    # Return auth_url as JSON so frontend can redirect manually
    return {"auth_url": auth_url}


@router.get("/callback")
async def google_callback(
    request: Request,
    code: str,
    state: str,
    db: Session = Depends(get_db),
):
    """
    Handle Google OAuth callback.

    Args:
        code: Authorization code from Google
        state: CSRF state parameter
        request: HTTP request (for error cases)
        db: Database session

    Returns:
        JSON response with success message and redirect URL
    """
    # Validate state parameter (CSRF protection)
    if state not in _state_store:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state parameter")

    state_payload = _state_store.pop(state)
    line_user_id = state_payload.get("line_user_id")
    redirect_url = state_payload.get("redirect_url") or os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")

    # Get user
    db_user = crud_user.get_user_by_line_user_id(db, line_user_id=line_user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    try:
        # Exchange code for token
        google_client = get_google_client()
        token_response = await google_client.exchange_code_for_token(code)

        access_token = token_response.get("access_token")
        refresh_token = token_response.get("refresh_token")
        expires_in = token_response.get("expires_in", 3600)
        token_type = token_response.get("token_type", "Bearer")

        # Calculate token expiry
        token_expiry = google_client.calculate_expiry_time(expires_in)

        # Update user with Google auth data
        user_info = await google_client.fetch_user_info(access_token)
        google_auth_data = schemas_user.UserGoogleAuth(
            access_token=access_token,
            refresh_token=refresh_token,
            token_expiry=token_expiry,
            calendar_connected=True,
            google_id=user_info.get("id"),
            email=user_info.get("email"),
        )
        crud_user.update_user_google_auth(db=db, db_user=db_user, google_auth_data=google_auth_data)

        # Redirect to frontend with success message
        frontend_url = redirect_url
        return RedirectResponse(
            url=_append_query(frontend_url, "google_auth", "success"),
            status_code=status.HTTP_302_FOUND
        )

    except Exception as e:
        print(f"Error in Google callback: {e}")
        # Redirect to frontend with error message
        frontend_url = redirect_url
        return RedirectResponse(
            url=_append_query(frontend_url, "google_auth", "error"),
            status_code=status.HTTP_302_FOUND
        )


@router.post("/refresh/{line_user_id}")
async def refresh_google_token(line_user_id: str, db: Session = Depends(get_db)):
    """
    Refresh Google access token if it has expired.

    Args:
        line_user_id: LINE user ID
        db: Database session

    Returns:
        JSON response with new token expiry
    """
    # Get user
    db_user = crud_user.get_user_by_line_user_id(db, line_user_id=line_user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not db_user.google_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No refresh token available",
        )

    try:
        google_client = get_google_client()
        token_response = await google_client.refresh_access_token(db_user.google_refresh_token)

        access_token = token_response.get("access_token")
        expires_in = token_response.get("expires_in", 3600)
        token_type = token_response.get("token_type", "Bearer")
        new_refresh_token = token_response.get("refresh_token", db_user.google_refresh_token)

        # Calculate new expiry
        token_expiry = google_client.calculate_expiry_time(expires_in)

        # Update user
        google_auth_data = schemas_user.UserGoogleAuth(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_expiry=token_expiry,
            calendar_connected=True,
        )
        crud_user.update_user_google_auth(db=db, db_user=db_user, google_auth_data=google_auth_data)

        return {
            "success": True,
            "message": "Token refreshed successfully",
            "token_expiry": token_expiry.isoformat(),
        }

    except Exception as e:
        print(f"Error refreshing Google token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh token: {str(e)}",
        )


@router.post("/disconnect/{line_user_id}")
async def disconnect_google(line_user_id: str, db: Session = Depends(get_db)):
    """
    Disconnect Google Calendar from user account.

    Args:
        line_user_id: LINE user ID
        db: Database session

    Returns:
        JSON response
    """
    db_user = crud_user.get_user_by_line_user_id(db, line_user_id=line_user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    try:
        # Clear Google auth data
        update_data = schemas_user.UserUpdate(
            google_connected=False,
        )
        # Manually clear tokens
        db_user.google_access_token = None
        db_user.google_refresh_token = None
        db_user.google_token_expiry = None
        db_user.google_token_type = None
        db_user.google_connected = False
        db.add(db_user)
        db.commit()

        return {"success": True, "message": "Google Calendar disconnected"}

    except Exception as e:
        print(f"Error disconnecting Google: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect: {str(e)}",
        )
