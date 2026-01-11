import requests
import aiohttp
import os
from typing import Optional, Dict, Any, List

HOTPEPPER_API_KEY = os.getenv("HOTPEPPER_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

url = "http://webservice.recruit.co.jp/hotpepper/gourmet/v1/"

BUDGET_LIST=[
        {"code" : "B009", "min" : 0, "max" : 500},
        {"code" : "B010", "min" : 501, "max" : 1000},
        {"code" : "B011", "min" : 1001, "max" : 1500},
        {"code" : "B001", "min" : 1501, "max" : 2000},
        {"code" : "B002", "min" : 2001, "max" : 3000},
        {"code" : "B003", "min" : 3001, "max" : 4000},
        {"code" : "B008", "min" : 4001, "max" : 5000},
        {"code" : "B004", "min" : 5001, "max" : 7000},
        {"code" : "B005", "min" : 7001, "max" : 10000},
        {"code" : "B006", "min" : 10001, "max" : 15000},
        {"code" : "B012", "min" : 15001, "max" : 20000},
        {"code" : "B013", "min" : 20001, "max" : 30000},
        {"code" : "B014", "min" : 30001, "max" : 100000},
        ]

async def get_location(location_name: str)->Optional[Dict[str,float]]:
    geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"

    if not GOOGLE_API_KEY:
        print("Error:GOOGLE API KEY does not exist")
        return None

    params = {
            "address": location_name,
            "key": GOOGLE_API_KEY,
            "language": "ja",
            "region": "ja",
            }

    try:
        response = requests.get(geocode_url, params = params)
        response.raise_for_status()
        data = response.json()

        if data['status'] == 'OK' and data['results']:
            location = data['results'][0]['geometry']['location']
            return {"lat": location['lat'], "lng": location['lng']}

        else:
            print(f"Geocoding failed for '{location_name}'. Status: {data.get('status')}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Google geocoding API request error: {e}")
        return None

            
def get_budget_code(min_price: int,max_price: int) -> Optional[str]:
    if min_price > max_price:
        return None
    
    codes = set()

    for budget in BUDGET_LIST:
        budget_min = budget["min"]
        budget_max = budget["max"]

        if budget_min <= max_price and budget_max >= min_price:
            codes.add(budget["code"])

    sorted_codes = []
    for budget in BUDGET_LIST:
        if budget["code"] in codes:
            sorted_codes.append(budget["code"])
    result = sorted_codes[:2]

    if result:
        return ",".join(result)
    else:
        return None


async def search_restaurants(
        area_code: str = "Z011",
        genre_code: str = "G001",
        count: int = 10,
        min_price: int = 2000,
        max_price: int = 3000,
        location_name: str = "東京",
        )->List[Dict[str,Any]]:

    if not HOTPEPPER_API_KEY:
        print("HOTPEPPER_API_KEY does not exist")
        return []
    
    coords = await get_location(location_name)

    params = {
            "key": HOTPEPPER_API_KEY,
            "format": "json",
            "genre": genre_code,
            "count": count,
            "order": 4,
            "budget": get_budget_code(min_price, max_price),
            "party_capacity": 4,
            "lat": coords['lat'],
            "lng": coords['lng'],
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

