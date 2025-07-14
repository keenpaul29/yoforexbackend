from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
from typing import List

router = APIRouter()

class PreTradeCalcRequest(BaseModel):
    entry: float
    stop: float
    risk_pct: float

class PreTradeCalcResponse(BaseModel):
    risk_amount: float
    position_size: float

@router.post("/pretrade/calc", response_model=PreTradeCalcResponse)
async def pretrade_calc(req: PreTradeCalcRequest):
    # assume $10k balance for demo
    risk_amount = req.risk_pct / 100 * 10_000
    position_size = risk_amount / abs(req.entry - req.stop)
    return PreTradeCalcResponse(risk_amount=risk_amount, position_size=position_size)

class AIAnalysisRequest(BaseModel):
    pair: str
    timeframe: str

@router.post("/ai-analysis")
async def ai_analysis(req: AIAnalysisRequest):
    # stub – plug your AI model here
    return {"analysis": f"Signal for {req.pair} on {req.timeframe}"}

class BacktestRequest(BaseModel):
    strategy: str
    pair: str
    from_date: datetime
    to_date: datetime

class BacktestResult(BaseModel):
    total_trades: int
    win_rate: float
    profit_factor: float
    net_profit: float

@router.post("/backtest", response_model=BacktestResult)
async def backtest(req: BacktestRequest):
    # stub – integrate with your backtester
    return BacktestResult(
        total_trades=50, win_rate=0.72, profit_factor=2.5, net_profit=1500
    )
