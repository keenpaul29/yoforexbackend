import os
import uuid
from fastapi import APIRouter, UploadFile, File, Query, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from utils.image_check import is_trading_chart
from utils.gemini_helper import analyze_image_with_gemini
from utils.db import get_db

import models
import schemas.swing as schemas

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter()

@router.post("/chart/")
async def analyze_chart(
    file: UploadFile = File(...),
    timeframe: str = Query(..., enum=["H1", "D1", "W1"], description="Swing timeframe"),
    db: Session = Depends(get_db)
):
    # 1) Save upload
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1] or ".png"
    path = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")
    with open(path, "wb") as out:
        out.write(await file.read())

    # 2) Validate it’s a chart
    if not is_trading_chart(path):
        os.remove(path)
        raise HTTPException(400, detail="Please upload a valid trading chart image.")

    # 3) Analyze and cleanup
    try:
        result = analyze_image_with_gemini(path, timeframe)
    finally:
        os.remove(path)

    
    # 4) Persist into history
    record = models.SwingAnalysisHistory(analysis=result)
    db.add(record)
    db.commit()
    db.refresh(record)

    # 5) Return the analysis JSON
    return result



@router.get(
    "/history",
    response_model=List[schemas.SwingAnalysisHistoryItem]
)
def get_swing_history(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Return the most recent `limit` analyses, newest first.
    """
    rows = (
        db.query(models.SwingAnalysisHistory)
          .order_by(models.SwingAnalysisHistory.created_at.desc())
          .limit(limit)
          .all()
    )
    return rows