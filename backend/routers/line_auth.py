import json
import os
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from crud import user as crud_user
from schemas import user as schemas_user
from database import SessionLocal
from services.line_service import get_line_profile
from utils.security import verify_line_signature
from line.handlers import _route_message, _strip_mention
from line.reply import reply_text
from line.config import BOT_MENTION

router = APIRouter()
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")


@router.post("/webhook")
async def line_webhook(
    request: Request,
    x_line_signature: str = Header(None),
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

    # Debug logging
    print(f"[LINE Webhook] Received request")
    print(f"[LINE Webhook] Signature: {x_line_signature}")
    print(f"[LINE Webhook] Body length: {len(body_str)}")

    # Verify signature (skip in development for testing)
    if not verify_line_signature(body_str, x_line_signature): #ENVIRONMENT == "production" and 
        print(f"[LINE Webhook] Signature verification failed")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature",
        )
    
    #if ENVIRONMENT == "development":
    #    print(f"[LINE Webhook] Signature verification SKIPPED (development mode)")

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
            await handle_follow_event(event)
        elif event_type == "message":
            await handle_message_event(event)
        elif event_type == "unfollow":
            await handle_unfollow_event(event)

    return {"status": "ok"}


async def handle_follow_event(event: dict[str, Any]) -> None:
    """
    Handle FollowEvent: Register new user or update existing user profile.

    Args:
        event: LINE event object
    """
    db = SessionLocal()
    try:
        user_id = event.get("source", {}).get("userId")
        if not user_id:
            print("No user_id in follow event")
            return

        # Fetch profile from LINE Messaging API
        profile = await get_line_profile(user_id)

        # Create or update user
        user_data = schemas_user.UserCreate(
            line_user_id=user_id,
            display_name=profile.get("display_name") if profile else None,
            picture_url=profile.get("picture_url") if profile else None,
            status_message=profile.get("status_message") if profile else None,
        )

        crud_user.create_or_update_user_by_line_id(db, line_user_id=user_id, user_data=user_data)
        print(f"Processed follow event for user {user_id}")

    except Exception as e:
        print(f"Error handling follow event: {e}")
    finally:
        db.close()


async def handle_message_event(event: dict[str, Any]) -> None:
    """
    Handle MessageEvent: Auto-register user if not exists, then route message.

    Args:
        event: LINE event object
    """
    db = SessionLocal()
    try:
        user_id = event.get("source", {}).get("userId")
        raw_message = event.get("message", {}).get("text")

        if not user_id or not raw_message:
            return

        # Auto-register user if not exists
        existing_user = crud_user.get_user_by_line_user_id(db, line_user_id=user_id)
        if not existing_user:
            # Fetch profile and register
            profile = await get_line_profile(user_id)
            user_data = schemas_user.UserCreate(
                line_user_id=user_id,
                display_name=profile.get("display_name") if profile else None,
                picture_url=profile.get("picture_url") if profile else None,
                status_message=profile.get("status_message") if profile else None,
            )
            crud_user.create_user(db=db, user=user_data)
            print(f"Auto-registered user {user_id} from message event")

        # Process message with handlers
        message = _strip_mention(event, raw_message, BOT_MENTION)
        print(f"[LINE] Processing message: {message}")
        
        reply_token = event.get("replyToken")
        response = await _route_message(event, message)
        
        if reply_token and response:
            print(f"[LINE] Sending reply: {response}")
            await reply_text(reply_token, response)
        else:
            print(f"[LINE] No response to send (reply_token={reply_token}, response={response})")

    except Exception as e:
        print(f"Error handling message event: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


async def handle_unfollow_event(event: dict[str, Any]) -> None:
    """
    Handle UnfollowEvent: User blocked or unblocked the bot.

    Args:
        event: LINE event object
    """
    try:
        user_id = event.get("source", {}).get("userId")
        if not user_id:
            return

        # Log event (could mark as inactive, cleanup sessions, etc.)
        print(f"User {user_id} unfollowed/blocked the bot")

    except Exception as e:
        print(f"Error handling unfollow event: {e}")
