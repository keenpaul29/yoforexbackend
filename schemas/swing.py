import os
import asyncio
import httpx
from fastapi import Depends, APIRouter

# … your existing imports, PriceAlert, alerts list, etc. …

# URL of the external alerts API (set via env or hardcode)
ALERTS_API_URL = os.getenv("ALERTS_API_URL", "https://your-api.com/api/price")
SYNC_INTERVAL   = int(os.getenv("ALERT_SYNC_INTERVAL", 60))  # seconds

async def sync_alerts_from_remote():
    """
    Fetch the latest alerts from ALERTS_API_URL
    and overwrite our in-memory `alerts` list.
    """
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(ALERTS_API_URL)
            resp.raise_for_status()
            data = resp.json()  # expecting List[ {id,pair,target,direction} ]

        # Replace the in-memory list in-place to keep references valid.
        alerts.clear()
        for item in data:
            # validate via Pydantic
            alerts.append(PriceAlert(**item))

        print(f"[alerts] synced {len(alerts)} items from remote")
    except Exception as e:
        print(f"[alerts] failed to sync: {e!r}")

async def _periodic_alert_sync():
    # wait a bit before first sync (optional)
    await asyncio.sleep(1)
    while True:
        await sync_alerts_from_remote()
        await asyncio.sleep(SYNC_INTERVAL)

# Hook into FastAPI startup
from fastapi import FastAPI

@router.on_event("startup")
async def start_alert_sync_task():
    """
    Schedule the periodic sync loop when the router is mounted.
    """
    # This will run in the background for the lifetime of the app
    asyncio.create_task(_periodic_alert_sync())
