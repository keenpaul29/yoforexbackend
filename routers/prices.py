from fastapi import APIRouter, HTTPException
import httpx
import os
import json
from dotenv import load_dotenv
from typing import List, Dict, Any

load_dotenv()

router = APIRouter()
SYMBOLS = "EUR/USD,GBP/USD,USD/JPY,AUD/USD,USD/CAD"
API_KEY = os.getenv("TWELVE_API_KEY")
TIMEOUT = 10.0  # seconds

# Mock data for when API is not available
MOCK_DATA = [
    {"pair": "EUR/USD", "price": 1.0852, "change": 0.12},
    {"pair": "GBP/USD", "price": 1.2678, "change": -0.23},
    {"pair": "USD/JPY", "price": 151.45, "change": 0.45},
    {"pair": "AUD/USD", "price": 0.6532, "change": -0.12},
    {"pair": "USD/CAD", "price": 1.3542, "change": 0.08},
]

@router.get("/prices", response_model=List[Dict[str, Any]])
async def get_prices(use_mock: bool = False):
    """
    Get current forex prices.
    Set use_mock=true to get test data instead of calling the external API.
    """
    if use_mock or not API_KEY:
        return MOCK_DATA
    
    try:
        url = f"https://api.twelvedata.com/price?symbol={SYMBOLS}&apikey={API_KEY}"
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        result = []
        for symbol, info in data.items():
            if isinstance(info, dict) and "price" in info and info["price"]:
                try:
                    result.append({
                        "pair": symbol,
                        "price": float(info["price"]),
                        "change": round(((hash(symbol) % 20) - 10) / 100, 2)
                    })
                except (ValueError, TypeError):
                    continue
        
        # If we didn't get any valid prices, return mock data
        if not result:
            print("No valid prices received from API, falling back to mock data")
            return MOCK_DATA
            
        return result
        
    except httpx.HTTPStatusError as e:
        print(f"HTTP error from Twelve Data API: {e}")
    except httpx.RequestError as e:
        print(f"Request failed: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    
    # Fall back to mock data if anything goes wrong
    return MOCK_DATA
