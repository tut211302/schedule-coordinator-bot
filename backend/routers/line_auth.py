import json
import os
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend import crud, schemas
from backend.dependencies import get_db
from backend.services.line_service import get_line_profile
from backend.utils.security import verify_line_signature

router = APIRouter()


@router.post("/webhook")
async def line_webhook(
    request: Request,
    x_line_signature: str = Header(None),
    db: Session = None,
):
    """
    Handle LINE Messaging API Webhook.

    This endpoint receives events from LINE platform:
    - FollowEvent: User follows the bot → register or update user
    - MessageEvent: User sends a message → placeholder for future logic
    - UnfollowEvent: User unfollows the bot → deactivate user if needed
    """
    # Get raw body
    body = await request.body()
    body_str = body.decode("utf-8")

    # Verify signature
    if not verify_line_signature(body_str, x_line_signature):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature",
        )

    # Parse JSON
    try:
        events = json.loads(body_str).get("events", [])
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON",
        )

    # Process each event
    for event in events:
        event_type = event.get("type")

        if event_type == "follow":
            await handle_follow_event(event, db)
        elif event_type == "message":
            await handle_message_event(event, db)
        elif event_type == "unfollow":
            await handle_unfollow_event(event, db)

    return {"status": "ok"}


async def handle_follow_event(event: dict[str, Any], db: Session = None) -> None:
    """
    Handle FollowEvent: Register new user or update existing user profile.

    Args:
        event: LINE event object
        db: Database session (dependency injection)
    """
    from backend.database import SessionLocal

    if db is None:
        db = SessionLocal()
        should_close = True
    else:
        should_close = False

    try:
        user_id = event.get("source", {}).get("userId")
        if not user_id:
            print("No user_id in follow event")
            return

        # Fetch profile from LINE Messaging API
        profile = await get_line_profile(user_id)

        # Check if user already exists
        existing_user = crud.user.get_user_by_line_user_id(db, line_user_id=user_id)

        if existing_user:
            # Update existing user
            update_data = schemas.user.UserUpdate(
                display_name=profile.get("display_name") if profile else None,
                picture_url=profile.get("picture_url") if profile else None,
                status_message=profile.get("status_message") if profile else None,
            )
            crud.user.update_user(db=db, db_user=existing_user, user_update=update_data)
            print(f"Updated user {user_id}")
        else:
            # Create new user
            user_create = schemas.user.UserCreate(
                line_user_id=user_id,
                display_name=profile.get("display_name") if profile else None,
                picture_url=profile.get("picture_url") if profile else None,
                status_message=profile.get("status_message") if profile else None,
            )
            crud.user.create_user(db=db, user=user_create)
            print(f"Created new user {user_id}")

    except Exception as e:
        print(f"Error handling follow event: {e}")
    finally:
        if should_close:
            db.close()


async def handle_message_event(event: dict[str, Any], db: Session = None) -> None:
    """
    Handle MessageEvent: Placeholder for future message routing logic.

    Args:
        event: LINE event object
        db: Database session
    """
    user_id = event.get("source", {}).get("userId")
    message = event.get("message", {}).get("text")
    print(f"Message from {user_id}: {message}")
    # Future: Route to AI or poll logic here


async def handle_unfollow_event(event: dict[str, Any], db: Session = None) -> None:
    """
    Handle UnfollowEvent: User blocked or unblocked the bot.

    Args:
        event: LINE event object
        db: Database session
    """
    from backend.database import SessionLocal

    if db is None:
        db = SessionLocal()
        should_close = True
    else:
        should_close = False

    try:
        user_id = event.get("source", {}).get("userId")
        if not user_id:
            return

        # Optionally mark user as inactive or log the event
        print(f"User {user_id} unfollowed/blocked the bot")
        # Future: Deactivate user, clean up sessions, etc.

    except Exception as e:
        print(f"Error handling unfollow event: {e}")
    finally:
        if should_close:
            db.close()
