from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()

class DayStat(BaseModel):
    day: str
    net_pct: float

class PerformanceStats(BaseModel):
    total_trades: int
    win_rate: float
    profit_factor: float
    total_profit: float
    by_day: List[DayStat]

@router.get("/", response_model=PerformanceStats)
async def get_performance(period: str = "week"):
    # stubbed–
    return PerformanceStats(
        total_trades=47,
        win_rate=71.2,
        profit_factor=2.8,
        total_profit=1248,
        by_day=[
            DayStat(day="Mon", net_pct=0.8),
            DayStat(day="Tue", net_pct=1.2),
            DayStat(day="Wed", net_pct=-0.4),
            DayStat(day="Thu", net_pct=1.6),
            DayStat(day="Fri", net_pct=0.7),
            DayStat(day="Sat", net_pct=2.0),
            DayStat(day="Sun", net_pct=1.1),
        ],
    )
