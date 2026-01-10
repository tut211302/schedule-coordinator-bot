import requests
import os
from typing import Optional, Dict, Any, List

HOTPEPPER_API_KEY = os.getenv("HOTPEPPER_API_KEY")

url = "http://webservice.recruit.co.jp/hotpepper/gourmet/v1/"

def search_restaurants(
        area_code: str = "Z011",
        genre_code: str = "G001",
        count: int = 10,
        budget_code: Optional[str] = "B002",
        )->List[Dict[str,Any]]:

    if not HOTPEPPER_API_KEY:
        print("HOTPEPPER_API_KEY does not exist")
        return []
    
    params = {
            "key": HOTPEPPER_API_KEY,
            "format": "json",
            "large_area": area_code,
            "genre": genre_code,
            "count": count,
            "order": 4,
            "budget": budget_code,
            "party_capacity": 4
            }

    try:
        response = requests.get(url,params = params)
        response.raise_for_status()

        data = response.json()
        
        if "results" in data and "shop" in data['results']:
            return data['results']['shop']

        return []

    except requests.exceptions.RequestException as e:
        print(f"HOT PEPPER API request error: {e}")
        return []

