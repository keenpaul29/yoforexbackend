from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import random
from services.finnhub_service import finnhub_client

router = APIRouter()

class NewsArticle(BaseModel):
    headline: str
    summary: str
    url: str
    time: str
    source: str
    sentiment: str = "neutral"  # positive, negative, neutral

class Insight(BaseModel):
    message: str
    impact: str 
    source: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class RiskReminder(BaseModel):
    message: str
    impact: str  # high, medium, low
    symbol: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class MarketEvent(BaseModel):
    event: str
    time: str
    impact: str
    symbol: Optional[str] = None
    url: Optional[str] = None

class TradingNewsResponse(BaseModel):
    daily_insight: Insight
    risk_reminder: RiskReminder
    market_events: List[MarketEvent]
    top_news: List[NewsArticle] = []

@router.get("/", response_model=TradingNewsResponse)
async def get_trading_news():
    try:
        # Fetch market news from FinnHub
        market_news = await finnhub_client.get_market_news()
        
        if not market_news:
            raise HTTPException(status_code=500, detail="Failed to fetch market news")
        
        # Process top 3 news articles
        top_news = []
        for article in market_news[:3]:
            top_news.append(NewsArticle(
                headline=article.get('headline', 'No headline'),
                summary=article.get('summary', 'No summary available'),
                url=article.get('url', '#'),
                time=datetime.fromtimestamp(article.get('datetime', 0)).strftime('%Y-%m-%d %H:%M:%S'),
                source=article.get('source', 'Unknown'),
                sentiment=random.choice(['positive', 'neutral', 'negative'])
            ))
        
        # Create a daily insight based on the latest news
        latest_news = market_news[0]
        daily_insight = Insight(
            message=f"{latest_news.get('headline', 'Market update available')}",
            impact=random.choice(['positive', 'neutral', 'high']),
            source=latest_news.get('source', 'Market Data')
        )
        
        # Create a risk reminder (this is a simplified example)
        risk_reminder = RiskReminder(
            message="Market shows increased volatility",
            impact=random.choice(['high', 'medium']),
            symbol="SPY"  # Example symbol
        )
        
        # Create market events from news
        market_events = []
        for event in market_news[:2]:  # Get top 2 events
            market_events.append(MarketEvent(
                event=event.get('headline', 'Market Event'),
                time=datetime.fromtimestamp(event.get('datetime', 0)).strftime('%Y-%m-%d %H:%M'),
                impact=random.choice(['high', 'medium', 'low']),
                url=event.get('url', '#')
            ))
        
        return {
            "daily_insight": daily_insight,
            "risk_reminder": risk_reminder,
            "market_events": market_events,
            "top_news": top_news
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching market data: {str(e)}")
    
    finally:
        # Ensure the client is properly closed
        if 'finnhub_client' in locals():
            await finnhub_client.close()
    return 