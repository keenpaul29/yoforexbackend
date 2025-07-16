from datetime import datetime
from typing import Optional, Union, Dict, Any

from pydantic import BaseModel


class TechnicalAnalysis(BaseModel):

    RSI: Optional[Union[float, str]]
    MACD: Optional[Union[float, str]]
    Moving_Average: Optional[Union[float, str]]
    ICT_Order_Block: str
    ICT_Fair_Value_Gap: str
    ICT_Breaker_Block: str
    ICT_Trendline: str


class ScalpAnalysis(BaseModel):

    signal: str
    confidence: Union[int, str]  # allow "75%" or 75
    entry: float
    stop_loss: float
    take_profit: float
    risk_reward_ratio: str
    timeframe: str  # e.g. M1 / M5 etc. – validated at the router level
    technical_analysis: TechnicalAnalysis
    recommendation: str
    dynamic_stop_loss: Union[float, str]   # allow 3.5 or "Calculated above…"
    dynamic_take_profit: Union[float, str]  # allow 1.8 or descriptive text


class ScalpAnalysisHistoryItem(BaseModel):

    id: int
    analysis: Dict[str, Any]
    created_at: datetime

    class Config:
        orm_mode = True

@router.on_event("startup")
async def start_alert_sync_task():
    """
    Schedule the periodic sync loop when the router is mounted.
    """
    # This will run in the background for the lifetime of the app
    asyncio.create_task(_periodic_alert_sync())
