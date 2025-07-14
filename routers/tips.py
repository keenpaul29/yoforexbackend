from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()

class Tip(BaseModel):
    id: str
    title: str
    body: str

@router.get("/", response_model=List[Tip])
async def get_tips():
    return [
        Tip(id="daily_insight", title="Daily Insight", body="USD is showing strength…"),
        Tip(id="risk_reminder", title="Risk Management Reminder", body="Never risk more than 2%…"),
    ]
