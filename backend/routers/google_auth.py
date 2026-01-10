"""
Google OAuth 2.0 authentication router (F012).
Handles Google Calendar integration authentication flow.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from dependencies import get_db
from schemas.user import GoogleAuthCallback, UserCreate
from crud import user as user_crud
from services.google_service import get_auth_url, exchange_code_for_tokens, refresh_access_token
from config import settings

router = APIRouter()


@router.get("/login")
async def google_login(lineUserId: str):
    """
    Start Google OAuth 2.0 authentication flow.
    
    Generates an authorization URL that the client should redirect to.
    The lineUserId is passed as state parameter to bind Google account
    with LINE user after callback.
    
    Args:
        lineUserId: LINE user ID to bind with Google account
        
    Returns:
        Authorization URL
        
    Raises:
        500: If Google credentials are not configured
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth credentials not configured"
        )
    
    auth_url = get_auth_url(lineUserId)
    
    return {"authUrl": auth_url}


@router.post("/callback")
async def google_callback(
    auth_data: GoogleAuthCallback,
    db: Session = Depends(get_db)
):
    """
    Handle Google OAuth 2.0 callback.
    
    Exchanges authorization code for tokens and stores them
    in the database linked to the LINE user.
    
    Args:
        auth_data: Contains authorization code and state (line_user_id)
        db: Database session
        
    Returns:
        Success status with email
        
    Raises:
        400: If state is missing or authentication fails
        500: If Google credentials are not configured
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth credentials not configured"
        )
    
    line_user_id = auth_data.state
    if not line_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing state parameter (lineUserId)"
        )
    
    try:
        # Exchange code for tokens
        token_data = exchange_code_for_tokens(auth_data.code, auth_data.state)
        
        # Get or create user
        user = user_crud.get_user_by_line_id(db, line_user_id)
        
        if not user:
            # Create user if not exists (edge case: webhook not received yet)
            user = user_crud.create_user(db, UserCreate(
                line_user_id=line_user_id,
                line_display_name="From Google Auth"
            ))
            print(f"[Google Auth] Created user from callback: {line_user_id}")
        
        # Update user with Google tokens
        user_crud.update_user_google_token(
            db=db,
            user=user,
            google_id=token_data["google_id"],
            email=token_data["email"],
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            token_expiry=token_data["expiry"]
        )
        
        print(f"[Google Auth] Linked Google account: {token_data['email']} -> {line_user_id}")
        
        return {
            "success": True,
            "email": token_data["email"],
            "message": "Google Calendar connected successfully"
        }
        
    except Exception as e:
        print(f"[Google Auth] Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication failed: {str(e)}"
        )


@router.post("/refresh")
async def refresh_token(lineUserId: str, db: Session = Depends(get_db)):
    """
    Refresh Google access token using stored refresh token.
    
    Args:
        lineUserId: LINE user ID
        db: Database session
        
    Returns:
        Success status
        
    Raises:
        404: If user not found
        400: If refresh token not available or refresh fails
    """
    user = user_crud.get_user_by_line_id(db, lineUserId)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No refresh token available. Please re-authenticate."
        )
    
    try:
        new_access_token, new_expiry = refresh_access_token(user.refresh_token)
        
        # Update stored access token
        user.access_token = new_access_token
        user.token_expiry = new_expiry
        db.commit()
        
        return {
            "success": True,
            "message": "Token refreshed successfully"
        }
        
    except Exception as e:
        print(f"[Google Auth] Refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Token refresh failed: {str(e)}"
        )


@router.post("/disconnect")
async def disconnect_google(lineUserId: str, db: Session = Depends(get_db)):
    """
    Disconnect Google Calendar integration.
    
    Removes stored tokens and marks calendar as disconnected.
    
    Args:
        lineUserId: LINE user ID
        db: Database session
        
    Returns:
        Success status
        
    Raises:
        404: If user not found
    """
    user = user_crud.get_user_by_line_id(db, lineUserId)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Clear Google-related fields
    user.access_token = None
    user.refresh_token = None
    user.token_expiry = None
    user.calendar_connected = False
    db.commit()
    
    print(f"[Google Auth] Disconnected: {lineUserId}")
    
    return {
        "success": True,
        "message": "Google Calendar disconnected"
    }
