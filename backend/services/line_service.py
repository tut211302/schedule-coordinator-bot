"""
LINE Messaging API service functions.
"""

import aiohttp
from typing import Optional, Dict, Any, List
from config import settings


LINE_API_BASE = "https://api.line.me/v2/bot"


async def get_line_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get LINE user profile information.
    
    Docs: https://developers.line.biz/en/reference/messaging-api/#get-profile
    
    Args:
        user_id: LINE user ID
        
    Returns:
        Dict with displayName, userId, pictureUrl, statusMessage
        or None if request fails
    """
    if not settings.LINE_CHANNEL_ACCESS_TOKEN:
        print("[LINE] Channel access token not configured")
        return None
    
    headers = {
        "Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                f"{LINE_API_BASE}/profile/{user_id}",
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    print(f"[LINE] Failed to get profile: {response.status} - {error_text}")
                    return None
        except Exception as e:
            print(f"[LINE] Error getting profile: {e}")
            return None


async def reply_message(reply_token: str, messages: List[Dict[str, Any]]) -> bool:
    """
    Reply to a LINE message.
    
    Docs: https://developers.line.biz/en/reference/messaging-api/#send-reply-message
    
    Args:
        reply_token: Reply token from webhook event
        messages: List of message objects to send
        
    Returns:
        True if successful, False otherwise
    """
    if not settings.LINE_CHANNEL_ACCESS_TOKEN:
        print("[LINE] Channel access token not configured")
        return False
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}"
    }
    
    payload = {
        "replyToken": reply_token,
        "messages": messages
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{LINE_API_BASE}/message/reply",
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    return True
                else:
                    error_text = await response.text()
                    print(f"[LINE] Failed to reply: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"[LINE] Error sending reply: {e}")
            return False


async def reply_text(reply_token: str, text: str) -> bool:
    """
    Convenience function to reply with a simple text message.
    
    Args:
        reply_token: Reply token from webhook event
        text: Text message to send (max 2000 characters)
        
    Returns:
        True if successful, False otherwise
    """
    # Truncate text if too long
    truncated_text = text[:2000] if len(text) > 2000 else text
    
    messages = [
        {
            "type": "text",
            "text": truncated_text
        }
    ]
    
    return await reply_message(reply_token, messages)


async def push_message(user_id: str, messages: List[Dict[str, Any]]) -> bool:
    """
    Push a message to a user (does not require reply token).
    
    Docs: https://developers.line.biz/en/reference/messaging-api/#send-push-message
    
    Args:
        user_id: LINE user ID
        messages: List of message objects to send
        
    Returns:
        True if successful, False otherwise
    """
    if not settings.LINE_CHANNEL_ACCESS_TOKEN:
        print("[LINE] Channel access token not configured")
        return False
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}"
    }
    
    payload = {
        "to": user_id,
        "messages": messages
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{LINE_API_BASE}/message/push",
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    return True
                else:
                    error_text = await response.text()
                    print(f"[LINE] Failed to push message: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"[LINE] Error pushing message: {e}")
            return False
