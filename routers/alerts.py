from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()

class PriceAlert(BaseModel):
    id: int
    pair: str
    target: float
    direction: str  # "up" or "down"

@router.get("/price", response_model=List[PriceAlert])
async def list_price_alerts():
    return [
        PriceAlert(id=1, pair="EUR/USD", target=1.0950, direction="up"),
        PriceAlert(id=2, pair="GBP/JPY", target=139.50, direction="down"),
    ]

@router.post("/price", response_model=PriceAlert)
async def create_price_alert(alert: PriceAlert):
    # echo back; persist in your DB
    return alert
