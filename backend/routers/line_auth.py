"""
LINE Webhook authentication router (F011).
Handles LINE Messaging API webhooks and user registration.
"""

import json
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from dependencies import get_db
from utils.security import validate_line_signature
from services.line_service import get_line_profile, reply_text
from crud import user as user_crud
from schemas.user import UserCreate
from config import settings

router = APIRouter()


async def process_line_event(event: dict, db: Session) -> None:
    """
    Process a single LINE webhook event.
    
    - Extracts user ID from event source
    - Creates new user if not exists
    - Fetches and stores LINE profile information
    
    Args:
        event: LINE webhook event object
        db: Database session
    """
    source = event.get("source", {})
    user_id = source.get("userId")
    
    if not user_id:
        print(f"[LINE] Event without userId: {event.get('type')}")
        return
    
    # Check if user exists
    user = user_crud.get_user_by_line_id(db, user_id)
    
    if not user:
        # Fetch LINE profile for new user
        profile = await get_line_profile(user_id)
        
        display_name = None
        picture_url = None
        
        if profile:
            display_name = profile.get("displayName")
            picture_url = profile.get("pictureUrl")
            print(f"[LINE] New user profile: {display_name}")
        
        # Create new user
        user = user_crud.create_user(db, UserCreate(
            line_user_id=user_id,
            line_display_name=display_name,
            line_picture_url=picture_url
        ))
        print(f"[LINE] Created new user: id={user.id}, line_user_id={user_id}")
    
    # Handle message events
    event_type = event.get("type")
    
    if event_type == "message":
        message = event.get("message", {})
        message_type = message.get("type")
        
        if message_type == "text":
            text = message.get("text", "")
            reply_token = event.get("replyToken")
            
            # Check if should handle (mention in group or direct message)
            should_handle = should_handle_message(event)
            
            if should_handle and reply_token:
                print(f"[LINE] Message from {user.line_display_name}: {text}")
                # Reply with acknowledgment (AI router will be implemented later)
                await reply_text(
                    reply_token,
                    f"メッセージを受け付けました。\n(登録済み: {user.line_display_name})"
                )
    
    elif event_type == "follow":
        # User added bot as friend
        print(f"[LINE] New follower: {user.line_display_name}")
        reply_token = event.get("replyToken")
        if reply_token:
            await reply_text(
                reply_token,
                f"友だち追加ありがとうございます！\n"
                f"Googleカレンダーと連携すると、スケジュール調整ができるようになります。"
            )
    
    elif event_type == "unfollow":
        # User blocked/unfollowed bot
        print(f"[LINE] User unfollowed: {user_id}")


def should_handle_message(event: dict) -> bool:
    """
    Determine if message should be handled.
    
    - Always handle in 1:1 chat
    - In group/room, only handle if bot is mentioned
    
    Args:
        event: LINE webhook event
        
    Returns:
        True if message should be handled
    """
    source_type = event.get("source", {}).get("type")
    
    # Always handle 1:1 chat
    if source_type == "user":
        return True
    
    # For group/room, check for mention
    message = event.get("message", {})
    
    # Check mention object (LINE API v2.19+)
    mention = message.get("mention")
    if mention and mention.get("mentionees"):
        return True
    
    # Check for text-based mention (fallback)
    text = message.get("text", "")
    bot_mention = settings.BOT_MENTION
    if bot_mention and bot_mention in text:
        return True
    
    return False


@router.post("/webhook")
async def line_webhook(
    body: str = Depends(validate_line_signature),
    db: Session = Depends(get_db)
):
    """
    LINE Messaging API webhook endpoint.
    
    Receives events from LINE and processes them:
    - Validates signature (in dependency)
    - Parses events
    - Registers/updates users
    - Handles messages
    
    Args:
        body: Validated request body
        db: Database session
        
    Returns:
        Success status
    """
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    events = payload.get("events", [])
    
    for event in events:
        await process_line_event(event, db)
    
    return {"status": "ok"}
