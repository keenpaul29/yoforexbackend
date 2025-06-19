from dotenv import load_dotenv
load_dotenv()

import os
import uuid
import base64
import mimetypes
import json
import requests
import numpy as np
import cv2

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

# --- Configuration ---
UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_KEY:
    raise RuntimeError("Set GEMINI_API_KEY in your environment or .env file")

# --- App Setup ---
app = FastAPI(
    title="Gemini Trading Chart Analyzer",
    description="Upload a trading chart image and get an AI-powered analysis in JSON.",
    version="1.1.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# --- Helpers ---
def get_image_mime_type(path: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    return mime or "image/png"

def is_trading_chart(path: str) -> bool:
    """
    Rudimentary chart detector: counts straight lines. 
    True if >20 lines found, else False.
    """
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return False

    # edge detection + Hough
    edges = cv2.Canny(img, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi/180,
        threshold=100,
        minLineLength=100,
        maxLineGap=10
    )
    return lines is not None and len(lines) > 20

def analyze_image_with_gemini(path: str, timeframe: str) -> dict:
    """
    Calls Gemini API for JSON analysis.
    """
    mime = get_image_mime_type(path)
    with open(path, "rb") as f:
        data_b64 = base64.b64encode(f.read()).decode()

    # Updated prompt with the selected timeframe
    prompt = (
    f"You are an expert trading chart analyst using ICT concepts and techniques for swing trading. "
    f"Based on the selected timeframe ({timeframe}), respond ONLY with this JSON schema:\n"
    '{ "signal":"BUY or SELL", '
    '"confidence":"int %", '
    '"entry":"price", '
    '"stop_loss":"price", '
    '"take_profit":"price", '
    '"risk_reward_ratio":"R:R", '
    '"timeframe":"{timeframe}", '
    '"technical_analysis":{ '
    '"RSI":"num", '
    '"MACD":"Bullish/Bearish", '
    '"Moving_Average":"status", '
    '"ICT_Order_Block":"Detected/Not Detected", '
    '"ICT_Fair_Value_Gap":"Detected/Not Detected", '
    '"ICT_Breaker_Block":"Detected/Not Detected", '
    '"ICT_Trendline":"Upward/Downward/Neutral" '
    '}, '
    '"recommendation":"text", '
    '"dynamic_stop_loss":"calculated based on selected timeframe", '
    '"dynamic_take_profit":"calculated based on selected timeframe" '
    "}\n"
    "Analyze the image, identify the relevant ICT concepts (order blocks, fair value gaps, etc.), "
    "and fill each field dynamically, including calculated TP and SL levels based on the selected timeframe (H4, D1, W1)."
)

    payload = {
        "contents": [
            { "parts":[ {"text": prompt},
                         {"inline_data":{"mime_type":mime,"data":data_b64}} ] }
        ],
        "generationConfig": { "response_mime_type": "application/json" }
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}"
    resp = requests.post(url, json=payload, timeout=60)
    if resp.status_code != 200:
        print("→ Gemini error:", resp.status_code, resp.text)
        raise HTTPException(502, detail="AI API error: " + resp.text)

    # extract the JSON from the response
    raw = resp.json()
    candidate = raw["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(candidate)

# --- Endpoint ---
@app.post("/analyze-chart/")
async def analyze_chart_endpoint(
    file: UploadFile = File(...),
    timeframe: str = Query(..., enum=["H1", "D1", "W1"], description="Select the timeframe for swing trading analysis.")
):
    # 1) save file
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1] or ".png"
    path = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")
    with open(path, "wb") as out:
        out.write(await file.read())

    # 2) reject if not a chart
    if not is_trading_chart(path):
        os.remove(path)
        raise HTTPException(400, detail="Please upload a trading chart image")

    # 3) analyze
    try:
        result = analyze_image_with_gemini(path, timeframe)
    finally:
        os.remove(path)

    return result

# --- Self-test ---
def _run_test():
    client = TestClient(app)
    sample = "test_chart.png"
    if not os.path.exists(sample):
        print(f"SKIPPING TEST: drop '{sample}' here.")
        return

    with open(sample, "rb") as img:
        r = client.post("/analyze-chart/", files={"file":("test.png", img, "image/png")}, params={"timeframe": "D1"})
    print("TEST status:", r.status_code)
    print("TEST body:", r.text)

if __name__ == "__main__":
    # only run test if key is set
    if GEMINI_KEY:
        try:
            print("→ Running self-test…")
            _run_test()
        except Exception as e:
            print("→ Self-test skipped:", e)
    else:
        print("→ No GEMINI_API_KEY; skipping self-test.")

    import uvicorn
    print("→ Starting server at http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
