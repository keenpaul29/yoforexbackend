import os
import json
import base64
import mimetypes
import requests
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_KEY:
    raise RuntimeError("GEMINI_API_KEY not set in .env")

def get_image_mime_type(path: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    return mime or "image/png"

def analyze_image_with_gemini(path: str, timeframe: str) -> dict:
    mime = get_image_mime_type(path)
    with open(path, "rb") as f:
        data_b64 = base64.b64encode(f.read()).decode()

    prompt = (
        f"You are an expert trading chart analyst using ICT concepts. "
        f"Based on timeframe ({timeframe}), respond ONLY with this JSON schema:\n"
        '{ "signal":"BUY/SELL", "confidence":"int%", "entry":"price", '
        '"stop_loss":"price","take_profit":"price","risk_reward_ratio":"R:R",'
        '"timeframe":"'+timeframe+'","technical_analysis":{'
        '"RSI":"num","MACD":"Bullish/Bearish","Moving_Average":"status",'
        '"ICT_Order_Block":"Detected/Not","ICT_Fair_Value_Gap":"Detected/Not",'
        '"ICT_Breaker_Block":"Detected/Not","ICT_Trendline":"Up/Down/Neutral"'
        '}, "recommendation":"text",'
        '"dynamic_stop_loss":"calculated","dynamic_take_profit":"calculated"}'
    )

    payload = {
        "contents":[
            {"parts":[{"text": prompt},
                      {"inline_data": {"mime_type": mime, "data": data_b64}}]}
        ],
        "generationConfig":{"response_mime_type":"application/json"}
    }

    url = (
      "https://generativelanguage.googleapis.com/v1beta/models/"
      "gemini-2.5-flash:generateContent?key=" + GEMINI_KEY
    )
    resp = requests.post(url, json=payload, timeout=60)
    if resp.status_code != 200:
        raise HTTPException(502, detail=f"AI API error: {resp.text}")

    raw = resp.json()
    candidate = raw["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(candidate)
