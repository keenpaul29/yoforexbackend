from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from utils.db import engine, Base
from routers import (
    auth,
    scalp,
    swing,
    market,
    performance,
    tools,
    community,
    tips,
    trades,
    prices
)
from schemas.swing import start_alert_sync_task

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="YoForex Chart Analysis API",
    version="1.1.0",
    description="Upload a trading chart image and get an AI‐powered analysis in JSON.",
)

origins = [
    "http://localhost:3000",
    "https://app.axiontrust.com",
    "https://axiontrust.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# your existing routers
app.include_router(auth.router)
app.include_router(scalp.router, prefix="/scalp", tags=["Chart Analysis"])
app.include_router(swing.router, prefix="/swing", tags=["Chart Analysis"])

# new functionality
app.include_router(market.router, prefix="/market", tags=["Market"])
app.include_router(performance.router, prefix="/performance", tags=["Performance"])
app.include_router(tools.router, prefix="/tools", tags=["Tools"])
app.include_router(community.router, prefix="/community", tags=["Community"])

# Initialize background tasks
@app.on_event("startup")
async def startup_event():
    await start_alert_sync_task()
app.include_router(tips.router, prefix="/tips", tags=["Tips"])
app.include_router(trades.router, prefix="/trades", tags=["Trades"])
app.include_router(prices.router, prefix="/prices", tags=["Prices"])