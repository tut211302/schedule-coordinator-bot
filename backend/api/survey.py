"""
Restaurant survey API endpoints.
Handles saving and retrieving restaurant search conditions.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from db.restaurant_conditions import (
    save_restaurant_conditions,
    get_restaurant_conditions,
    get_aggregated_conditions,
)
from api.hotpepper import search_restaurants


survey_router = APIRouter()


class SurveyRequest(BaseModel):
    """Request model for submitting restaurant survey."""
    line_user_id: str = Field(..., min_length=1)
    session_id: Optional[int] = None
    area: Optional[str] = None
    genre_codes: Optional[List[str]] = None
    budget_code: Optional[str] = None


class SurveyResponse(BaseModel):
    """Response model for survey submission."""
    success: bool
    message: str
    id: Optional[int] = None


@survey_router.post("/api/survey/conditions", response_model=SurveyResponse)
async def submit_survey(request: SurveyRequest):
    """
    Submit restaurant search conditions.
    """
    try:
        record_id = save_restaurant_conditions(
            line_user_id=request.line_user_id,
            session_id=request.session_id,
            area=request.area,
            genre_codes=request.genre_codes,
            budget_code=request.budget_code
        )
        
        return SurveyResponse(
            success=True,
            message="条件を保存しました",
            id=record_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@survey_router.get("/api/survey/conditions/{session_id}")
async def get_session_conditions(session_id: int):
    """
    Get all restaurant conditions for a session.
    """
    try:
        conditions = get_restaurant_conditions(session_id=session_id)
        return {
            "success": True,
            "conditions": conditions,
            "count": len(conditions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@survey_router.get("/api/survey/conditions/{session_id}/aggregated")
async def get_aggregated_session_conditions(session_id: int):
    """
    Get aggregated restaurant conditions for a session.
    Returns combined preferences from all users.
    """
    try:
        aggregated = get_aggregated_conditions(session_id=session_id)
        return {
            "success": True,
            **aggregated
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@survey_router.get("/api/survey/search")
async def search_shops(
    area: Optional[str] = None,
    genre: Optional[str] = None,
    budget: Optional[str] = None,
    keyword: Optional[str] = None,
    count: int = 10
):
    """
    Search restaurants using Hotpepper API.
    """
    try:
        genre_codes = [genre] if genre else None
        
        results = await search_restaurants(
            area=area,
            genre_codes=genre_codes,
            budget_code=budget,
            keyword=keyword,
            count=count
        )
        
        return {
            "success": True,
            **results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@survey_router.get("/api/survey/search/session/{session_id}")
async def search_shops_for_session(session_id: int, count: int = 10):
    """
    Search restaurants based on aggregated session conditions.
    Uses the most popular preferences from all users.
    """
    try:
        # Get aggregated conditions
        aggregated = get_aggregated_conditions(session_id=session_id)
        
        if aggregated["total_respondents"] == 0:
            return {
                "success": True,
                "message": "まだ誰も条件を入力していません",
                "results_available": 0,
                "shops": []
            }
        
        # Use the most popular area
        area = aggregated["areas"][0] if aggregated["areas"] else None
        
        # Use the most popular genre
        genre_codes = None
        if aggregated["genre_codes"]:
            sorted_genres = sorted(
                aggregated["genre_codes"].items(),
                key=lambda x: x[1],
                reverse=True
            )
            genre_codes = [sorted_genres[0][0]] if sorted_genres else None
        
        # Use the most popular budget
        budget_code = None
        if aggregated["budget_codes"]:
            sorted_budgets = sorted(
                aggregated["budget_codes"].items(),
                key=lambda x: x[1],
                reverse=True
            )
            budget_code = sorted_budgets[0][0] if sorted_budgets else None
        
        results = await search_restaurants(
            area=area,
            genre_codes=genre_codes,
            budget_code=budget_code,
            count=count
        )
        
        return {
            "success": True,
            "used_conditions": {
                "area": area,
                "genre_codes": genre_codes,
                "budget_code": budget_code
            },
            "aggregated_from": aggregated["total_respondents"],
            **results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
