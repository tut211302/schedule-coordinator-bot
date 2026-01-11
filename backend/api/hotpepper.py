"""
Hotpepper API client for restaurant search.
"""

import os
import json
import aiohttp
from typing import Dict, List, Optional
from urllib.parse import urlencode


HOTPEPPER_API_KEY = os.getenv("HOTPEPPER_API_KEY", "")
HOTPEPPER_BASE_URL = "https://webservice.recruit.co.jp/hotpepper/gourmet/v1/"


async def search_restaurants(
    area: Optional[str] = None,
    genre_codes: Optional[List[str]] = None,
    budget_code: Optional[str] = None,
    keyword: Optional[str] = None,
    count: int = 10,
    start: int = 1
) -> Dict:
    """
    Search restaurants using Hotpepper API.
    
    Args:
        area: Free text area search (e.g., "渋谷")
        genre_codes: List of genre codes (e.g., ["G001"])
        budget_code: Budget code (e.g., "B002")
        keyword: Free text keyword search
        count: Number of results to return (max 100)
        start: Starting position for pagination
    
    Returns:
        Dictionary containing search results
    """
    if not HOTPEPPER_API_KEY:
        return {
            "error": "HOTPEPPER_API_KEY is not configured",
            "results_available": 0,
            "results_returned": 0,
            "shops": []
        }
    
    params = {
        "key": HOTPEPPER_API_KEY,
        "format": "json",
        "count": min(count, 100),
        "start": start,
    }
    
    # Add optional parameters
    if area:
        params["keyword"] = area  # Use keyword for area search
    
    if genre_codes and len(genre_codes) > 0:
        # Hotpepper accepts multiple genre codes
        params["genre"] = genre_codes[0]  # Primary genre
    
    if budget_code:
        params["budget"] = budget_code
    
    if keyword:
        if "keyword" in params:
            params["keyword"] += f" {keyword}"
        else:
            params["keyword"] = keyword
    
    url = f"{HOTPEPPER_BASE_URL}?{urlencode(params)}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return {
                        "error": f"API request failed with status {response.status}",
                        "results_available": 0,
                        "results_returned": 0,
                        "shops": []
                    }
                
                # Hotpepper returns text/javascript;charset=utf-8 even for JSON
                try:
                    data = await response.json(content_type=None)
                except Exception:
                    text = await response.text()
                    try:
                        data = json.loads(text)
                    except json.JSONDecodeError:
                        return {
                            "error": "Failed to decode API response",
                            "results_available": 0,
                            "results_returned": 0,
                            "shops": []
                        }
                results = data.get("results", {})
                
                shops = results.get("shop", [])
                
                # Format shop data for easier consumption
                formatted_shops = []
                for shop in shops:
                    formatted_shops.append({
                        "id": shop.get("id"),
                        "name": shop.get("name"),
                        "name_kana": shop.get("name_kana"),
                        "address": shop.get("address"),
                        "station_name": shop.get("station_name"),
                        "access": shop.get("access"),
                        "url": shop.get("urls", {}).get("pc"),
                        "photo": shop.get("photo", {}).get("pc", {}).get("l"),
                        "photo_s": shop.get("photo", {}).get("pc", {}).get("s"),
                        "genre": shop.get("genre", {}).get("name"),
                        "budget": shop.get("budget", {}).get("name"),
                        "budget_average": shop.get("budget", {}).get("average"),
                        "open": shop.get("open"),
                        "close": shop.get("close"),
                        "catch": shop.get("catch"),
                        "capacity": shop.get("capacity"),
                        "private_room": shop.get("private_room"),
                        "card": shop.get("card"),
                        "non_smoking": shop.get("non_smoking"),
                        "parking": shop.get("parking"),
                        "lat": shop.get("lat"),
                        "lng": shop.get("lng"),
                    })
                
                return {
                    "results_available": int(results.get("results_available", 0)),
                    "results_returned": int(results.get("results_returned", 0)),
                    "results_start": int(results.get("results_start", 1)),
                    "shops": formatted_shops
                }
                
    except aiohttp.ClientError as e:
        return {
            "error": f"Network error: {str(e)}",
            "results_available": 0,
            "results_returned": 0,
            "shops": []
        }
    except Exception as e:
        return {
            "error": f"Unexpected error: {str(e)}",
            "results_available": 0,
            "results_returned": 0,
            "shops": []
        }


