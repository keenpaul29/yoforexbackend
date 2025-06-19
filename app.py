# app.py
from dotenv import load_dotenv
import os
import uuid
import base64
import mimetypes
import requests
import json
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

# Load environment variables from .env file
load_dotenv()

# Create a directory for file uploads
UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize FastAPI app
app = FastAPI(
    title="Gemini Trading Chart Analyzer",
    description="Upload a trading chart image and get an AI-powered analysis in a structured JSON format.",
    version="1.1.0"
)

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

def get_image_mime_type(file_path):
    """Determines the MIME type of an image file."""
    mime_type, _ = mimetypes.guess_type(file_path)
    # Default to PNG if the MIME type cannot be guessed
    return mime_type or "image/png"

def analyze_image_with_gemini(image_path: str):
    """
    Analyzes a local image file using Gemini, expecting a JSON response
    that matches the frontend schema exactly.
    """
    # 1. Get API Key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Set GEMINI_API_KEY in your environment or a .env file")

    # 2. Prepare the image data
    mime_type = get_image_mime_type(image_path)
    with open(image_path, "rb") as img_file:
        image_data = base64.b64encode(img_file.read()).decode('utf-8')

    # 3. Construct the API request payload
    prompt_text = (
        "You are an expert trading chart analyst. Respond ONLY with a single JSON object, no prose.\n\n"
        "The JSON must match this schema exactly:\n"
        "{\n"
        '  "signal": "BUY or SELL",\n'
        '  "confidence": "integer percentage, e.g. 87",\n'
        '  "entry": "price string, e.g. \'1.0892\'",\n'
        '  "stop_loss": "price string, e.g. \'1.085\'",\n'
        '  "take_profit": "price string, e.g. \'1.095\'",\n'
        '  "risk_reward_ratio": "string, e.g. \'1:1.38\'",\n'
        '  "technical_analysis": {\n'
        '    "RSI": "numeric value or string, e.g. \'45.2\'",\n'
        '    "MACD": "Bullish or Bearish",\n'
        '    "Moving_Average": "status, e.g. \'Above 50 EMA\'"\n'
        '  },\n'
        '  "recommendation": "short recommendation text"\n'
        "}\n\n"
        "Analyze the image and fill in each field."
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt_text},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": image_data
                        }
                    }
                ]
            }
        ],
        # Instruct model to return JSON
        "generationConfig": {
            "response_mime_type": "application/json"
        }
    }

    headers = {
        "Content-Type": "application/json"
    }

    # 4. Make the API call to Gemini
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"→ Gemini API request failed: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Error communicating with the AI API: {e}"
        )

    # 5. Process the response
    try:
        response_json = resp.json()
        raw_json_text = response_json['candidates'][0]['content']['parts'][0]['text']
        parsed_data = json.loads(raw_json_text)
        return parsed_data
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print("→ Error parsing Gemini response:", e)
        print("→ Full Gemini response:", resp.text)
        raise HTTPException(
            status_code=500,
            detail="Failed to parse the structured JSON from the AI API response."
        )


@app.post("/analyze-chart/")
async def analyze_chart_endpoint(file: UploadFile = File(...)):
    """
    Endpoint to upload a chart image and receive a structured AI analysis.
    """
    # Generate a unique filename to prevent conflicts
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1] or ".png"
    path = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")

    # Save the uploaded file to the local directory
    try:
        with open(path, "wb") as f:
            f.write(await file.read())
    except IOError as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {e}")

    # Perform the AI analysis
    try:
        analysis_result = analyze_image_with_gemini(path)
    finally:
        # Clean up the saved file after analysis is complete
        if os.path.exists(path):
            os.remove(path)

    return analysis_result


def _run_test():
    """Runs a self-test of the /analyze-chart/ endpoint."""
    client = TestClient(app)
    img_path = "test_chart.png"
    if not os.path.exists(img_path):
        print(f"SKIPPING SELF-TEST: Place a sample image named '{img_path}' and rerun.")
        return

    print("→ Running self-test with 'test_chart.png'...")
    try:
        with open(img_path, "rb") as img:
            files = {"file": ("test_chart.png", img, "image/png")}
            res = client.post("/analyze-chart/", files=files)

        print(f"→ Self-test status: {res.status_code}")
        if res.status_code == 200:
            print("→ Self-test response JSON:")
            print(json.dumps(res.json(), indent=2))
        else:
            print("→ Self-test error response:")
            print(res.text)

    except Exception as e:
        print(f"→ Self-test failed with an exception: {e}")


if __name__ == "__main__":
    if os.getenv("GEMINI_API_KEY"):
        _run_test()
    else:
        print("SKIPPING SELF-TEST: GEMINI_API_KEY not set.")

    import uvicorn
    print("\n→ Starting Uvicorn server. Go to http://127.0.0.1:8000/docs for the API interface.")
    uvicorn.run(app, host="0.0.0.0", port=8000)
