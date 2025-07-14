from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

router = APIRouter()

class Trade(BaseModel):
    id: int
    pair: str
    type: str
    pnl_pct: float
    opened_at: datetime
    closed_at: datetime

@router.get("/", response_model=List[Trade])
async def list_trades(
    strategy: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    page: int = 1,
):
    return [
        Trade(
            id=1,
            pair="EUR/USD",
            type="long",
            pnl_pct=2.3,
            opened_at=datetime.utcnow(),
            closed_at=datetime.utcnow(),
        )
    ]

@router.get("/{trade_id}", response_model=Trade)
async def get_trade(trade_id: int):
    return Trade(
        id=trade_id,
        pair="EUR/USD",
        type="long",
        pnl_pct=2.3,
        opened_at=datetime.utcnow(),
        closed_at=datetime.utcnow(),
    )