async def fetch_restaurant_by_id(shop_id: str) -> Dict:
    """
    Fetch a single restaurant by Hotpepper shop ID.
    """
    if not HOTPEPPER_API_KEY:
        return {
            "error": "HOTPEPPER_API_KEY is not configured",
            "results_available": 0,
            "results_returned": 0,
            "shops": []
        }

    params = {
        "key": HOTPEPPER_API_KEY,
        "format": "json",
        "id": shop_id,
        "count": 1,
    }
    url = f"{HOTPEPPER_BASE_URL}?{urlencode(params)}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return {
                        "error": f"API request failed with status {response.status}",
                        "results_available": 0,
                        "results_returned": 0,
                        "shops": []
                    }

                try:
                    data = await response.json(content_type=None)
                except Exception:
                    text = await response.text()
                    try:
                        data = json.loads(text)
                    except json.JSONDecodeError:
                        return {
                            "error": "Failed to decode API response",
                            "results_available": 0,
                            "results_returned": 0,
                            "shops": []
                        }

                results = data.get("results", {})
                shops = results.get("shop", [])
                if not shops:
                    return {
                        "results_available": 0,
                        "results_returned": 0,
                        "shops": []
                    }

                shop = shops[0]
                formatted = {
                    "id": shop.get("id"),
                    "name": shop.get("name"),
                    "name_kana": shop.get("name_kana"),
                    "address": shop.get("address"),
                    "station_name": shop.get("station_name"),
                    "access": shop.get("access"),
                    "url": shop.get("urls", {}).get("pc"),
                    "photo": shop.get("photo", {}).get("pc", {}).get("l"),
                    "photo_s": shop.get("photo", {}).get("pc", {}).get("s"),
                    "genre": shop.get("genre", {}).get("name"),
                    "budget": shop.get("budget", {}).get("name"),
                    "budget_average": shop.get("budget", {}).get("average"),
                    "open": shop.get("open"),
                    "close": shop.get("close"),
                    "catch": shop.get("catch"),
                    "capacity": shop.get("capacity"),
                    "private_room": shop.get("private_room"),
                    "card": shop.get("card"),
                    "non_smoking": shop.get("non_smoking"),
                    "parking": shop.get("parking"),
                    "lat": shop.get("lat"),
                    "lng": shop.get("lng"),
                }

                return {
                    "results_available": int(results.get("results_available", 0)),
                    "results_returned": int(results.get("results_returned", 0)),
                    "results_start": int(results.get("results_start", 1)),
                    "shops": [formatted]
                }

    except aiohttp.ClientError as e:
        return {
            "error": f"Network error: {str(e)}",
            "results_available": 0,
            "results_returned": 0,
            "shops": []
        }
    except Exception as e:
        return {
            "error": f"Unexpected error: {str(e)}",
            "results_available": 0,
            "results_returned": 0,
            "shops": []
        }


def format_shops_for_line_carousel(
    shops: List[Dict],
    session_id: Optional[int] = None,
    max_items: int = 10,
    vote_label: str = "ここがいい！",
    include_vote_action: bool = True,
) -> List[Dict]:
    """
    Format shop data for LINE Flex Message carousel.
    
    Args:
        shops: List of shop dictionaries from search_restaurants
        max_items: Maximum number of items (LINE carousel max is 10)
    
    Returns:
        List of carousel column dictionaries
    """
    columns = []
    
    for shop in shops[:max_items]:
        # Truncate text to fit LINE limits
        title = (shop.get("name", "お店")[:40]) if shop.get("name") else "お店"
        text = shop.get("catch", "") or shop.get("access", "") or ""
        text = text[:60] if text else "詳細はリンクをご確認ください"
        
        postback_data = {
            "action": "select_shop",
            "shop_id": shop.get("id"),
            "shop_name": shop.get("name", "")[:40],
        }
        if session_id is not None:
            postback_data["session_id"] = session_id

        actions = [
            {
                "type": "uri",
                "label": "🔗 お店の詳細",
                "uri": shop.get("url") or "https://www.hotpepper.jp/"
            }
        ]
        if include_vote_action:
            actions.append(
                {
                    "type": "postback",
                    "label": vote_label,
                    "displayText": vote_label,
                    "data": urlencode(postback_data)
                }
            )

        column = {
            "thumbnailImageUrl": shop.get("photo") or shop.get("photo_s") or "https://via.placeholder.com/300x200",
            "imageBackgroundColor": "#FFFFFF",
            "title": title,
            "text": text,
            "defaultAction": {
                "type": "uri",
                "label": "詳細を見る",
                "uri": shop.get("url") or "https://www.hotpepper.jp/"
            },
            "actions": actions,
        }
        
        columns.append(column)
    
    return columns


def create_line_carousel_message(
    shops: List[Dict],
    alt_text: str = "おすすめのお店",
    session_id: Optional[int] = None,
    vote_label: str = "ここがいい！",
    include_vote_action: bool = True,
) -> Dict:
    """
    Create a LINE Flex Message carousel from shop data.
    
    Args:
        shops: List of shop dictionaries
        alt_text: Alternative text for notifications
    
    Returns:
        LINE Flex Message dictionary
    """
    columns = format_shops_for_line_carousel(
        shops,
        session_id=session_id,
        vote_label=vote_label,
        include_vote_action=include_vote_action,
    )
    
    if not columns:
        return {
            "type": "text",
            "text": "条件に合うお店が見つかりませんでした。条件を変更してお試しください。"
        }
    
    return {
        "type": "template",
        "altText": alt_text,
        "template": {
            "type": "carousel",
            "columns": columns,
            "imageAspectRatio": "rectangle",
            "imageSize": "cover"
        }
    }
