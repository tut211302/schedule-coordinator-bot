import json

from fastapi import APIRouter, HTTPException, Request, status

from line.config import LINE_CHANNEL_SECRET
from line.handlers import handle_line_events
from line.signature import verify_line_signature

line_router = APIRouter()


@line_router.post("/webhook/line")
async def line_webhook(request: Request):
    """
    LINE Messaging API webhook endpoint.
    - Signature verification with LINE_CHANNEL_SECRET
    - Filters to text messages; actual handling is delegated to handle_line_events
    """
    if not LINE_CHANNEL_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LINE_CHANNEL_SECRET is not configured",
        )

    signature = request.headers.get("x-line-signature", "")
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-Line-Signature header",
        )

    body = await request.body()
    if not verify_line_signature(body, signature, LINE_CHANNEL_SECRET):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature",
        )

    try:
        payload = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    events = payload.get("events", [])
    await handle_line_events(events)
    return {"success": True, "handledEvents": len(events)}

