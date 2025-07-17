import os
import httpx
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

class FinnhubService:
    def __init__(self):
        self.api_key = os.getenv("FINNHUB_API_KEY")
        if not self.api_key:
            raise ValueError("FINNHUB_API_KEY not found in environment variables")
        self.base_url = "https://finnhub.io/api/v1"
        self.client = httpx.AsyncClient()

    async def get_market_news(self):
        """Fetch general market news"""
        try:
            response = await self.client.get(
                f"{self.base_url}/news",
                params={
                    "category": "general",
                    "token": self.api_key
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching market news: {str(e)}")
            return []

    async def get_company_news(self, symbol: str):
        """Fetch news for a specific company"""
        try:
            # Get date range (last 30 days)
            to_date = datetime.now()
            from_date = to_date - timedelta(days=30)
            
            response = await self.client.get(
                f"{self.base_url}/company-news",
                params={
                    "symbol": symbol,
                    "from": from_date.strftime('%Y-%m-%d'),
                    "to": to_date.strftime('%Y-%m-%d'),
                    "token": self.api_key
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching company news: {str(e)}")
            return []

    async def close(self):
        await self.client.aclose()

# Create a singleton instance
finnhub_client = FinnhubService()
