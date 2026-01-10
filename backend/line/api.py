from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from db.line_users import upsert_line_user

line_api_router = APIRouter()


class LineLinkRequest(BaseModel):
    line_user_id: str = Field(..., min_length=1)
    display_name: Optional[str] = None
    picture_url: Optional[str] = None
    session_id: Optional[str] = None


@line_api_router.post("/api/line/link")
async def link_line_user(payload: LineLinkRequest):
    if not payload.line_user_id:
        raise HTTPException(status_code=400, detail="line_user_id is required")
    upsert_line_user(payload.line_user_id, payload.display_name, payload.picture_url)
    return {"success": True}
