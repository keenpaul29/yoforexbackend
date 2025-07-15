# backend/routers/alerts.py

import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import List, Dict
import httpx

router = APIRouter()

# ———  Data model & in-memory store  ———
class PriceAlert(BaseModel):
    id: int
    pair: str         # e.g. "BTC/USD" or "XAU/USD"
    target: float
    direction: str    # "up" or "down"

alerts: List[PriceAlert] = []

# Major pairs you want to stream
MAJOR_PAIRS = ["EUR/USD", "GBP/JPY", "XAU/USD", "BTC/USD", "ETH/USD"]
FETCH_INTERVAL = 1  # seconds

# ———  REST endpoints  ———
@router.get("/price", response_model=List[PriceAlert])
async def list_price_alerts():
    return alerts

@router.post("/price", response_model=PriceAlert)
async def create_price_alert(alert: PriceAlert):
    alerts.append(alert)
    return alert

# ———  Helper to fetch live price  ———
async def fetch_price(pair: str) -> float:
    base, quote = pair.split("/", 1)
    async with httpx.AsyncClient(timeout=10) as client:
        if base in ("BTC", "ETH"):
            # Crypto via CoinGecko
            resp = await client.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": base.lower(), "vs_currencies": quote.lower()}
            )
            data = resp.json()
            return data[base.lower()][quote.lower()]
        else:
            # Forex/Gold via exchangerate.host
            resp = await client.get(
                "https://api.exchangerate.host/convert",
                params={"from": base, "to": quote}
            )
            return resp.json()["result"]

# ———  WebSocket connection manager  ———
class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, message: Dict):
        for ws in list(self.active):
            try:
                await ws.send_json(message)
            except WebSocketDisconnect:
                self.disconnect(ws)

price_manager = ConnectionManager()
alert_manager = ConnectionManager()

# ———  WS: live prices feed  ———
@router.websocket("/ws/prices")
async def websocket_prices(ws: WebSocket):
    await price_manager.connect(ws)
    try:
        while True:
            snapshot = {p: await fetch_price(p) for p in MAJOR_PAIRS}
            await price_manager.broadcast({"type": "prices", "data": snapshot})
            await asyncio.sleep(FETCH_INTERVAL)
    finally:
        price_manager.disconnect(ws)

# ———  WS: alert notifications  ———
@router.websocket("/ws/alerts")
async def websocket_alerts(ws: WebSocket):
    await alert_manager.connect(ws)
    try:
        while True:
            for alert in alerts:
                current = await fetch_price(alert.pair)
                if (
                    (alert.direction == "up"   and current >= alert.target)
                    or
                    (alert.direction == "down" and current <= alert.target)
                ):
                    await alert_manager.broadcast({
                        "type": "alert",
                        "id": alert.id,
                        "pair": alert.pair,
                        "current": current,
                        "target": alert.target,
                        "direction": alert.direction
                    })
            await asyncio.sleep(FETCH_INTERVAL)
    finally:
        alert_manager.disconnect(ws)
