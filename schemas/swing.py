from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import os
import asyncio
import httpx
from fastapi import Depends, APIRouter

# … your existing imports, PriceAlert, alerts list, etc. …

# Configuration for alerts
ALERTS_API_URL = os.getenv("ALERTS_API_URL")
SYNC_INTERVAL = int(os.getenv("ALERT_SYNC_INTERVAL", 300))  # Default to 5 minutes
ALERTS_ENABLED = os.getenv("ALERTS_ENABLED", "false").lower() == "true"

async def sync_alerts_from_remote():
    """
    Fetch the latest alerts from ALERTS_API_URL
    and overwrite our in-memory `alerts` list.
    """
    if not ALERTS_ENABLED or not ALERTS_API_URL:
        print("[alerts] Alert syncing is disabled. Set ALERTS_ENABLED=true and ALERTS_API_URL to enable.")
        return

    try:
        print(f"[alerts] Fetching alerts from {ALERTS_API_URL}")
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(ALERTS_API_URL)
            resp.raise_for_status()
            data = resp.json()  # expecting List[ {id,pair,target,direction} ]

        # Replace the in-memory list in-place to keep references valid.
        alerts = []
        for item in data:
            try:
                # validate via Pydantic
                alerts.append(PriceAlert(**item))
            except Exception as e:
                print(f"[alerts] Invalid alert format: {e}")

        print(f"[alerts] Successfully synced {len(alerts)} alerts")
        return alerts
    except httpx.HTTPStatusError as e:
        print(f"[alerts] HTTP error while fetching alerts: {e}")
    except httpx.RequestError as e:
        print(f"[alerts] Failed to connect to alerts API: {e}")
    except Exception as e:
        print(f"[alerts] Unexpected error: {e}")
    return []

async def _periodic_alert_sync():
    # Initial delay to let the app start up
    await asyncio.sleep(5)
    
    if not ALERTS_ENABLED or not ALERTS_API_URL:
        print("[alerts] Alert syncing is disabled. Set ALERTS_ENABLED=true and ALERTS_API_URL to enable.")
        return
        
    print(f"[alerts] Starting alert sync service. Interval: {SYNC_INTERVAL}s")
    
    while True:
        try:
            await sync_alerts_from_remote()
        except Exception as e:
            print(f"[alerts] Error in sync task: {e}")
        await asyncio.sleep(SYNC_INTERVAL)

# This function will be called from app.py on startup
async def start_alert_sync_task():
    """
    Schedule the periodic sync loop when the router is mounted.
    """
    if not ALERTS_ENABLED or not ALERTS_API_URL:
        print("[alerts] Alert syncing is disabled. Set ALERTS_ENABLED=true and ALERTS_API_URL to enable.")
        return
        
    # This will run in the background for the lifetime of the app
    asyncio.create_task(_periodic_alert_sync())
    print("[alerts] Alert sync service started")

class PriceAlert(BaseModel):
    id: str
    pair: str
    target: float
    direction: str

class SwingAnalysisHistoryItem(BaseModel):
    id: int
    created_at: datetime
    analysis: Dict[str, Any]

    class Config:
        orm_mode = True
