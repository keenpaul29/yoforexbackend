# schemas/swing.py

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

class SwingAnalysis(BaseModel):
    signal: str
    confidence: Union[int, str]            # allow "75%" or 75
    entry: float
    stop_loss: float
    take_profit: float
    risk_reward_ratio: str
    timeframe: str
    technical_analysis: TechnicalAnalysis
    recommendation: str
    dynamic_stop_loss: Union[float, str]   # allow 3310.0 or "Calculated above…"
    dynamic_take_profit: Union[float, str]  # allow 3150.0 or descriptive text

class SwingAnalysisHistoryItem(BaseModel):
    id: int
    analysis: Dict[str, Any]
    created_at: datetime

    class Config:
        orm_mode = True
