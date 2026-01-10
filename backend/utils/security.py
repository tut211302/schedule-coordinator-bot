"""
Security utilities for webhook signature validation.
"""

import base64
import hmac
import hashlib
from fastapi import HTTPException, Request
from config import settings


async def validate_line_signature(request: Request) -> str:
    """
    Validate LINE webhook request signature.
    
    LINE uses HMAC-SHA256 signature to verify that requests come from LINE servers.
    Docs: https://developers.line.biz/en/reference/messaging-api/#signature-validation
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Request body as string if signature is valid
        
    Raises:
        HTTPException: If signature is invalid or missing
    """
    signature = request.headers.get("x-line-signature")
    
    if not signature:
        raise HTTPException(status_code=401, detail="Missing X-Line-Signature header")
    
    body = await request.body()
    body_str = body.decode("utf-8")
    
    # Calculate expected signature
    channel_secret = settings.LINE_CHANNEL_SECRET
    if not channel_secret:
        raise HTTPException(status_code=500, detail="LINE_CHANNEL_SECRET not configured")
    
    mac = hmac.new(
        channel_secret.encode("utf-8"),
        body,
        hashlib.sha256
    ).digest()
    expected_signature = base64.b64encode(mac).decode("utf-8")
    
    # Constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(expected_signature, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    return body_str
