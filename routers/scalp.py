import os
import uuid
from fastapi import APIRouter, UploadFile, File, Query, HTTPException
from utils.image_check import is_trading_chart
from utils.gemini_helper import analyze_image_with_gemini

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter()

@router.post("/chart/")
async def analyze_chart(
    file: UploadFile = File(...),
    timeframe: str = Query(..., enum=["M1", "M5", "M15", "M30", "H1"], description="Swing timeframe")
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

    return result
