from fastapi import APIRouter
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter()

class Quote(BaseModel):
    pair: str
    price: float
    change_pct: float

@router.get("/quotes", response_model=List[Quote])
async def get_quotes(pairs: Optional[str] = None):
    # stubbed data – replace with real data source
    dummy = [
        Quote(pair="EUR/USD", price=1.0892, change_pct=0.05),
        Quote(pair="GBP/USD", price=1.2754, change_pct=-0.12),
        Quote(pair="USD/JPY", price=138.92, change_pct=0.23),
        Quote(pair="AUD/USD", price=0.6598, change_pct=0.08),
        Quote(pair="USD/CAD", price=1.3465, change_pct=-0.03),
    ]
    if pairs:
        wanted = {p.upper() for p in pairs.split(",")}
        return [q for q in dummy if q.pair.replace("/", "") in wanted]
    return dummy

class MarketEvent(BaseModel):
    symbol: str
    impact: str
    time: str

class UpcomingEvent(BaseModel):
    symbol: str
    in_minutes: int

class MarketEventsResponse(BaseModel):
    historic: List[MarketEvent]
    upcoming: List[UpcomingEvent]

@router.get("/events", response_model=MarketEventsResponse)
async def get_events(
    impact: Optional[str] = "all",  # high, extreme or all
    upcoming_window: Optional[int] = 120,
):
    # stubbed; wire this into your econ‐calendar service
    return MarketEventsResponse(
        historic=[
            MarketEvent(symbol="USD CPI Data", impact="High", time="14:30"),
            MarketEvent(symbol="USD FOMC Statement", impact="Extreme", time="16:00"),
            MarketEvent(symbol="GBP Employment Change", impact="High", time="08:00"),
        ],
        upcoming=[
            UpcomingEvent(symbol="USD CPI Data", in_minutes=30),
            UpcomingEvent(symbol="EUR ECB Speech", in_minutes=45),
        ],
    )
